{%- from "helm/map.jinja" import client with context %}
{%- if client.enabled %}

{%- set helm_tmp = "/tmp/helm-" + client.version %}
{%- set helm_bin = "/usr/bin/helm-" + client.version %}

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
    - unless: test -d /root/.helm
    - require:
      - file: /usr/bin/helm

install_tiller:
  cmd.run:
    - name: helm init --upgrade
    - unless: "helm version --server --short | grep -E 'Server: v{{ client.version }}(\\+|$)'"
    - require:
      - cmd: prepare_client
{%- endif %}
