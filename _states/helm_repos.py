import re

from salt.exceptions import CommandExecutionError

def managed(name, present={}, absent=[], exclusive=False, helm_home=None):
  '''
  Ensure the supplied repositories are available to the helm client. If the
  `exclusive` flag is set to a truthy value, any extra repositories in the 
  helm client will be removed.

  name
      The name of the state

  present
      A dict of repository names to urls to ensure are registered with the 
      Helm client
  
  absent
      A list of repository names to ensure are unregistered from the Helm client
  
  exclusive
      A boolean flag indicating whether the state should ensure only the 
      supplied repositories are availabe to the target minion.

  helm_home
      An optional path to the Helm home directory 
  '''
  ret = {'name': name,
         'changes': {},
         'result': True,
         'comment': ''}
  
  try:
    result = __salt__['helm.manage_repos'](
      present=present, 
      absent=absent, 
      exclusive=exclusive,
      helm_home=helm_home
    )

    if result['failed']:
      ret['comment'] = 'Failed to add or remove some repositories'
      ret['changes'] = result
      ret['result'] = False
      return ret

    if result['added'] or result['removed']:
      ret['comment'] = 'Repositories were added or removed'
      ret['changes'] = result
      return ret

    ret['comment'] = ("Repositories were in the desired state: "
                     "%s" % [name for (name, url) in present.iteritems()])
    return ret
  except CommandExecutionError as e:
    ret['result'] = False
    ret['comment'] = "Failed to add some repositories: %s" % e
    return ret

def updated(name, helm_home=None):
  '''
  Ensure the local Helm repository cache is up to date with each of the 
  helm client's configured remote chart repositories. Because the `helm repo 
  update` command doesn't indicate whether any changes were made to the local 
  cache, this will only indicate change if the Helm client failed to retrieve
  an update from one or more of the repositories, regardless of whether an 
  update was made to the local Helm chart repository cache.

  name
      The name of the state

  helm_home
      An optional path to the Helm home directory 
  '''
  ret = {'name': name,
         'changes': {},
         'result': True,
         'comment': 'Successfully synced repositories: ' }
  
  output = None
  try:
    output = __salt__['helm.update_repos'](helm_home=helm_home)
  except CommandExecutionError as e:
    ret['result'] = False
    ret['comment'] = "Failed to update repos: %s" % e
    return ret

  success_repos = re.findall(
    r'Successfully got an update from the \"([^\"]+)\"', output)
  failed_repos = re.findall(
    r'Unable to get an update from the \"([^\"]+)\"', output)
  
  if failed_repos and len(failed_repos) > 0:
    ret['result'] = False
    ret['changes']['succeeded'] = success_repos
    ret['changes']['failed'] = failed_repos
    ret['comment'] = 'Failed to sync against some repositories'
  else:
    ret['comment'] += "%s" % success_repos
  
  return ret