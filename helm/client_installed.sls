{%- from slspath + "/map.jinja" import config, constants with context %}

include:
  - .kubectl_installed

{%- set tar_opts = "- options: v" %}
{%- if grains['saltversioninfo'] < [2016, 11] %}
{%- set tar_opts = "- tar_options: v" %}
{%- endif %}

{%- set binary_source = "https://storage.googleapis.com/kubernetes-helm/helm-v" + 
                        config.version + "-" + config.flavor + ".tar.gz" %}

{%- set binary_source = config.get(
      "download_url", 
      "https://storage.googleapis.com/kubernetes-helm" +
      "/helm-v" + config.version + "-" + config.flavor + ".tar.gz"
    ) %}

{{ constants.helm.tmp }}:
  archive.extracted:
    - source: {{ binary_source }}
    - source_hash: {{ config.download_hash }}
    - archive_format: tar
    - user: root
    - group: root
    {{ tar_opts }}
    - onlyif:
        - test "{{ config.version }}" -eq "canary" || test ! -e {{ constants.helm.tmp }}/{{ config.flavor }}/helm


{{ config.bin }}:
  file.copy:
    - source: {{ constants.helm.tmp }}/{{ config.flavor }}/helm
    - mode: 555
    - user: root
    - group: root
    - force: true
    - require:
      - archive: {{ constants.helm.tmp }}
    - unless: cmp -s {{ config.bin }} {{ constants.helm.tmp }}/{{ config.flavor }}/helm

prepare_client:
  cmd.run:
    - name: {{ constants.helm.cmd }} init --client-only --home {{ config.helm_home }}
    - unless: test -d {{ config.helm_home }}
    - require:
      - file: {{ config.bin }}
