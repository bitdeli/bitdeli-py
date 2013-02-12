_ddb = None

def model(func):
    from discodb import DiscoDB
    global _ddb
    _ddb = lambda profiles: DiscoDB(func(profiles))
    return func

def model_discodb(func):
    global _ddb
    _ddb = func
    return func

def _load(model, segments):
    if segments:
        # FIXME return segmented model
        pass
    else:
        return model
