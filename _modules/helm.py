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


def _helm_cmd(*args):
    return {
        'cmd': ('helm',) + args,
        'env': {'HELM_HOME': HELM_HOME},
    }


def release_exists(name, namespace):
    cmd = _helm_cmd('list', '--short', '--all', '--namespace', namespace, name)
    return __salt__['cmd.run_stdout'](**cmd) == name


def release_create(name, namespace, chart_name, version=None, values=None):
    args = []
    if version is not None:
        args += ['--version', version]
    if values is not None:
        args += ['--values', '/dev/stdin']
    cmd = _helm_cmd('install', '--namespace', namespace,
                    '--name', name, chart_name, *args)
    if values is not None:
        cmd['stdin'] = yaml.serialize(values, default_flow_style=False)
    LOG.debug('Creating release with args: %s', cmd)
    return ok_or_output(cmd, 'Failed to create release "{}"'.format(name))


def release_delete(name):
    cmd = _helm_cmd('delete', '--purge', name)
    return ok_or_output(cmd, 'Failed to delete release "{}"'.format(name))


def release_upgrade(name, namespace, chart_name, version=None, values=None):
    args = []
    if version is not None:
        args += ['--version', version]
    if values is not None:
        args += ['--values', '/dev/stdin']
    cmd = _helm_cmd('upgrade', '--namespace', namespace,
                    name, chart_name, *args)
    if values is not None:
        cmd['stdin'] = yaml.serialize(values, default_flow_style=False)
    LOG.debug('Upgrading release with args: %s', cmd)
    return ok_or_output(cmd, 'Failed to upgrade release "{}"'.format(name))


def get_values(name):
    cmd = _helm_cmd('get', 'values', '--all', name)
    return yaml.deserialize(__salt__['cmd.run_stdout'](**cmd))
