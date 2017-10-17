import logging

from salt.serializers import yaml
from salt.exceptions import CommandExecutionError


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
    if tiller_kwargs.get('tiller_host'):
        tiller_args = ('--host', tiller_kwargs['tiller_host'])
    elif tiller_kwargs.get('tiller_namespace'):
        tiller_args = ('--tiller-namespace', tiller_kwargs['tiller_namespace'])
    else:
        tiller_args = ()
    env = {'HELM_HOME': HELM_HOME}
    if tiller_kwargs.get('kube_config'):
        env['KUBECONFIG'] = tiller_kwargs['kube_config']
    if tiller_kwargs.get('gce_service_token'):
        env['GOOGLE_APPLICATION_CREDENTIALS'] = \
            tiller_kwargs['gce_service_token']
    return {
        'cmd': ('helm',) + tiller_args + args,
        'env': env,
    }

def _parse_repo(repo_string = None):
  split_string = repo_string.split('\t')
  return {
    "name": split_string[0].strip(),
    "url": split_string[1].strip()
  }

def list_repos():
  '''
  Get the result of running `helm repo list` on the target minion, formatted
  as a list of dicts with two keys:

    * name: the name with which the repository is registered
    * url: the url registered for the repository
  '''
  cmd = _helm_cmd('repo', 'list')
  result = __salt__['cmd.run_stdout'](**cmd)
  if result is None:
    return result

  result = result.split("\n")
  result.pop(0)
  return { 
    repo['name']: repo['url'] for repo in [_parse_repo(line) for line in result]
  }

def add_repo(name, url):
  '''
  Register the repository located at the supplied url with the supplied name. 
  Note that re-using an existing name will overwrite the repository url for
  that registered repository to point to the supplied url.

  name
      The name with which to register the repository with the Helm client.

  url
      The url for the chart repository.
  '''
  cmd = _helm_cmd('repo', 'add', name, url)
  ret = __salt__['cmd.run_all'](**cmd)
  if ret['retcode'] != 0:
    raise CommandExecutionError(ret['stderr'])
  return ret['stdout']

def remove_repo(name):
  '''
  Remove the repository from the Helm client registered with the supplied
  name.

  name
      The name (as registered with the Helm client) for the repository to remove
  '''
  cmd = _helm_cmd('repo', 'remove', name)
  ret = __salt__['cmd.run_all'](**cmd)
  if ret['retcode'] != 0:
    raise CommandExecutionError(ret['stderr'])
  return ret['stdout']

def manage_repos(present={}, absent=[], exclusive=False):
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
  existing_repos = list_repos()
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
        'stdout': add_repo(name, url)
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
      result['removed'].append({ 'name': name, 'stdout': remove_repo(name) })
    except CommandExecutionError as e:
      result['failed'].append({ 
        "type": "removal", "name": name, "error": '%s' % e 
      })

  return result

def update_repos():
  '''
  Ensures the local helm repository cache for each repository is up to date. 
  Proxies the `helm repo update` command.
  '''
  cmd = _helm_cmd('repo', 'update')
  return __salt__['cmd.run_stdout'](**cmd)

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
