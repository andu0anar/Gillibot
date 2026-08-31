from .base import Plugin


class Admin(Plugin):
    name = 'admin'

    def __init__(self, bot):
        super().__init__(bot)
        # client_id -> admin level (set by guid/name lookup later)
        self.admins = {}
        self.names = {}

    def on_name(self, event):
        self.names[event['client_id']] = event['name']

    def on_disconnect(self, event):
        self.names.pop(event['client_id'], None)

    def on_say(self, event):
        text = event['text'].strip()
        cid = event['client_id']
        name = event.get('name', self.names.get(cid, f'Player {cid}'))

        if text == '!players':
            status = self.rcon.get_status()
            if status:
                self.rcon.say(f'^3Server status: ^7{status[:80]}')

        elif text.startswith('!kick '):
            target_name = text[6:].strip()
            target_id = self._find_player(target_name)
            if target_id is not None:
                self.rcon.kick(target_id, f'Kicked by {name}')
                self.rcon.say(f'^7{target_name} ^1kicked ^7by ^3{name}')
            else:
                self.rcon.tell(cid, f'^1Player not found: {target_name}')

        elif text.startswith('!slap '):
            target_name = text[6:].strip()
            target_id = self._find_player(target_name)
            if target_id is not None:
                self.rcon.slap(target_id)

        elif text.startswith('!mute '):
            target_name = text[6:].strip()
            target_id = self._find_player(target_name)
            if target_id is not None:
                self.rcon.mute(target_id)
                self.rcon.say(f'^3{target_name} ^7has been ^1muted^7.')

        elif text == '!help':
            self.rcon.tell(cid, '^3Commands: ^7!knife  !knch <name>  !accept  !decline  !knifeoff  !knifescores  !players  !kick <name>  !slap <name>  !mute <name>')

    def _find_player(self, name_fragment):
        name_fragment = name_fragment.lower()
        for cid, name in self.names.items():
            if name_fragment in name.lower():
                return cid
        return None
