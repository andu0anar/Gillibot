import socket
import time

HEADER = b'\xff\xff\xff\xff'


class RconClient:
    def __init__(self, host, port, password, timeout=2.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout

    def send(self, command):
        payload = HEADER + f'rcon {self.password} {command}'.encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        try:
            sock.sendto(payload, (self.host, self.port))
            time.sleep(0.05)
            response = sock.recv(4096)
            return response[4:].decode(errors='replace').strip()
        except socket.timeout:
            return None
        finally:
            sock.close()

    def say(self, message):
        self.send(f'say {message}')

    def tell(self, client_id, message):
        self.send(f'tell {client_id} {message}')

    def kick(self, client_id, reason=''):
        self.send(f'clientkick {client_id} "{reason}"')

    def slap(self, client_id):
        self.send(f'slap {client_id}')

    def nuke(self, client_id):
        self.send(f'nuke {client_id}')

    def mute(self, client_id):
        self.send(f'mute {client_id}')

    def set_team(self, client_id, team):
        # team: red, blue, spectator, free
        self.send(f'forceteam {client_id} {team}')

    def get_status(self):
        return self.send('status')

    def get_cvar(self, cvar):
        return self.send(cvar)

    def set_cvar(self, cvar, value):
        self.send(f'{cvar} "{value}"')
