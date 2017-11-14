{%- from slspath + "/map.jinja" import config, constants with context %}

include:
  - .kubectl_installed

{{ config.kubectl.config_file }}:
  file.managed:
    - source: salt://helm/files/kubeconfig.yaml.j2
    - mode: 400
    - user: root
    - group: root
    - makedirs: true
    - template: jinja
    {%- if config.kubectl.install %}
    - require:
        - sls: {{ slspath }}.kubectl_installed
    {%- endif %}

{%- if config.kubectl.config.gce_service_token %}
{{ constants.kubectl.gce_service_token_path }}:
  file.managed:
    - source: salt://helm/files/gce_token.json.j2
    - mode: 400
    - user: root
    - group: root
    - makedirs: true
    - template: jinja
    - context:
        content: {{ config.kubectl.config.gce_service_token }}
    {%- if config.kubectl.install %}
    - require:
        - sls: {{ slspath }}.kubectl_installed
    {%- endif %}
{%- endif %}{# gce_service_token #}