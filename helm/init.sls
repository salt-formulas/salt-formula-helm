{%- if pillar.helm is defined %}
include:
{%- if pillar.helm.client is defined %}
- helm.client
{%- endif %}
{%- endif %}
