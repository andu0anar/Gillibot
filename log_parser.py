import re

# Urban Terror kill mod IDs
MOD = {
    0:  'Unknown',
    1:  'Water',
    2:  'Lava',
    3:  'Telefrag',
    4:  'Falling',
    5:  'Knife',
    6:  'KnifeThrown',
    7:  'Beretta',
    8:  'Deagle',
    9:  'Spas',
    10: 'UMP45',
    11: 'MP5K',
    12: 'LR300',
    13: 'G36',
    14: 'PSG1',
    15: 'HK69',
    16: 'NADE',
    17: 'NADESplash',
    18: 'Rocket',
    19: 'RocketSplash',
    20: 'SR8',
    21: 'AK103',
    22: 'Negev',
    23: 'HE',
    24: 'Glock',
    25: 'Colt',
    26: 'Kevlar',
    27: 'Kick',
    28: 'Extinguisher',
}

KNIFE_MODS = {5, 6}  # Knife and KnifeThrown

_RE_KILL = re.compile(
    r'^\s*\d+:\d+\s+Kill:\s+(\d+)\s+(\d+)\s+(\d+):\s+(.+)\s+killed\s+(.+)\s+by\s+(\S+)'
)
_RE_CLIENT_INFO = re.compile(
    r'^\s*\d+:\d+\s+ClientUserinfoChanged:\s+(\d+)\s+n\\([^\\]+)\\'
)
_RE_CLIENT_CONNECT = re.compile(r'^\s*\d+:\d+\s+ClientConnect:\s+(\d+)')
_RE_CLIENT_DISCONNECT = re.compile(r'^\s*\d+:\d+\s+ClientDisconnect:\s+(\d+)')
_RE_INIT_GAME = re.compile(r'^\s*\d+:\d+\s+InitGame:')
_RE_SHUTDOWN = re.compile(r'^\s*\d+:\d+\s+ShutdownGame')
_RE_CHAT = re.compile(r'^\s*\d+:\d+\s+say:\s+(\d+)\s+(.+):\s+(.*)')
_RE_TEAMCHAT = re.compile(r'^\s*\d+:\d+\s+sayteam:\s+(\d+)\s+(.+):\s+(.*)')


def parse_line(line):
    m = _RE_KILL.match(line)
    if m:
        mod_id = int(m.group(3))
        return {
            'event': 'kill',
            'killer_id': int(m.group(1)),
            'victim_id': int(m.group(2)),
            'mod_id': mod_id,
            'mod_name': MOD.get(mod_id, 'Unknown'),
            'killer_name': m.group(4).strip(),
            'victim_name': m.group(5).strip(),
            'is_knife': mod_id in KNIFE_MODS,
        }

    m = _RE_CLIENT_INFO.match(line)
    if m:
        return {'event': 'name', 'client_id': int(m.group(1)), 'name': m.group(2)}

    m = _RE_CLIENT_CONNECT.match(line)
    if m:
        return {'event': 'connect', 'client_id': int(m.group(1))}

    m = _RE_CLIENT_DISCONNECT.match(line)
    if m:
        return {'event': 'disconnect', 'client_id': int(m.group(1))}

    m = _RE_CHAT.match(line)
    if m:
        return {'event': 'say', 'client_id': int(m.group(1)), 'name': m.group(2), 'text': m.group(3)}

    m = _RE_TEAMCHAT.match(line)
    if m:
        return {'event': 'sayteam', 'client_id': int(m.group(1)), 'name': m.group(2), 'text': m.group(3)}

    if _RE_INIT_GAME.match(line):
        return {'event': 'init_game'}

    if _RE_SHUTDOWN.match(line):
        return {'event': 'shutdown'}

    return None
