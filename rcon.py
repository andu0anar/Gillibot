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
        """Send and wait for response — use for status/cvar queries only."""
        payload = HEADER + f'rcon {self.password} {command}'.encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        try:
            sock.sendto(payload, (self.host, self.port))
            response = sock.recv(4096)
            return response[4:].decode(errors='replace').strip()
        except socket.timeout:
            return None
        finally:
            sock.close()

    def fire(self, command):
        """Send without waiting for a response — for say/bigtext/kick etc."""
        payload = HEADER + f'rcon {self.password} {command}'.encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(payload, (self.host, self.port))
        finally:
            sock.close()

    def say(self, message):
        self.fire(f'say {message}')
        time.sleep(0.05)  # brief gap so lines render separately in chat

    def bigtext(self, message):
        self.fire(f'bigtext "{message}"')

    def centerprint(self, message):
        self.fire(f'cp "{message}"')

    def tell(self, client_id, message):
        self.fire(f'tell {client_id} {message}')

    def kick(self, client_id, reason=''):
        self.fire(f'clientkick {client_id} "{reason}"')

    def slap(self, client_id):
        self.fire(f'slap {client_id}')

    def nuke(self, client_id):
        self.fire(f'nuke {client_id}')

    def mute(self, client_id):
        self.fire(f'mute {client_id}')

    def set_team(self, client_id, team):
        # team: red, blue, spectator, free
        self.send(f'forceteam {client_id} {team}')

    def get_status(self):
        return self.send('status')

    def get_cvar(self, cvar):
        return self.send(cvar)

    def set_cvar(self, cvar, value):
        self.send(f'{cvar} "{value}"')
