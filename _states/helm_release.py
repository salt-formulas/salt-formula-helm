import difflib
import os 
import logging

from salt.exceptions import CommandExecutionError
from salt.serializers import yaml

LOG = logging.getLogger(__name__)

def _get_values_from_file(values_file=None):
    if values_file:
      try:
        with open(values_file) as values_stream:
          values = yaml.deserialize(values_stream)
        return values
      except e:
        raise CommandExecutionError("encountered error reading from values "
                                    "file (%s): %s" % (values_file, e))
    return None

def _get_yaml_diff(new_yaml=None, old_yaml=None):
  if not new_yaml and not old_yaml:
    return None
  
  old_str = yaml.serialize(old_yaml, default_flow_style=False)
  new_str = yaml.serialize(new_yaml, default_flow_style=False)
  return difflib.unified_diff(old_str.split('\n'), new_str.split('\n'))

def _failure(name, message, changes={}):
    return {
        'name': name,
        'changes': changes,
        'result': False,
        'comment': message,
    }

def present(name, chart_name, namespace, version=None, values_file=None,
            tiller_namespace='kube-system', **kwargs):
    '''
    Ensure that a release with the supplied name is in the desired state in the 
    Tiller installation. This state will handle change detection to determine 
    whether an installation or update needs to be made. 

    In the event the namespace to which a release is installed changes, the
    state will first delete and purge the release and the re-install it into
    the new namespace, since Helm does not support updating a release into a 
    new namespace.

    name
        The name of the release to ensure is present

    chart_name
        The name of the chart to install, including the repository name as 
        applicable (such as `stable/mysql`)

    namespace
        The namespace to which the release should be (re-)installed

    version
        The version of the chart to install. Defaults to the latest version

    values_file
        The path to the a values file containing all the chart values that 
        should be applied to the release. Note that this should not be passed
        if there are not chart value overrides required.

    '''
    kwargs['tiller_namespace'] = tiller_namespace
    old_release = __salt__['helm.get_release'](name, **kwargs)
    if not old_release:
        err = __salt__['helm.release_create'](
            name, chart_name, namespace, version, values_file, **kwargs
        )
        if err:
            return _failure(name, err)
        return {
            'name': name,
            'changes': {
                'name': name,
                'chart_name': chart_name,
                'namespace': namespace,
                'version': version,
                'values': _get_values_from_file(values_file)
            },
            'result': True,
            'comment': 'Release "{}" was created'.format(name),
        }

    changes = {}
    warnings = []
    if old_release.get('chart') != chart_name.split("/")[1]:
      changes['chart'] = { 'old': old_release['chart'], 'new': chart_name }

    if old_release.get('version') != version:
      changes['version'] = { 'old': old_release['version'], 'new': version }

    if old_release.get('namespace') != namespace:
        changes['namespace'] = { 'old': old_release['namespace'], 'new': namespace }

    if (not values_file and old_release.get("values") or
        not old_release.get("values") and values_file):
      changes['values'] = { 'old': old_release['values'], 'new': values_file }

    values = _get_values_from_file(values_file)
    diff = _get_yaml_diff(values, old_release.get('values'))
    
    if diff:
      diff_string = '\n'.join(diff)
      if diff_string:
        changes['values'] = diff_string

    if not changes:
      return {
        'name': name,
        'result': True,
        'changes': {},
        'comment': 'Release "{}" is already in the desired state'.format(name)
      }

    module_fn = 'helm.release_upgrade'
    if changes.get("namespace"):
      LOG.debug("purging old release (%s) due to namespace change" % name)
      err = __salt__['helm.release_delete'](name, **kwargs)
      if err:
        return _failure(name, err, changes)
      module_fn = 'helm.release_create'
      warnings.append('Release (%s) was replaced due to namespace change' % name)

    err = __salt__[module_fn](
        name, chart_name, namespace, version, values_file, **kwargs
    )
    if err:
      return _failure(name, err, changes)

    ret = {
        'name': name,
        'changes': changes,
        'result': True,
        'comment': 'Release "{}" was updated'.format(name),
    }

    if warnings:
      ret['warnings'] = warnings

    return ret


def absent(name, tiller_namespace='kube-system', **kwargs):
    '''
    Ensure that any release with the supplied release name is absent from the
    tiller installation.

    name
        The name of the release to ensure is absent
    '''
    kwargs['tiller_namespace'] = tiller_namespace
    exists = __salt__['helm.release_exists'](name, **kwargs)
    if not exists:
        return {
            'name': name,
            'changes': {},
            'result': True,
            'comment': 'Release "{}" doesn\'t exist'.format(name),
        }
    err = __salt__['helm.release_delete'](name, **kwargs)
    if err:
        return _failure(name, err)
    return {
        'name': name,
        'changes': {name: 'DELETED'},
        'result': True,
        'comment': 'Release "{}" was deleted'.format(name),
    }
