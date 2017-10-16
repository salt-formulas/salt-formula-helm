{%- from slspath + "/map.jinja" import config, constants with context %}

include:
  - .kubectl_installed

{{ constants.helm.tmp }}:
  file.directory:
    - user: root
    - group: root
  archive.extracted:
    - source: https://storage.googleapis.com/kubernetes-helm/helm-v{{ config.version }}-{{ config.flavor }}.tar.gz
    - source_hash: {{ config.download_hash }}
    - archive_format: tar
    {%- if grains['saltversioninfo'] < [2016, 11] %}
    - tar_options: v
    {%- else %}
    - options: v
    {%- endif %}
    - if_missing: {{ constants.helm.tmp }}/{{ config.flavor }}/helm
    - require:
      - file: {{ constants.helm.tmp }}

{{ constants.helm.bin }}:
  file.managed:
    - source: {{ constants.helm.tmp }}/{{ config.flavor }}/helm
    - mode: 555
    - user: root
    - group: root
    - require:
      - archive: {{ constants.helm.tmp }}

/usr/bin/helm:
  file.symlink:
    - target: helm-v{{ config.version }}
    - require:
      - file: {{ constants.helm.bin }}

prepare_client:
  cmd.run:
    - name: {{ constants.helm.cmd }} init --client-only
    - env:
      - HELM_HOME: {{ constants.helm.home }}
    - unless: test -d {{ constants.helm.home }}
    - require:
      - file: {{ constants.helm.bin }}
