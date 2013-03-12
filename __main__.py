import json

from bitdeli import model
from bitdeli import insight

from bitdeli.protocol import params, output, entries, all_inputs, output_sys
from bitdeli.bencode import BenJson, bencode
from bitdeli import profiles

DDB_PART_SIZE = 8 * 1024 * 1024

PARAMS = params()

def load_inputs():
    from discodb import DiscoDB
    def load_ddb():
        return DiscoDB.loads(''.join(part for did, part in entries()))
    inputs = all_inputs()
    inputs.next()
    return load_ddb(), [load_ddb() for input in inputs]

def split(data):
    i = 0
    while i < len(data):
        yield data[i:i + DDB_PART_SIZE]
        i += DDB_PART_SIZE

def do_insight(db, segments):
    import model as _
    import insight as _
    m = model._load(db, segments, PARAMS['segment-labels'])
    # FIXME handle missing _run
    widgets = insight._run(m, PARAMS['params'])
    return map(lambda x: BenJson(json.dumps(x)), widgets)

def do_segment(db, segments):
    import model as _
    import insight as _
    params = PARAMS['params']
    m = model._load(db, segments, PARAMS['segment-labels'])
    db = insight._segment(m, params)
    label = 'untitled'
    if insight._segment_label:
        label = insight._segment_label(db, m, params)
    output_sys('label', label.encode('utf-8'))
    output_sys('size', len(db))
    return db

def do_model():
    import model as _
    # FIXME handle missing _ddb
    return model._ddb(profiles())

if __name__ == '__main__':
    mtype = PARAMS['type']
    if mtype == 'insight':
        output(do_insight(*load_inputs()))
    elif mtype == 'segment':
        output(split(do_segment(*load_inputs()).dumps()))
    elif mtype == 'draft':
        output(do_insight(do_model(), []))
    elif mtype == 'model':
        output(split(do_model().dumps()))
    else:
        raise Exception('Unknown type: %s' % mtype)
