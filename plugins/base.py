class Plugin:
    name = 'base'

    def __init__(self, bot):
        self.bot = bot
        self.rcon = bot.rcon
        self.config = bot.config

    def on_event(self, event):
        handler = getattr(self, f'on_{event["event"]}', None)
        if handler:
            handler(event)

    def on_init_game(self, event): pass
    def on_shutdown(self, event): pass
    def on_connect(self, event): pass
    def on_disconnect(self, event): pass
    def on_name(self, event): pass
    def on_kill(self, event): pass
    def on_say(self, event): pass
    def on_sayteam(self, event): pass
