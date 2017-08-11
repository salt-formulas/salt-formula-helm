import difflib
import logging

from salt.serializers import yaml


def failure(name, message):
    return {
        'name': name,
        'changes': {},
        'result': False,
        'comment': message,
    }


def present(name, chart_name, namespace, version=None, values=None):
    exists =  __salt__['helm.release_exists'](name, namespace)
    if not exists:
        result = __salt__['helm.release_create'](
            name, namespace, chart_name, version, values)
        if not result:
            return failure(name, 'Failed to create release "{}"'.format(name))
        return {
            'name': name,
            'changes': {name: 'CREATED'},
            'result': True,
            'comment': 'Release "{}" was created'.format(name),
        }

    old_values = __salt__['helm.get_values'](name)
    result = __salt__['helm.release_upgrade'](
        name, namespace, chart_name, version, values)
    if not result:
        return failure(name, 'Failed to create release "{}"'.format(name))

    new_values = __salt__['helm.get_values'](name)
    if new_values == old_values:
        return {
            'name': name,
            'changes': {},
            'result': True,
            'comment': 'Release "{}" already exists'.format(name),
        }

    old_str = yaml.serialize(old_values, default_flow_style=False)
    new_str = yaml.serialize(new_values, default_flow_style=False)
    diff = difflib.unified_diff(
        old_str.split('\n'), new_str.split('\n'), lineterm='')
    return {
        'name': name,
        'changes': {'values': '\n'.join(diff)},
        'result': True,
        'comment': 'Release "{}" was updated'.format(name),
    }


def absent(name, namespace):
    exists =  __salt__['helm.release_exists'](name, namespace)
    if not exists:
        return {
            'name': name,
            'changes': {},
            'result': True,
            'comment': 'Release "{}" doesn\'t exist'.format(name),
        }
    result = __salt__['helm.release_delete'](name)
    if not result:
        return failure(name, 'Failed to delete release "{}"'.format(name))
    return {
        'name': name,
        'changes': {name: 'DELETED'},
        'result': True,
        'comment': 'Release "{}" was deleted'.format(name),
    }
