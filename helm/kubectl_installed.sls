{%- from slspath + "/map.jinja" import config, constants with context %}

{%- if config.kubectl.install %}
extract_kubectl:
  archive.extracted:
    - name: {{ constants.helm.tmp }}/kubectl/v{{ config.kubectl.version }}
    - source: https://dl.k8s.io/v{{ config.kubectl.version }}/kubernetes-client-linux-amd64.tar.gz
    - source_hash: {{ config.kubectl.download_hash }}
    - archive_format: tar
    {%- if grains['saltversioninfo'] < [2016, 11] %}
    - tar_options: v
    {%- else %}
    - options: v
    {%- endif %}
    - if_missing: {{ constants.helm.tmp }}/kubectl/v{{ config.kubectl.version }}
    - require:
      - file: {{ constants.helm.tmp }}

{{ constants.kubectl.bin }}:
  file.managed:
    - source: {{ constants.helm.tmp }}/kubectl/v{{ config.kubectl.version }}/kubernetes/client/bin/kubectl
    - mode: 555
    - user: root
    - group: root
    - require:
      - archive: extract_kubectl
{%- endif %}