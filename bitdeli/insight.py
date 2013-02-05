
_rules = {}
_view = None

def view(func):
    global _view
    _view = func
    return func

def on(rule):
    def decorator(func):
        _rules[rule] = func
        return func
    return decorator

def _route(event):
    action = event['action']
    widget = event['widget']
    id = event['id']
    matches = ('%s #%s' % (action, id),
               '#%s' % id,
               '%s .%s' % (action, widget),
               '.%s' % widget,
               action)
    for match in matches:
        func = _rules.get(match)
        if func:
            return func
    raise Exception("No handler found for '%s %s'" %
                    (event['action'], event['id']))

def _eval(func, model, event):
    res = func(model, event)
    if type(res) == list and res and type(res[0]) != tuple:
        return res
    else:
        widgets = _view(model)
        for rule, fields in res:
            attr = 'type' if rule[0] == '.' else 'id'
            matches = filter(lambda w: w.kwargs[attr] == rule[1:], widgets)
            if matches:
                for match in matches:
                    match.kwargs.update(fields)
            else:
                name = func.func_name
                raise Exception("Output rule '%s' by the function '%s' "
                                "(triggered by '%s %s') doesn't match "
                                "any widgets" %
                                (rule, name, event['action'], event['id']))
        return widgets

def _run(model, event):
    if event:
        widgets = _eval(_route(event), model, event)
    else:
        widgets = _view(model)
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
