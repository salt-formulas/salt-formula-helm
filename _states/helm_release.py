import logging

def present(name, chart_name, version=None, values=None, logLevel=None):
    exists =  __salt__['helm.release_exists'](name)
    if not exists:
        result = __salt__['helm.release_create'](
            name, chart_name, version, values)
        if result:
            return {
                'name': name,
                'changes': {name: 'CREATED'},
                'result': True,
                'comment': 'Release "{}" was created'.format(name),
            }
        else:
            return {
                'name': name,
                'changes': {},
                'result': False,
                'comment': 'Failed to create release "{}"'.format(name),
            }
    return {
        'name': name,
        'changes': {},
        'result': True,
        'comment': 'Release "{}" already exists'.format(name),
    }
