_ddb = None
_segment_key = None
_segment_model = None

def model(func):
    from discodb import DiscoDB
    global _ddb
    _ddb = lambda profiles: DiscoDB(func(profiles))
    return func

def model_discodb(func):
    global _ddb
    _ddb = func
    return func

def segment_model(func):
    global _segment_model
    _segment_model = func
    return func

def uid(func):
    from segment_discodb import SegmentDiscoDB
    global _segment_model
    _segment_model = lambda model, segments: SegmentDiscoDB(model,
                                                            segments,
                                                            func)
    return func

def _load(model, segments):
    if segments:
        if not _segment_model:
            uid(lambda x: x)
        return _segment_model(model, segments)
    else:
        return model


