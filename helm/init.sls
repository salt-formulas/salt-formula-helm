{%- if pillar.helm is defined %}
include:
  - .releases_managed
{%- endif %}
