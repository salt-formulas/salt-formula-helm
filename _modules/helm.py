import logging

from salt.serializers import yaml

HELM_HOME = '/srv/helm/home'
LOG = logging.getLogger(__name__)

def _helm_cmd(*args):
    return {
        'cmd': ('helm',) + args,
        'env': {'HELM_HOME': HELM_HOME},
    }


def release_exists(name):
    cmd = _helm_cmd('list', '--short', '--all', name)
    return __salt__['cmd.run_stdout'](**cmd) == name


def release_create(name, chart_name, version=None, values=None):
    args = []
    if version is not None:
        args += ['--version', version]
    if values is not None:
        args += ['--values', '/dev/stdin']
    cmd = _helm_cmd('install', '--name', name, chart_name, *args)
    if values is not None:
        cmd['stdin'] = yaml.serialize(values, default_flow_style=False)
    LOG.debug('Creating release with args: %s', cmd)
    return __salt__['cmd.retcode'](**cmd) == 0
