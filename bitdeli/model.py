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
    def default_model(model, segment, labels):
        from segment_discodb import SegmentDiscoDB
        return SegmentDiscoDB(model, segments, func, labels)
    global _segment_model
    _segment_model = default_model
    return func

def _load(model, segments, labels):
    if segments:
        if not _segment_model:
            uid(lambda x: x)
        return _segment_model(model, segments, labels)
    else:
        return model


