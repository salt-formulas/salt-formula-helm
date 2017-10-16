{%- from slspath + "/map.jinja" import config, constants with context %}

include:
  - .client_installed

{%- if "repos" in config %}
{%- for repo_name, repo_url in config.repos.items() %}
ensure_{{ repo_name }}_repo:
  cmd.run:
    - name: {{ constants.helm.cmd }} repo add {{ repo_name }} {{ repo_url }}
    - env:
      - HELM_HOME: {{ constants.helm.home }}
    - unless: {{ constants.helm.cmd }} repo list | grep '^{{ repo_name }} {{ repo_url|replace(".", "\.") }}'
    - require:
      - sls: {{ slspath }}.client_installed
{%- endfor %}
{%- endif %}{# "repos" in client #}
