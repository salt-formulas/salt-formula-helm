{%- from "helm/map.jinja" import client with context %}
{%- if client.enabled %}

{%- set helm_tmp = "/tmp/helm-" + client.version %}
{%- set helm_bin = "/usr/bin/helm-" + client.version %}
{%- set helm_home = "/srv/helm/home" %}
{%- if client.tiller.host %}
{%- set helm_run = "helm --host '{}'".format(client.tiller.host) %}
{%- set tiller_arg = "- tiller_host: \"{}\"".format(client.tiller.host) %}
{%- else %}
{%- set helm_run = "helm --tiller-namespace '{}'".format(client.tiller.namespace) %}
{%- set tiller_arg = "- tiller_namespace: \"{}\"".format(client.tiller.namespace) %}
{%- endif %}

{{ helm_tmp }}:
  file.directory:
    - user: root
    - group: root
  archive.extracted:
    - source: {{ client.download_url }}
    - source_hash: {{ client.download_hash }}
    - archive_format: tar
    {%- if grains['saltversioninfo'] < [2016, 11] %}
    - tar_options: v
    {%- else %}
    - options: v
    {%- endif %}
    - if_missing: {{ helm_tmp }}/linux-amd64/helm
    - require:
      - file: {{ helm_tmp }}

{{ helm_bin }}:
  file.managed:
    - source: {{ helm_tmp }}/linux-amd64/helm
    - mode: 555
    - user: root
    - group: root
    - require:
      - archive: {{ helm_tmp }}

/usr/bin/helm:
  file.symlink:
    - target: helm-{{ client.version }}
    - require:
      - file: {{ helm_bin }}

prepare_client:
  cmd.run:
    - name: {{ helm_run }} init --client-only
    - env:
      - HELM_HOME: {{ helm_home }}
    - unless: test -d {{ helm_home }}
    - require:
      - file: /usr/bin/helm

{%- if client.tiller.install %}
install_tiller:
  cmd.run:
    - name: {{ helm_run }} init --upgrade
    - env:
      - HELM_HOME: {{ helm_home }}
    - unless: "{{ helm_run }} version --server --short | grep -E 'Server: v{{ client.version }}(\\+|$)'"
    - require:
      - cmd: prepare_client

wait_for_tiller:
  cmd.run:
    - name: while ! {{ helm_run }} list; do sleep 3; done
    - env:
      - HELM_HOME: {{ helm_home }}
    - onchanges:
      - cmd: install_tiller
{%- endif %}

{%- for repo_name, repo_url in client.repos.items() %}
ensure_{{ repo_name }}_repo:
  cmd.run:
    - name: {{ helm_run }} repo add {{ repo_name }} {{ repo_url }}
    - env:
      - HELM_HOME: {{ helm_home }}
    - unless: {{ helm_run }} repo list | grep '^{{ repo_name }}[[:space:]]{{ repo_url|replace(".", "\.") }}'
    - require:
      - cmd: prepare_client
{%- endfor %}

{%- set namespaces = [] %}
{%- for release_id, release in client.releases.items() %}
{%- set release_name = release.get('name', release_id) %}
{%- set namespace = release.get('namespace', 'default') %}
{%- if release.get('enabled', True) %}
ensure_{{ release_id }}_release:
  helm_release.present:
    - name: {{ release_name }}
    - chart_name: {{ release['chart'] }}
    - namespace: {{ namespace }}
    {{ tiller_arg }}
    {%- if release.get('version') %}
    - version: {{ release['version'] }}
    {%- endif %}
    {%- if release.get('values') %}
    - values:
        {{ release['values']|yaml(False)|indent(8) }}
    {%- endif %}
    - require:
{%- if client.tiller.install %}
      - cmd: wait_for_tiller
{%- endif %}
      - cmd: ensure_{{ namespace }}_namespace
    {%- do namespaces.append(namespace) %}
{%- else %}{# not release.enabled #}
absent_{{ release_id }}_release:
  helm_release.absent:
    - name: {{ release_name }}
    - namespace: {{ namespace }}
    {{ tiller_arg }}
    - require:
{%- if client.tiller.install %}
      - cmd: wait_for_tiller
{%- endif %}
      - cmd: prepare_client
{%- endif %}{# release.enabled #}
{%- endfor %}{# release_id, release in client.releases #}

{%- for namespace in namespaces %}
ensure_{{ namespace }}_namespace:
  cmd.run:
    - name: kubectl create namespace {{ namespace }}
    - unless: kubectl get namespace {{ namespace }}
{%- endfor %}

{%- endif %}
