{%- from "helm/map.jinja" import client with context %}
{%- if client.enabled %}

{%- set helm_tmp = "/tmp/helm-" + client.version %}
{%- set helm_bin = "/usr/bin/helm-" + client.version %}
{%- set helm_home = "/srv/helm/home" %}

{{ helm_tmp }}:
  file.directory:
    - user: root
    - group: root
  archive.extracted:
    - source: {{ client.download_url }}
    - source_hash: {{ client.download_hash }}
    - archive_format: tar
    - tar_options: v
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
    - name: helm init --client-only
    - env:
      - HELM_HOME: {{ helm_home }}
    - unless: test -d {{ helm_home }}
    - require:
      - file: /usr/bin/helm

install_tiller:
  cmd.run:
    - name: helm init --upgrade
    - env:
      - HELM_HOME: {{ helm_home }}
    - unless: "helm version --server --short | grep -E 'Server: v{{ client.version }}(\\+|$)'"
    - require:
      - cmd: prepare_client

wait_for_tiller:
  cmd.run:
    - name: while ! helm list; do sleep 3; done
    - env:
      - HELM_HOME: {{ helm_home }}
    - onchanges:
      - cmd: install_tiller

{%- for repo_name, repo_url in client.repos.items() %}
ensure_{{ repo_name }}_repo:
  cmd.run:
    - name: helm repo add {{ repo_name }} {{ repo_url }}
    - env:
      - HELM_HOME: {{ helm_home }}
    - unless: helm repo list | grep '^{{ repo_name }}[[:space:]]{{ repo_url|replace(".", "\.") }}'
    - require:
      - cmd: prepare_client
{%- endfor %}

{%- for release_id, release in client.releases.items() %}
{%- set release_name = release.get('name', release_id) %}
{%- if release.get('enabled', True) %}
ensure_{{ release_id }}_release:
  helm_release.present:
    - name: {{ release_name }}
    - chart_name: {{ release['chart'] }}
    {%- if release.get('version') %}
    - version: {{ release['version'] }}
    {% endif %}
    {%- if release.get('values') %}
    - values:
        {{ release['values']|yaml(False)|indent(8) }}
    {% endif %}
    - require:
      - cmd: wait_for_tiller
{%- else %}{# not release.enabled #}
absent_{{ release_id }}_release:
  helm_release.absent:
    - name: {{ release_name }}
{%- endif %}{# release.enabled #}
{%- endfor %}{# release_id, release in client.releases #}

{%- endif %}
