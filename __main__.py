import json

from bitdeli import model
from bitdeli import insight

from bitdeli.protocol import params, output
from bitdeli.bencode import BenJson
from bitdeli import profiles

PARAMS = params()

def do_insight():
    import model as _
    import insight as _
    # FIXME load model data (input)
    m = model._load(None) # FIXME add segments
    widgets = insight._run(m, PARAMS['event'])
    output(map(lambda x: BenJson(json.dumps(x)), widgets))

def do_model():
    import model as _
    model._new(profiles())
    # FIXME save model here?

if __name__ == '__main__':
    mtype = PARAMS['type']
    if mtype == 'insight':
        do_insight()
    elif mtype == 'model':
        do_model()
    else:
        raise Exception('Unknown type: %s' % mtype)
