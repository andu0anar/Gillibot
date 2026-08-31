import sqlite3
import os
from datetime import datetime
from .base import Plugin

KNIFE_MODS = {5, 6}
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'gillibot_stats.db')


class Stats(Plugin):
    name = 'stats'

    def __init__(self, bot):
        super().__init__(bot)
        self.db = sqlite3.connect(os.path.abspath(DB_PATH), check_same_thread=False)
        self._init_db()
        self.names = {}  # client_id -> name

    def _init_db(self):
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS knife_stats (
                name        TEXT PRIMARY KEY,
                knife_kills INTEGER DEFAULT 0,
                knife_deaths INTEGER DEFAULT 0,
                duel_wins   INTEGER DEFAULT 0,
                duel_losses INTEGER DEFAULT 0,
                last_seen   TEXT
            )
        ''')
        self.db.commit()

    def _upsert(self, name):
        self.db.execute('''
            INSERT INTO knife_stats (name, last_seen)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET last_seen = excluded.last_seen
        ''', (name, datetime.utcnow().isoformat()))
        self.db.commit()

    def record_knife_kill(self, killer_name, victim_name):
        self._upsert(killer_name)
        self._upsert(victim_name)
        self.db.execute(
            'UPDATE knife_stats SET knife_kills = knife_kills + 1 WHERE name = ?',
            (killer_name,)
        )
        self.db.execute(
            'UPDATE knife_stats SET knife_deaths = knife_deaths + 1 WHERE name = ?',
            (victim_name,)
        )
        self.db.commit()

    def record_duel_win(self, winner_name, loser_name):
        self._upsert(winner_name)
        self._upsert(loser_name)
        self.db.execute(
            'UPDATE knife_stats SET duel_wins = duel_wins + 1 WHERE name = ?',
            (winner_name,)
        )
        self.db.execute(
            'UPDATE knife_stats SET duel_losses = duel_losses + 1 WHERE name = ?',
            (loser_name,)
        )
        self.db.commit()

    def get_stats(self, name):
        cur = self.db.execute(
            'SELECT knife_kills, knife_deaths, duel_wins, duel_losses FROM knife_stats WHERE name = ?',
            (name,)
        )
        return cur.fetchone()

    def get_top(self, limit=5):
        cur = self.db.execute(
            '''SELECT name, knife_kills, knife_deaths, duel_wins
               FROM knife_stats
               ORDER BY knife_kills DESC
               LIMIT ?''',
            (limit,)
        )
        return cur.fetchall()

    def _find_name(self, fragment):
        fragment = fragment.lower()
        for name in self.names.values():
            if fragment in name.lower():
                return name
        # fall back to DB search
        cur = self.db.execute(
            "SELECT name FROM knife_stats WHERE LOWER(name) LIKE ? LIMIT 1",
            (f'%{fragment}%',)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def _show_stats(self, cid, target_name):
        row = self.get_stats(target_name)
        if not row:
            self.rcon.tell(cid, f'^3No stats found for ^7{target_name}')
            return
        kills, deaths, dw, dl = row
        kd = f'{kills/deaths:.2f}' if deaths else 'inf'
        duel_record = f'^2{dw}^7W - ^1{dl}^7L'
        self.rcon.say(f'^3=== Knife Stats: ^7{target_name} ^3===')
        self.rcon.say(f'^7Knife Kills: ^2{kills}  ^7Deaths: ^1{deaths}  ^7K/D: ^3{kd}')
        self.rcon.say(f'^7Duel Record: {duel_record}')

    # ------------------------------------------------------------------
    # Plugin event handlers
    # ------------------------------------------------------------------

    def on_name(self, event):
        self.names[event['client_id']] = event['name']

    def on_disconnect(self, event):
        self.names.pop(event['client_id'], None)

    def on_kill(self, event):
        if event['killer_id'] == event['victim_id'] or event['killer_id'] == 1022:
            return
        if event['mod_id'] in KNIFE_MODS:
            self.record_knife_kill(event['killer_name'], event['victim_name'])

    def on_say(self, event):
        text = event['text'].strip()
        cid = event['client_id']
        lower = text.lower()

        if lower == '!knstats':
            name = self.names.get(cid)
            if name:
                self._show_stats(cid, name)

        elif lower.startswith('!knstats '):
            fragment = text[9:].strip()
            target = self._find_name(fragment)
            if target:
                self._show_stats(cid, target)
            else:
                self.rcon.tell(cid, f'^1Player not found: ^7{fragment}')

        elif lower == '!kntop':
            rows = self.get_top(5)
            if not rows:
                self.rcon.say('^3No knife stats recorded yet.')
                return
            self.rcon.say('^3=== Top Knife Killers ===')
            medals = ['^1#1', '^2#2', '^3#3', '^7#4', '^7#5']
            for i, (name, kills, deaths, dw) in enumerate(rows):
                kd = f'{kills/deaths:.2f}' if deaths else 'inf'
                medal = medals[i] if i < len(medals) else f'^7#{i+1}'
                self.rcon.say(f'{medal} ^7{name}  ^2{kills}^7K  ^3{kd}^7KD  ^5{dw}^7DW')
