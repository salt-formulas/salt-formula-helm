==========
User guide
==========

.. highlight:: yaml

Instalation
===========

Our formula is already being installed from `system level <https://github.com/Mirantis/reclass-system-salt-model/blob/master/salt/master/pkg.yml>`_
so if you have ``system.salt.master.pkg`` or ``system.salt.master.git`` class
on your config node, you don't need to do anything.

Using class from system level
-----------------------------

You can use ``system.salt.master.formula.pkg.helm`` `class <https://github.com/Mirantis/reclass-system-salt-model/blob/master/salt/master/formula/pkg/helm.yml>`_
to install from packages or include following to some part of config node
model::

  parameters:
    salt:
      master:
        environment:
          prd:
            formula:
              helm:
                source: pkg
                name: salt-formula-helm

If you want to isntall from Git repo, you can use ``system.salt.master.formula.git.helm`` `class <https://github.com/Mirantis/reclass-system-salt-model/blob/master/salt/master/formula/git/helm.yml>`_
or following snippet::

  parameters:
    salt:
      master:
        environment:
          prd:
            formula:
              helm:
                source: git
                address: '${_param:salt_master_environment_repository}/salt-formula-helm.git'
                revision: ${_param:salt_master_environment_revision}
                module:
                  helm.py:
                    enabled: true
                state:
                  helm_release.py:
                    enabled: true

Using apt
---------

You can also just install using ``apt`` from our repo at `<http://apt-mk.mirantis.com/>`_:

.. code-block:: bash

  apt install salt-formula-helm

Basic usage
===========

The most simple way to use this formula is to include ``service.helm.client``
class or one derived from it to one of your Kubernetes controllers. Following
our cookiecutter model structure, if you create file at ``classes/cluster/<cluster name>/kubernetes/helm.yml``
with following contents (we'll use this file throughout this guide)::

  classes:
  - service.helm.client

and then add it to one of kubernetes controllers by adding to ``reclass:storage:node``
section of ``classes/cluster/<cluster name>/infra/config.yml`` file::

  kubernetes_control_node01:
  - cluster.${_param:cluster_name}.kubernetes.helm

And then run ``reclass`` state and ``refresh_pillar`` method:

.. code-block:: bash

  salt -I 'salt:master' state.sls reclass
  salt '*' saltutil.refresh_pillar

Now you can address this node via ``helm:client`` pillar value:

.. code-block:: bash

  salt -I 'helm:client' state.sls helm

After you run this, the state will install ``helm`` binary on selected node and
deploy Tiller on Kubernetes cluster.

Release creation
----------------

To create some release, you should add its description to
``helm:client:releases`` section of the model::

  classes:
  - service.helm.client
  parameters:
    helm:
      client:
        releases:
          my-first-sql:  # This name is used by default as release name
            name: the-mysql  # But can be overriden here
            chart: stable/mysql  # This chart exists in default helm repo

After this if you run ``helm`` state

.. code-block:: bash

  salt -I 'helm:client' state.sls helm

``the-mysql`` release will be created in Tiller in ``default`` namespace.

Using Mirantis chart repository
-------------------------------

To use charts from Mirantis chart repository you must describe it in model and
use it in ``chart``::

  helm:
    client:
      repos:
        mirantisworkloads: https://mirantisworkloads.storage.googleapis.com/
      releases:
        zoo1:
          name: my-zookeeper
          chart: mirantisworkloads/zookeeper  # we reference installed repo

This pillar will install latest version of Zookeeper chart from Mirantis
repository.

Release customizations
----------------------

You can change namespace where the release is created, version of chart to use
and specify any values to pass to the chart::

 releases:
   zoo1:
     chart: mirantisworkloads/zookeeper
     namespace: different-ns  # Namespace will be created if absent
     version: 1.2.0  # select any available version
     values:
       logLevel: INFO  # any values used by chart can specified here

Note that after initial deployment, you can change these values (except
namespace) if chart supports it.

.. note::

  In Kubernetes versions up to 1.6 statefulsets cannot be upgraded, so you
  cannot change version of chart that creates statefulset, like our Zookeeper
  chart.

Release deletion
----------------

To ensure that release is absent, you should set its ``enable`` parameter to
``false``::

  releases:
    zoo1:
      name: my-zookeeper  # Note that releases are identified in Tiller by name
                          # so you must leave custom name if you've specified
                          # one.
      enabled: false

After this model is applied, ``my-zookeeper`` release will be deleted.

Running on remote Kubernetes
============================

Up to this point we assumed that Helm formula is applied to controller node of
existing Kubernetes cluster with already installed and configured ``kubectl``.
If you want to use it with some remote Kubernetes or on any different node
(e.g. Salt Master node), you'll need to install and configure ``kubectl`` on
it.

For example, to run it on our cluster, you should add ``cluster.<cluster name>.kubernetes.helm``
class to config node in ``nodes/<your config node fqdn>.yml``, and then modify
``classes/cluster/<cluster name>/kubernetes/helm.yml``::

  helm:
    client:
      kubectl:
        install: true
        config:
          user: 
            username: ${_param:kubernetes_admin_user}
            password: ${_param:kubernetes_admin_password}
          cluster:
            server: https://${_param:kubernetes_control_address}
            certificate_authority: /etc/ssl/certs/ca-salt_master_ca.crt

Note that we're using parameters that are already specified in ``cluster.<cluster name>.kubernetes``
class for simplicity. We are also using path to CA certificate specifit to
config node. If you don't have such file, you'll have to specify base64
representation of certificate file in ``certificate_authority_data``.

Now if we apply state ``helm`` to our config node, both ``helm`` and ``kubectl``
binaries will be installed and ``kubectl`` config will be created in
``/srv/helm/kubeconfig.yaml``.
