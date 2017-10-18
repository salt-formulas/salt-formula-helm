import logging
import re

from salt.serializers import yaml
from salt.exceptions import CommandExecutionError

LOG = logging.getLogger(__name__)

def ok_or_output(cmd, prefix=None):
    ret = __salt__['cmd.run_all'](**cmd)
    if ret['retcode'] == 0:
        return None
    msg = "Stdout:\n{0[stdout]}\nStderr:\n{0[stderr]}".format(ret)
    if prefix:
        msg = prefix + ':\n' + msg
    return msg


def _helm_cmd(*args, **kwargs):
    if kwargs.get('tiller_host'):
        addtl_args = ('--host', kwargs['tiller_host'])
    elif kwargs.get('tiller_namespace'):
        addtl_args = ('--tiller-namespace', kwargs['tiller_namespace'])
    else:
        addtl_args = ()

    if kwargs.get('helm_home'):
      addtl_args = addtl_args + ('--home', kwargs['helm_home'])

    env = {}
    if kwargs.get('kube_config'):
        env['KUBECONFIG'] = kwargs['kube_config']
    if kwargs.get('gce_service_token'):
        env['GOOGLE_APPLICATION_CREDENTIALS'] = \
            kwargs['gce_service_token']
    return {
        'cmd': ('helm',) + addtl_args + args,
        'env': env,
    }

def _parse_release(output):
  result = {}
  chart_match = re.search(r'CHART\: ([^0-9]+)-([^\s]+)', output)
  if chart_match:
    result['chart'] = chart_match.group(1)
    result['version'] = chart_match.group(2)
  
  user_values_match = re.search(r"(?<=USER-SUPPLIED VALUES\:\n)(\n*.+)+?(?=\n*COMPUTED VALUES\:)", output, re.MULTILINE)
  if user_values_match:
    result['values'] = yaml.deserialize(user_values_match.group(0))

  computed_values_match = re.search(r"(?<=COMPUTED VALUES\:\n)(\n*.+)+?(?=\n*HOOKS\:)", output, re.MULTILINE)
  if computed_values_match:
    result['computed_values'] = yaml.deserialize(computed_values_match.group(0))

  manifest_match = re.search(r"(?<=MANIFEST\:\n)(\n*(?!Release \".+\" has been upgraded).*)+", output, re.MULTILINE)
  if manifest_match:
    result['manifest'] = manifest_match.group(0)

  namespace_match = re.search(r"(?<=NAMESPACE\: )(.*)", output)
  if namespace_match:
    result['namespace'] = namespace_match.group(0)

  return result

def _parse_repo(repo_string = None):
  split_string = repo_string.split('\t')
  return {
    "name": split_string[0].strip(),
    "url": split_string[1].strip()
  }
  

def _get_release_namespace(name, tiller_namespace="kube-system", **kwargs):
  cmd = _helm_cmd("list", name, **kwargs)
  result = __salt__['cmd.run_stdout'](**cmd)
  if not result or len(result.split("\n")) < 2:
    return None

  return result.split("\n")[1].split("\t")[5]

def list_repos(**kwargs):
  '''
  Get the result of running `helm repo list` on the target minion, formatted
  as a list of dicts with two keys:

    * name: the name with which the repository is registered
    * url: the url registered for the repository
  '''
  cmd = _helm_cmd('repo', 'list', **kwargs)
  result = __salt__['cmd.run_stdout'](**cmd)
  if result is None:
    return result

  result = result.split("\n")
  result.pop(0)
  return { 
    repo['name']: repo['url'] for repo in [_parse_repo(line) for line in result]
  }

def add_repo(name, url, **kwargs):
  '''
  Register the repository located at the supplied url with the supplied name. 
  Note that re-using an existing name will overwrite the repository url for
  that registered repository to point to the supplied url.

  name
      The name with which to register the repository with the Helm client.

  url
      The url for the chart repository.
  '''
  cmd = _helm_cmd('repo', 'add', name, url, **kwargs)
  ret = __salt__['cmd.run_all'](**cmd)
  if ret['retcode'] != 0:
    raise CommandExecutionError(ret['stderr'])
  return ret['stdout']

def remove_repo(name, **kwargs):
  '''
  Remove the repository from the Helm client registered with the supplied
  name.

  name
      The name (as registered with the Helm client) for the repository to remove
  '''
  cmd = _helm_cmd('repo', 'remove', name, **kwargs)
  ret = __salt__['cmd.run_all'](**cmd)
  if ret['retcode'] != 0:
    raise CommandExecutionError(ret['stderr'])
  return ret['stdout']

def manage_repos(present={}, absent=[], exclusive=False, **kwargs):
  '''
  Manage the repositories registered with the Helm client's local cache. 

  *ensuring repositories are present*
  Repositories that should be present in the helm client can be supplied via 
  the `present` dict parameter; each key in the dict is a release name, and the
  value is the repository url that should be registered.

  *ensuring repositories are absent*
  Repository names supplied via the `absent` parameter must be a string. If the
  `exclusive` flag is set to True, the `absent` parameter will be ignored, even
  if it has been supplied.

  This function returns a dict with the following keys:

    * already_present: a listing of supplied repository definitions to add that 
      are already registered with the Helm client

    * added: a list of repositories that are newly registered with the Helm 
      client. Each item in the list is a dict with the following keys:
        * name: the repo name
        * url: the repo url
        * stdout: the output from the `helm repo add` command call for the repo
    
    * already_absent: any repository name supplied via the `absent` parameter 
      that was already not registered with the Helm client
    
    * removed: the result of attempting to remove any repositories

    * failed: a list of repositores that were unable to be added. Each item in
      the list is a dict with the following keys:
        * type: the text "removal" or "addition", as appropriate
        * name: the repo name
        * url: the repo url (if appropriate)
        * error: the output from add or remove command attempted for the 
          repository

  present
      The dict of repositories that should be registered with the Helm client. 
      Each dict key is the name with which the repository url (the corresponding
      value) should be registered with the Helm client.

  absent
      The list of repositories to ensure are not registered with the Helm client.
      Each entry in the list must be the (string) name of the repository.

  exclusive
      A flag indicating whether only the supplied repos should be available in 
      the target minion's Helm client. If configured to true, the `absent` 
      parameter will be ignored and only the repositories configured via the 
      `present` parameter will be registered with the Helm client. Defaults to 
      False.
  '''
  existing_repos = list_repos(**kwargs)
  result = {
    "already_present": [],
    "added": [],
    "already_absent": [],
    "removed": [],
    "failed": []
  }

  for name, url in present.iteritems():
    if not name or not url:
      raise CommandExecutionError(('Supplied repo to add must have a name (%s) '
                                   'and url (%s)' % (name, url)))
    
    if name in existing_repos and existing_repos[name] == url:
      result['already_present'].append({ "name": name, "url": url })
      continue

    try:
      result['added'].append({ 
        'name': name, 
        'url': url, 
        'stdout': add_repo(name, url, **kwargs)
      })
      existing_repos = {
        n: u for (n, u) in existing_repos.iteritems() if name != n
      }
    except CommandExecutionError as e:
      result['failed'].append({ 
        "type": "addition", 
        "name": name, 
        'url': url, 
        'error': '%s' % e
      })  
  
  #
  # Handle removal of repositories configured to be absent (or not configured
  # to be present if the `exclusive` flag is set)
  #
  existing_names = [name for (name, url) in existing_repos.iteritems()]
  if exclusive:
    present['stable'] = "exclude"
    absent = [name for name in existing_names if not name in present]
  
  for name in absent:
    if not name or not isinstance(name, str):
      raise CommandExecutionError(('Supplied repo name to be absent must be a '
                                   'string: %s' % name))
    
    if name not in existing_names:
      result['already_absent'].append(name)
      continue

    try:
      result['removed'].append({ 
        'name': name, 
        'stdout': remove_repo(name, **kwargs) 
      })
    except CommandExecutionError as e:
      result['failed'].append({ 
        "type": "removal", "name": name, "error": '%s' % e 
      })

  return result

def update_repos(**kwargs):
  '''
  Ensures the local helm repository cache for each repository is up to date. 
  Proxies the `helm repo update` command.
  '''
  cmd = _helm_cmd('repo', 'update', **kwargs)
  return __salt__['cmd.run_stdout'](**cmd)

def get_release(name, tiller_namespace="kube-system", **kwargs):
  '''
  Get the parsed release metadata from calling `helm get {{ release }}` for the 
  supplied release name, or None if no release is found. The following keys may 
  or may not be in the returned dict:

    * chart
    * version
    * values
    * computed_values
    * manifest
    * namespace
  '''
  kwargs['tiller_namespace'] = tiller_namespace
  cmd = _helm_cmd('get', name, **kwargs)
  result = __salt__['cmd.run_stdout'](**cmd)
  if not result:
    return None

  release = _parse_release(result)

  #
  # `helm get {{ release }}` doesn't currently (2.6.2) return the namespace, so 
  # separately retrieve it if it's not available
  #
  if not 'namespace' in release:
    release['namespace'] = _get_release_namespace(name, **kwargs)
  return release

def release_exists(name, tiller_namespace="kube-system", **kwargs):
  '''
  Determine whether a release exists in the cluster with the supplied name
  '''
  kwargs['tiller_namespace'] = tiller_namespace
  return get_release(name, **kwargs) is not None

def release_create(name, chart_name, namespace='default',
                   version=None, values_file=None,
                   tiller_namespace='kube-system', **kwargs):
    '''
    Install a release. There must not be a release with the supplied name 
    already installed to the Kubernetes cluster.

    Note that if a release already exists with the specified name, you'll need
    to use the release_upgrade function instead; unless the release is in a
    different namespace, in which case you'll need to delete and purge the 
    existing release (using release_delete) and *then* use this function to
    install a new release to the desired namespace.
    '''
    args = []
    if version is not None:
        args += ['--version', version]
    if values_file is not None:
        args += ['--values', values_file]
    cmd = _helm_cmd('install', '--namespace', namespace, '--name', name, chart_name, 
                    *args, **kwargs)
    LOG.debug('Creating release with args: %s', cmd)
    return ok_or_output(cmd, 'Failed to create release "{}"'.format(name))


def release_delete(name, tiller_namespace='kube-system', **kwargs):
    '''
    Delete and purge any release found with the supplied name.
    '''
    kwargs['tiller_namespace'] = tiller_namespace
    cmd = _helm_cmd('delete', '--purge', name, **kwargs)
    return ok_or_output(cmd, 'Failed to delete release "{}"'.format(name))


def release_upgrade(name, chart_name, namespace='default',
                    version=None, values_file=None,
                    tiller_namespace='kube-system', **kwargs):
    '''
    Upgrade an existing release. There must be a release with the supplied name
    already installed to the Kubernetes cluster.

    If attempting to change the namespace for the release, this function will
    fail; you will need to first delete and purge the release and then use the
    release_create function to create a new release in the desired namespace.
    '''
    kwargs['tiller_namespace'] = tiller_namespace
    args = []
    if version is not None:
      args += ['--version', version]
    if values_file is not None:
      args += ['--values', values_file]
    cmd = _helm_cmd('upgrade', '--namespace', namespace, name, chart_name, **kwargs)
    LOG.debug('Upgrading release with args: %s', cmd)
    return ok_or_output(cmd, 'Failed to upgrade release "{}"'.format(name))
