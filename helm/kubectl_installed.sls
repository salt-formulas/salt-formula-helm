{%- from slspath + "/map.jinja" import config, constants with context %}
{%- set extraction_path = constants.helm.tmp + 
                          "/kubectl/v" + config.kubectl.version %}
{%- set extracted_binary_path = extraction_path +
                                "/kubernetes/client/bin/kubectl" %}

{%- set binary_source = config.kubectl.get(
      "download_url", 
      "https://dl.k8s.io/v" + config.kubectl.version + 
      "/kubernetes-client-" + config.flavor + ".tar.gz"
    ) %}

{%- if config.kubectl.install %}
extract_kubectl:
  archive.extracted:
    - name: {{ extraction_path }}
    - source: {{ binary_source }}
    - source_hash: {{ config.kubectl.download_hash }}
    - archive_format: tar
    {%- if grains['saltversioninfo'] < [2016, 11] %}
    - tar_options: v
    {%- else %}
    - options: v
    {%- endif %}
    - onlyif:
          - test ! -e {{ extracted_binary_path }}

{{ config.kubectl.bin }}:
  file.managed:
    - source: {{ extracted_binary_path }}
    - mode: 555
    - user: root
    - group: root
    - require:
      - archive: extract_kubectl
    - unless: cmp -s {{ config.kubectl.bin }} {{ extracted_binary_path }}
{%- endif %}