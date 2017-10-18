{%- from slspath + "/map.jinja" import config, constants with context %}

include:
  - .client_installed
  - .tiller_installed
  - .kubectl_configured
  - .repos_managed

{%- if "releases" in config %}
{%- for release_id, release in config.releases.items() %}
{%- set release_name = release.get('name', release_id) %}
{%- set namespace = release.get('namespace', 'default') %}
{%- set values_file = config.values_dir + "/" + release_name + ".yaml" %}

{%- if release.get('enabled', True) %}

{%- if release.get("values") %}
{{ values_file }}:
  file.managed:
    - makedirs: True
    - contents: |
        {{ release['values'] | yaml(false) | indent(8) }}
{%- else %}
{{ values_file }}:
  file.absent
{%- endif %}

ensure_{{ release_id }}_release:
  helm_release.present:
    - name: {{ release_name }}
    - chart_name: {{ release['chart'] }}
    - namespace: {{ namespace }}
    - kube_config: {{ config.kubectl.config_file }}
    - helm_home: {{ config.helm_home }}
    {{ constants.helm.tiller_arg }}
    {{ constants.helm.gce_state_arg }}
    {%- if release.get('version') %}
    - version: {{ release['version'] }}
    {%- endif %}
    {%- if release.get("values") %}
    - values_file: {{ values_file }}
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

{%- if release.get("values") %}
{{ values_file }}:
  file.absent
{%- endif %}


absent_{{ release_id }}_release:
  helm_release.absent:
    - name: {{ release_name }}
    - namespace: {{ namespace }}
    - kube_config: {{ config.kubectl.config_file }}
    - helm_home: {{ config.helm_home }}
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
