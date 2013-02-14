from itertools import izip_longest

_rules = {}
_insight = None
_segment = None
_segment_label = None

def insight(func):
    global _insight
    _insight = func
    return func

def segment(func):
    from discodb import DiscoDB
    global _segment
    _segment = lambda model, params: DiscoDB(izip_longest(func(model, params),
                                                          [],
                                                          fillvalue=''))
    return func

def segment_label(func):
    global _segment_label
    _segment_label = func
    return func

def _run(model, params):
    widgets = _insight(model, params)
    #FIXME widget encoding
    return map(lambda w: w.kwargs, widgets)

if __name__ == '__main__':
    @view
    def view(model):
        return [1, 2, 3, model]

    @on('click')
    def onclick(model, event):
        return ['a', model, 'b', event]

    print _run({})
