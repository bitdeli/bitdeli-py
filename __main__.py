import json

from bitdeli import model
from bitdeli import insight

from bitdeli.protocol import params, output, entries
from bitdeli.bencode import BenJson, bencode
from bitdeli import profiles

DDB_PART_SIZE = 8 * 1024 * 1024

PARAMS = params()

def load_model():
    from discodb import DiscoDB
    return DiscoDB.loads(''.join(part for did, part in entries()))

def split(data):
    i = 0
    while i < len(data):
        yield data[i:i + DDB_PART_SIZE]
        i += DDB_PART_SIZE

def do_insight(db):
    import model as _
    import insight as _
    m = model._load(db, None) # FIXME add segments
    # FIXME handle missing _run
    widgets = insight._run(m, PARAMS['event'])
    return map(lambda x: BenJson(json.dumps(x)), widgets)

def do_model():
    import model as _
    # FIXME handle missing _ddb
    return model._ddb(profiles())

def do_segment(db):
    import model as _
    import insight as _
    m = model._load(db, None) # FIXME add segments
    # FIXME _segment not defined
    return insight._segment(m, PARAMS['params'])

if __name__ == '__main__':
    mtype = PARAMS['type']
    if mtype == 'insight':
        output(do_insight(load_model()))
    elif mtype == 'draft':
        output(do_insight(do_model()))
    elif mtype == 'model':
        output(split(do_model().dumps()))
    elif mtype == 'segment':
        output(split(do_segment(load_model()).dumps()))
    else:
        raise Exception('Unknown type: %s' % mtype)
