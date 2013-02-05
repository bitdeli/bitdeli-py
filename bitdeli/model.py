
_new = None

def new(func):
    global _new
    _new = func
    # FIXME func could be a generator of k-v pairs:
    # create discodb in a wrapper func
    return func

def _load(segments):
    if segments:
        # FIXME return segmented model
        pass
    else:
        return 'this is a model'
