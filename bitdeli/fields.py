from collections import namedtuple
from bencode import BenJson
from datetime import datetime
from json import dumps

F_UID = 0
F_IP = 1
F_OBJECT = 2
F_ID = 3
F_TSTAMP = 4
F_GROUPKEY = 5

Event = namedtuple('Event',
                   ('uid', 'ip', 'object', 'id', 'timestamp', 'groupkey'))

def make_event(uid, obj, groupkey):
    tstamp = datetime.utcnow().isoformat('T') + 'Z'
    return (str(uid), '0.0.0.0', obj, '', tstamp, groupkey)
