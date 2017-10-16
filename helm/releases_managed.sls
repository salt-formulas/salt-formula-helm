{%- from slspath + "/map.jinja" import config, constants with context %}

include:
  - .client_installed
  - .tiller_installed
  - .kubectl_configured
  - .repos_synchronized

{%- if "releases" in config %}
{%- for release_id, release in config.releases.items() %}
{%- set release_name = release.get('name', release_id) %}
{%- set namespace = release.get('namespace', 'default') %}

{%- if release.get('enabled', True) %}
ensure_{{ release_id }}_release:
  helm_release.present:
    - name: {{ release_name }}
    - chart_name: {{ release['chart'] }}
    - namespace: {{ namespace }}
    - kube_config: {{ constants.kubectl.config }}
    {{ constants.helm.tiller_arg }}
    {{ constants.helm.gce_state_arg }}
    {%- if release.get('version') %}
    - version: {{ release['version'] }}
    {%- endif %}
    {%- if release.get('values') %}
    - values:
        {{ release['values']|yaml(False)|indent(8) }}
    {%- endif %}
    - require:
      {%- if config.tiller.install %}
      - sls: {{ slspath }}.tiller_installed
      {%- endif %}
      - sls: {{ slspath }}.client_installed
      - sls: {{ slspath }}.kubectl_configured
      # 
      # note: intentionally don't fail if one or more repos fail to synchronize,
      # since there should be a local repo cache anyways.
      # 

{%- else %}{# not release.enabled #}
absent_{{ release_id }}_release:
  helm_release.absent:
    - name: {{ release_name }}
    - namespace: {{ namespace }}
    - kube_config: {{ constants.kubectl.config }}
    {{ constants.helm.tiller_arg }}
    {{ constants.helm.gce_state_arg }}
    - require:
      {%- if config.tiller.install %}
      - sls: {{ slspath }}.tiller_installed
      {%- endif %}
      - sls: {{ slspath }}.client_installed
      - sls: {{ slspath }}.kubectl_configured
      # 
      # note: intentionally don't fail if one or more repos fail to synchronize,
      # since there should be a local repo cache anyways.
      # 

{%- endif %}{# release.enabled #}
{%- endfor %}{# release_id, release in client.releases #}
{%- endif %}{# "releases" in client #}
