import time
import os
import configparser

from rcon import RconClient
from log_parser import parse_line
from plugins.knife_challenge import KnifeChallenge
from plugins.admin import Admin


class Gillibot:
    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        srv = self.config['server']
        self.rcon = RconClient(
            host=srv['host'],
            port=int(srv['port']),
            password=srv['rcon_password'],
        )
        self.log_file = srv['log_file']
        self.players = {}  # client_id -> name

        self.plugins = [
            KnifeChallenge(self),
            Admin(self),
        ]

    def _dispatch(self, event):
        if event['event'] == 'name':
            self.players[event['client_id']] = event['name']
        elif event['event'] == 'disconnect':
            self.players.pop(event['client_id'], None)
        elif event['event'] == 'init_game':
            self.players.clear()

        for plugin in self.plugins:
            try:
                plugin.on_event(event)
            except Exception as e:
                print(f'[plugin error] {plugin.name}: {e}')

    def _tick(self):
        for plugin in self.plugins:
            try:
                plugin.on_tick()
            except Exception as e:
                print(f'[plugin tick error] {plugin.name}: {e}')

    def run(self):
        print(f'[Gillibot] Starting. Tailing {self.log_file}')
        self.rcon.say('^3Gillibot ^7online. Type ^2!help ^7for commands.')
        last_tick = time.time()

        with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
            f.seek(0, os.SEEK_END)  # start at end of file (live tail)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    now = time.time()
                    if now - last_tick >= 5:
                        last_tick = now
                        self._tick()
                    continue
                event = parse_line(line)
                if event:
                    print(f'[event] {event}')
                    self._dispatch(event)


if __name__ == '__main__':
    import sys
    cfg = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
    bot = Gillibot(cfg)
    bot.run()
