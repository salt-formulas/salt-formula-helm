{%- from slspath + "/map.jinja" import config, constants with context %}

include:
  - .client_installed
  - .kubectl_configured

{%- if config.tiller.install %}
install_tiller:
  cmd.run:
    - name: {{ constants.helm.cmd }} init --upgrade
    - env:
      - HELM_HOME: {{ constants.helm.home }}
      - KUBECONFIG: {{ constants.kubectl.config }}
      {{ constants.tiller.gce_env_var }}
    - unless: "{{ constants.helm.cmd }} version --server --short | grep -E 'Server: v{{ config.version }}(\\+|$)'"
    - require:
      - sls: {{ slspath }}.client_installed
      - sls: {{ slspath }}.kubectl_configured

wait_for_tiller:
  cmd.run:
    - name: while ! {{ constants.helm.cmd }} list; do sleep 3; done
    - timeout: 30
    - env:
      - HELM_HOME: {{ constants.helm.home }}
      - KUBECONFIG: {{ constants.kubectl.config }}
      {{ constants.tiller.gce_env_var }}
    - require:
      - sls: {{ slspath }}.client_installed
      - sls: {{ slspath }}.kubectl_configured
    - onchanges:
      - cmd: install_tiller
{%- endif %}