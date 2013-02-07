import json

from bitdeli import model
from bitdeli import insight

from bitdeli.protocol import params, output, entries
from bitdeli.bencode import BenJson, bencode
from bitdeli import profiles

DDB_PART_SIZE = 8 * 1024 * 1024

PARAMS = params()

def do_insight():
    def load_model():
        from discodb import DiscoDB
        return DiscoDB.loads(''.join(part for did, part in entries()))
    import model as _
    import insight as _
    m = model._load(load_model(), None) # FIXME add segments
    # FIXME handle missing _run
    widgets = insight._run(m, PARAMS['event'])
    output(map(lambda x: BenJson(json.dumps(x)), widgets))

def do_model():
    def split(data):
        i = 0
        while i < len(data):
            yield data[i:i + DDB_PART_SIZE]
            i += DDB_PART_SIZE
    import model as _
    # FIXME handle missing _ddb
    ddb = model._ddb(profiles())
    output(split(ddb.dumps()))

if __name__ == '__main__':
    mtype = PARAMS['type']
    if mtype == 'insight':
        do_insight()
    elif mtype == 'model':
        do_model()
    else:
        raise Exception('Unknown type: %s' % mtype)
