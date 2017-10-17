import difflib

from salt.serializers import yaml


def failure(name, message):
    return {
        'name': name,
        'changes': {},
        'result': False,
        'comment': message,
    }


def present(name, chart_name, namespace, version=None, values_file=None,
            tiller_namespace='kube-system', tiller_host=None,
            kube_config=None, gce_service_token=None, helm_home=None):
    kwargs = {
        'tiller_namespace': tiller_namespace,
        'tiller_host': tiller_host,
        'kube_config': kube_config,
        'gce_service_token': gce_service_token,
        'helm_home': helm_home
    }
    exists = __salt__['helm.release_exists'](name, namespace, **kwargs)
    if not exists:
        err = __salt__['helm.release_create'](
            name, chart_name, namespace, version, values_file, **kwargs)
        if err:
            return failure(name, err)
        return {
            'name': name,
            'changes': {name: 'CREATED'},
            'result': True,
            'comment': 'Release "{}" was created'.format(name),
        }

    old_values = __salt__['helm.get_values'](name, **kwargs)
    err = __salt__['helm.release_upgrade'](
        name, chart_name, namespace, version, values_file, **kwargs)
    if err:
        return failure(name, err)

    new_values = __salt__['helm.get_values'](name, **kwargs)
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


def absent(name, namespace, tiller_namespace='kube-system', tiller_host=None,
           kube_config=None, gce_service_token=None, helm_home=None):
    kwargs = {
        'tiller_namespace': tiller_namespace,
        'tiller_host': tiller_host,
        'kube_config': kube_config,
        'gce_service_token': gce_service_token,
        'helm_home': helm_home
    }
    exists = __salt__['helm.release_exists'](name, namespace, **kwargs)
    if not exists:
        return {
            'name': name,
            'changes': {},
            'result': True,
            'comment': 'Release "{}" doesn\'t exist'.format(name),
        }
    err = __salt__['helm.release_delete'](name, **kwargs)
    if err:
        return failure(name, err)
    return {
        'name': name,
        'changes': {name: 'DELETED'},
        'result': True,
        'comment': 'Release "{}" was deleted'.format(name),
    }
