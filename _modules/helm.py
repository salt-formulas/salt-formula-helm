import logging

from salt.serializers import yaml

HELM_HOME = '/srv/helm/home'
LOG = logging.getLogger(__name__)

def ok_or_output(cmd, prefix=None):
    ret = __salt__['cmd.run_all'](**cmd)
    if ret['retcode'] == 0:
        return None
    msg = "Stdout:\n{0[stdout]}\nStderr:\n{0[stderr]}".format(ret)
    if prefix:
        msg = prefix + ':\n' + msg
    return msg


def _helm_cmd(*args, **tiller_kwargs):
    if tiller_kwargs['tiller_host']:
        tiller_args = ('--host', tiller_kwargs['tiller_host'])
    else:
        tiller_args = ('--tiller-namespace', tiller_kwargs['tiller_namespace'])
    env = {'HELM_HOME': HELM_HOME}
    if tiller_kwargs['kube_config']:
        env['KUBECONFIG'] = tiller_kwargs['kube_config']
    if tiller_kwargs['gce_service_token']:
        env['GOOGLE_APPLICATION_CREDENTIALS'] = \
            tiller_kwargs['gce_service_token']
    return {
        'cmd': ('helm',) + tiller_args + args,
        'env': env,
    }


def release_exists(name, namespace='default',
                   tiller_namespace='kube-system', tiller_host=None,
                   kube_config=None, gce_service_token=None):
    cmd = _helm_cmd('list', '--short', '--all', '--namespace', namespace, name,
                    tiller_namespace=tiller_namespace, tiller_host=tiller_host,
                    kube_config=kube_config,
                    gce_service_token=gce_service_token)
    return __salt__['cmd.run_stdout'](**cmd) == name


def release_create(name, chart_name, namespace='default',
                   version=None, values=None,
                   tiller_namespace='kube-system', tiller_host=None,
                   kube_config=None, gce_service_token=None):
    tiller_args = {
        'tiller_namespace': tiller_namespace,
        'tiller_host': tiller_host,
        'kube_config': kube_config,
        'gce_service_token': gce_service_token,
    }
    args = []
    if version is not None:
        args += ['--version', version]
    if values is not None:
        args += ['--values', '/dev/stdin']
    cmd = _helm_cmd('install', '--namespace', namespace,
                    '--name', name, chart_name, *args, **tiller_args)
    if values is not None:
        cmd['stdin'] = yaml.serialize(values, default_flow_style=False)
    LOG.debug('Creating release with args: %s', cmd)
    return ok_or_output(cmd, 'Failed to create release "{}"'.format(name))


def release_delete(name, tiller_namespace='kube-system', tiller_host=None,
                   kube_config=None, gce_service_token=None):
    cmd = _helm_cmd('delete', '--purge', name,
                    tiller_namespace=tiller_namespace, tiller_host=tiller_host,
                    kube_config=kube_config,
                    gce_service_token=gce_service_token)
    return ok_or_output(cmd, 'Failed to delete release "{}"'.format(name))


def release_upgrade(name, chart_name, namespace='default',
                    version=None, values=None,
                    tiller_namespace='kube-system', tiller_host=None,
                    kube_config=None, gce_service_token=None):
    tiller_args = {
        'tiller_namespace': tiller_namespace,
        'tiller_host': tiller_host,
        'kube_config': kube_config,
        'gce_service_token': gce_service_token,
    }
    args = []
    if version is not None:
        args += ['--version', version]
    if values is not None:
        args += ['--values', '/dev/stdin']
    cmd = _helm_cmd('upgrade', '--namespace', namespace,
                    name, chart_name, *args, **tiller_args)
    if values is not None:
        cmd['stdin'] = yaml.serialize(values, default_flow_style=False)
    LOG.debug('Upgrading release with args: %s', cmd)
    return ok_or_output(cmd, 'Failed to upgrade release "{}"'.format(name))


def get_values(name, tiller_namespace='kube-system', tiller_host=None,
               kube_config=None, gce_service_token=None):
    cmd = _helm_cmd('get', 'values', '--all', name,
                    tiller_namespace=tiller_namespace, tiller_host=tiller_host,
                    kube_config=kube_config,
                    gce_service_token=gce_service_token)
    return yaml.deserialize(__salt__['cmd.run_stdout'](**cmd))
