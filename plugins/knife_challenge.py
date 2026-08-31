from .base import Plugin

KNIFE_MODS = {5, 6}


class KnifeChallenge(Plugin):
    name = 'knife_challenge'

    def __init__(self, bot):
        super().__init__(bot)
        cfg = self.config['knife_challenge']
        self.win_kills = int(cfg.get('win_kills', 10))
        self.active = False
        self.scores = {}      # client_id -> kill count
        self.names = {}       # client_id -> name

    def start(self, caller_id=None):
        if self.active:
            self.rcon.say('^3Knife Challenge is already running!')
            return
        self.active = True
        self.scores = {}
        self.rcon.say('^1>>> ^7KNIFE CHALLENGE ^1<<<')
        self.rcon.say(f'^7First to ^2{self.win_kills} ^7knife kills wins! ^3Blades only!')
        self.rcon.say('^7Use only your ^3knife^7. Guns = shame.')

    def stop(self, caller_id=None):
        if not self.active:
            self.rcon.say('^3No Knife Challenge running.')
            return
        self.active = False
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

    def on_name(self, event):
        self.names[event['client_id']] = event['name']

    def on_disconnect(self, event):
        cid = event['client_id']
        self.scores.pop(cid, None)
        self.names.pop(cid, None)

    def on_init_game(self, event):
        if self.active:
            self.active = False
            self.scores = {}

    def on_kill(self, event):
        if not self.active:
            return

        killer_id = event['killer_id']
        victim_id = event['victim_id']
        mod_id = event['mod_id']

        # World kill or self-kill — ignore
        if killer_id == victim_id or killer_id == 1022:
            return

        self.names[killer_id] = event['killer_name']
        self.names[victim_id] = event['victim_name']

        if mod_id not in KNIFE_MODS:
            # Gun kill during challenge — call them out
            killer_name = event['killer_name']
            self.rcon.say(f'^3{killer_name} ^7used a gun! ^1SHAME!')
            return

        self.scores[killer_id] = self.scores.get(killer_id, 0) + 1
        kills = self.scores[killer_id]
        killer_name = event['killer_name']
        victim_name = event['victim_name']

        self.rcon.say(
            f'^3{killer_name} ^7knifed ^1{victim_name}^7! '
            f'^2{kills}^7/{self.win_kills}'
        )

        if kills % 5 == 0 and kills < self.win_kills:
            self._announce_scores()

        if kills >= self.win_kills:
            self.rcon.say(f'^1>>> ^3{killer_name} ^7WINS THE KNIFE CHALLENGE! ^1<<<')
            self._announce_scores()
            self.active = False
            self.scores = {}

    def on_say(self, event):
        text = event['text'].strip().lower()
        cid = event['client_id']

        if text == '!knife':
            self.start(cid)
        elif text == '!knifeoff':
            self.stop(cid)
        elif text == '!knifescores':
            self._announce_scores()
