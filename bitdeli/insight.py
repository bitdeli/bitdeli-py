
_rules = {}
_insight = None

def insight(func):
    global _insight
    _insight = func
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
