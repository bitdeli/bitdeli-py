from datetime import datetime, timedelta
from types import DictType
from fields import Event

from protocol import output, entries, params
from bencode import encoder_alias, BenJson
from chunkedlist import ChunkedList
from cbencode import Decoder

# shorthands
from widgets import Title, Description, set_theme
from profiles import Profiles

PARAMS = params()
GROUP_FORMAT = '%Y-%m-%d'

class Profile(dict):
    def __init__(self, entry):
        uid, data = entry
        self.uid = uid
        super(Profile, self).__init__(data)

    def set_expire(self, days):
        t = PARAMS['group'][:10]
        expires = datetime.strptime(t, GROUP_FORMAT) + timedelta(days=days)
        self['!!expires'] = datetime.strftime(expires, GROUP_FORMAT)

    def close(self):
        output([(self.uid, self)])

def profile_events():
    decoder = Decoder(json_decode=BenJson, lazylist_obj=ChunkedList)
    def events_iter(it):
        for did, entry in it:
            if entry == 'profile_done':
                return
            else:
                yield Event._make(entry)
    entries_iter = entries(decoder)
    for did, profile_data in entries_iter:
        profile = Profile(profile_data)
        events = events_iter(entries_iter)
        yield profile, events
        for event in events:
            pass
        profile.close()

def profiles():
    for did, entry in entries():
        yield Profile(entry)

encoder_alias(Profile, DictType)
