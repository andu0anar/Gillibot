import time
from .base import Plugin

KNIFE_MODS = {5, 6}
TIME_LIMIT = 180       # 3 minutes for all modes
WARN_AT = {60, 30, 10} # seconds remaining to announce


class KnifeChallenge(Plugin):
    name = 'knife_challenge'

    def __init__(self, bot):
        super().__init__(bot)
        cfg = self.config['knife_challenge']
        self.win_kills = int(cfg.get('win_kills', 10))

        # Server-wide state
        self.active = False
        self.scores = {}
        self.names = {}
        self.start_time = None
        self._warned = set()

        # Duel state
        self.duel_active = False
        self.duel_pending = False
        self.duel_challenger_id = None
        self.duel_target_id = None
        self.duel_win_kills = 1     # default: sudden death
        self.duel_scores = {}
        self.duel_start_time = None
        self._duel_warned = set()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_player_id(self, name_fragment):
        name_fragment = name_fragment.lower()
        for cid, name in self.names.items():
            if name_fragment in name.lower():
                return cid
        return None

    def _remaining(self, start):
        return max(0, TIME_LIMIT - (time.time() - start))

    def _reset_all(self):
        self.active = False
        self.duel_active = False
        self.duel_pending = False
        self.scores = {}
        self.duel_scores = {}
        self.start_time = None
        self.duel_start_time = None
        self._warned.clear()
        self._duel_warned.clear()

    # ------------------------------------------------------------------
    # Server-wide challenge
    # ------------------------------------------------------------------

    def start(self, caller_id=None):
        if self.active or self.duel_active or self.duel_pending:
            self.rcon.say('^3A Knife Challenge is already running!')
            return
        self.active = True
        self.scores = {}
        self.start_time = time.time()
        self._warned.clear()
        self.rcon.bigtext('^1KNIFE CHALLENGE!')
        self.rcon.say('^1===========================================')
        self.rcon.say('^1>>>        ^3K N I F E   C H A L L E N G E        ^1<<<')
        self.rcon.say('^1===========================================')
        self.rcon.say(f'^7First to ^2{self.win_kills} ^7knife kills wins! ^3Blades only!')
        self.rcon.say('^73 minutes on the clock. ^1Guns = shame.')
        self.rcon.say('^1===========================================')

    def stop(self, caller_id=None):
        if not self.active and not self.duel_active and not self.duel_pending:
            self.rcon.say('^3No Knife Challenge running.')
            return
        self._reset_all()
        self.rcon.say('^7Knife Challenge ^1stopped^7.')

    def _announce_scores(self):
        if not self.scores:
            return
        ranked = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)[:3]
        self.rcon.say('^3--- Knife Challenge Standings ---')
        medals = ['^1#1', '^2#2', '^3#3']
        for i, (cid, kills) in enumerate(ranked):
            name = self.names.get(cid, f'Player {cid}')
            medal = medals[i] if i < len(medals) else f'^7#{i+1}'
            self.rcon.say(f'{medal} ^7{name} - ^2{kills} ^7kills')

    def _expire_global(self):
        self.rcon.say('^1>>> ^7Knife Challenge ^1TIME UP! ^7No winner. ^1<<<')
        self._announce_scores()
        self.active = False
        self.scores = {}
        self.start_time = None
        self._warned.clear()

    # ------------------------------------------------------------------
    # Targeted 1v1 duel
    # ------------------------------------------------------------------

    def start_duel(self, challenger_id, target_name, kill_target=1):
        if self.active or self.duel_active or self.duel_pending:
            self.rcon.say('^3A Knife Challenge is already running!')
            return

        target_id = self._find_player_id(target_name)
        if target_id is None:
            self.rcon.tell(challenger_id, f'^1Player not found: ^7{target_name}')
            return
        if target_id == challenger_id:
            self.rcon.tell(challenger_id, '^1You can\'t challenge yourself.')
            return

        self.duel_pending = True
        self.duel_challenger_id = challenger_id
        self.duel_target_id = target_id
        self.duel_win_kills = max(1, kill_target)

        c_name = self.names.get(challenger_id, f'Player {challenger_id}')
        t_name = self.names.get(target_id, f'Player {target_id}')

        if self.duel_win_kills == 1:
            mode_str = '^1SUDDEN DEATH'
        else:
            mode_str = f'^7First to ^2{self.duel_win_kills}'

        self.rcon.bigtext(f'^3{c_name} ^7vs ^3{t_name}')
        self.rcon.say('^1===========================================')
        self.rcon.say(f'^1>>>           ^3K N I F E   D U E L           ^1<<<')
        self.rcon.say('^1===========================================')
        self.rcon.say(f'^3{c_name} ^7has challenged ^3{t_name} ^7to a duel!')
        self.rcon.say(f'^7Mode: {mode_str} ^7| ^33 minute clock')
        self.rcon.say(f'^3{t_name}^7: type ^2!accept ^7or ^1!decline')
        self.rcon.say('^1===========================================')

    def _accept_duel(self, cid):
        if not self.duel_pending or cid != self.duel_target_id:
            return
        self.duel_pending = False
        self.duel_active = True
        self.duel_scores = {self.duel_challenger_id: 0, self.duel_target_id: 0}
        self.duel_start_time = time.time()
        self._duel_warned.clear()

        c_name = self.names.get(self.duel_challenger_id, '?')
        t_name = self.names.get(self.duel_target_id, '?')

        if self.duel_win_kills == 1:
            mode_str = '^1SUDDEN DEATH'
        else:
            mode_str = f'^7First to ^2{self.duel_win_kills}'

        self.rcon.bigtext('^1KNIFE DUEL — FIGHT!')
        self.rcon.say('^1===========================================')
        self.rcon.say(f'^1>>>           ^3D U E L   B E G I N S           ^1<<<')
        self.rcon.say('^1===========================================')
        self.rcon.say(f'^3{c_name} ^7vs ^3{t_name} ^7— {mode_str}')
        self.rcon.say('^7Blades only. ^1Guns = instant forfeit.')
        self.rcon.say('^1===========================================')

    def _decline_duel(self, cid):
        if not self.duel_pending or cid != self.duel_target_id:
            return
        t_name = self.names.get(self.duel_target_id, '?')
        c_name = self.names.get(self.duel_challenger_id, '?')
        self.rcon.say(f'^3{t_name} ^7declined ^3{c_name}\'s ^7duel challenge.')
        self.duel_pending = False
        self.duel_challenger_id = None
        self.duel_target_id = None

    def _record_duel_result(self, winner_name, loser_name):
        stats = self.bot.get_plugin('stats')
        if stats:
            stats.record_duel_win(winner_name, loser_name)

    def _expire_duel(self):
        c_name = self.names.get(self.duel_challenger_id, '?')
        t_name = self.names.get(self.duel_target_id, '?')
        c_kills = self.duel_scores.get(self.duel_challenger_id, 0)
        t_kills = self.duel_scores.get(self.duel_target_id, 0)

        self.rcon.say('^1>>> ^7Knife Duel ^1TIME UP! ^1<<<')
        if c_kills == t_kills:
            self.rcon.say(f'^7{c_name} ^3{c_kills} ^7— ^3{t_kills} ^7{t_name} ^7— ^3DRAW!')
        elif c_kills > t_kills:
            self.rcon.say(f'^3{c_name} ^7wins on points! ^2{c_kills}^7-^1{t_kills}')
            self._record_duel_result(c_name, t_name)
        else:
            self.rcon.say(f'^3{t_name} ^7wins on points! ^2{t_kills}^7-^1{c_kills}')
            self._record_duel_result(t_name, c_name)

        self.duel_active = False
        self.duel_scores = {}
        self.duel_start_time = None
        self._duel_warned.clear()

    def _handle_duel_kill(self, event):
        killer_id = event['killer_id']
        victim_id = event['victim_id']
        mod_id = event['mod_id']

        duel_ids = {self.duel_challenger_id, self.duel_target_id}
        if killer_id not in duel_ids or victim_id not in duel_ids or killer_id == victim_id:
            return

        killer_name = self.names.get(killer_id, event['killer_name'])
        other_id = self.duel_target_id if killer_id == self.duel_challenger_id else self.duel_challenger_id

        if mod_id not in KNIFE_MODS:
            winner_name = self.names.get(other_id, '?')
            self.rcon.say(f'^3{killer_name} ^7used a gun! ^1FORFEIT! ^3{winner_name} ^7wins!')
            self._record_duel_result(winner_name, killer_name)
            self.duel_active = False
            self.duel_scores = {}
            self.duel_start_time = None
            self._duel_warned.clear()
            return

        self.duel_scores[killer_id] = self.duel_scores.get(killer_id, 0) + 1
        kills = self.duel_scores[killer_id]
        other_kills = self.duel_scores.get(other_id, 0)

        remaining = int(self._remaining(self.duel_start_time))
        self.rcon.say(
            f'^3{killer_name} ^7knifed ^1{self.names.get(victim_id, event["victim_name"])}^7! '
            f'^2{kills}^7-^2{other_kills} ^7| ^3{remaining}s left'
        )

        if kills >= self.duel_win_kills:
            loser_name = self.names.get(other_id, '?')
            self._record_duel_result(killer_name, loser_name)
            self.rcon.bigtext(f'^3{killer_name} ^7WINS THE DUEL!')
            self.rcon.say('^1===========================================')
            self.rcon.say(f'^1>>> ^3{killer_name} ^7WINS THE KNIFE DUEL! ^1<<<')
            self.rcon.say('^1===========================================')
            self.duel_active = False
            self.duel_scores = {}
            self.duel_start_time = None
            self._duel_warned.clear()

    # ------------------------------------------------------------------
    # Plugin event handlers
    # ------------------------------------------------------------------

    def on_name(self, event):
        self.names[event['client_id']] = event['name']

    def on_disconnect(self, event):
        cid = event['client_id']
        self.scores.pop(cid, None)
        self.names.pop(cid, None)
        if (self.duel_active or self.duel_pending) and cid in (self.duel_challenger_id, self.duel_target_id):
            self.rcon.say('^7A duellist disconnected — knife duel ^1cancelled^7.')
            self.duel_active = False
            self.duel_pending = False
            self.duel_scores = {}
            self.duel_start_time = None

    def on_init_game(self, event):
        self._reset_all()

    def on_tick(self):
        now = time.time()

        if self.active and self.start_time:
            remaining = self._remaining(self.start_time)
            warn_key = next((w for w in WARN_AT if abs(remaining - w) < 5 and w not in self._warned), None)
            if warn_key:
                self._warned.add(warn_key)
                self.rcon.say(f'^3Knife Challenge: ^2{warn_key} seconds ^3remaining!')
            if remaining == 0:
                self._expire_global()

        if self.duel_active and self.duel_start_time:
            remaining = self._remaining(self.duel_start_time)
            warn_key = next((w for w in WARN_AT if abs(remaining - w) < 5 and w not in self._duel_warned), None)
            if warn_key:
                self._duel_warned.add(warn_key)
                self.rcon.say(f'^3Knife Duel: ^2{warn_key} seconds ^3remaining!')
            if remaining == 0:
                self._expire_duel()

    def on_kill(self, event):
        killer_id = event['killer_id']
        victim_id = event['victim_id']
        mod_id = event['mod_id']

        if killer_id == victim_id or killer_id == 1022:
            return

        self.names[killer_id] = event['killer_name']
        self.names[victim_id] = event['victim_name']

        if self.duel_active:
            self._handle_duel_kill(event)
            return

        if not self.active:
            return

        if mod_id not in KNIFE_MODS:
            self.rcon.say(f'^3{event["killer_name"]} ^7used a gun! ^1SHAME!')
            return

        self.scores[killer_id] = self.scores.get(killer_id, 0) + 1
        kills = self.scores[killer_id]
        remaining = int(self._remaining(self.start_time))

        self.rcon.say(
            f'^3{event["killer_name"]} ^7knifed ^1{event["victim_name"]}^7! '
            f'^2{kills}^7/{self.win_kills} ^7| ^3{remaining}s left'
        )

        if kills % 5 == 0 and kills < self.win_kills:
            self._announce_scores()

        if kills >= self.win_kills:
            self.rcon.bigtext(f'^3{event["killer_name"]} ^7WINS!')
            self.rcon.say('^1===========================================')
            self.rcon.say(f'^1>>> ^3{event["killer_name"]} ^7WINS THE KNIFE CHALLENGE! ^1<<<')
            self.rcon.say('^1===========================================')
            self._announce_scores()
            self.active = False
            self.scores = {}
            self.start_time = None

    def on_say(self, event):
        text = event['text'].strip()
        cid = event['client_id']
        lower = text.lower()

        if lower == '!knife':
            self.start(cid)

        elif lower.startswith('!knch '):
            # parse: !knch <name> [kills]
            parts = text[6:].strip().rsplit(None, 1)
            if len(parts) == 2 and parts[1].isdigit():
                target, kill_target = parts[0], int(parts[1])
            else:
                target, kill_target = (parts[0] if parts else ''), 1
            self.start_duel(cid, target, kill_target)

        elif lower == '!accept':
            self._accept_duel(cid)
        elif lower == '!decline':
            self._decline_duel(cid)
        elif lower == '!knifeoff':
            self.stop(cid)
        elif lower == '!knifescores':
            self._announce_scores()
