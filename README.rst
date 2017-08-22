
==================================
helm
==================================

This formula installs Helm client, installs Tiller on Kubernetes cluster and
creates releases in it.

Sample pillars
==============

Enable formula, install helm client on node and tiller on Kubernetes (assuming
already configured kubectl config or local cluster endpoint):

.. code-block:: yaml

    helm:
      client:
        enabled: true

Change version of helm being downloaded and installed:

.. code-block:: yaml

    helm:
      client:
        version: 2.6.0  # defaults to 2.4.2 currently
        download_hash: sha256=youneedtocalculatehashandputithere

Don't install tiller and use existing one exposed on some well-known address:

.. code-block:: yaml

    helm:
      client:
        tiller:
          install: false
          host: 10.11.12.13:14151

Change namespace where tiller is isntalled and looked for:

.. code-block:: yaml

    helm:
      client:
        tiller:
          namespace: not-kube-system  # kube-system is default

Install Mirantis repository and deploy zookeper chart from it:

.. code-block:: yaml

    helm:
      client:
        repos:
          mirantisworkloads: https://mirantisworkloads.storage.googleapis.com/
        releases:
          zoo1:
            name: my-zookeeper
            chart: mirantisworkloads/zookeeper  # we reference installed repo
            version: 1.2.0  # select any available version
            values:
              logLevel: INFO  # any values used by chart can specified here

Delete that release:

.. code-block:: yaml

    helm:
      client:
        repos:
          mirantisworkloads: https://mirantisworkloads.storage.googleapis.com/
        releases:
          zoo1:
            enabled: false

Install kubectl and manage remote cluster:

.. code-block:: yaml

    helm:
      client:
        kubectl:
          install: true  # installs kubectl 1.6.7 by default
          config:
            cluster:  # directly translated to cluster definition in kubeconfig
              server: https://kubernetes.example.com
              certificate-authority-data: base64_of_ca_certificate
            user:  # same for user
              username: admin
              password: uberadminpass

Change kubectl download URL and use it with GKE-based cluster:

.. code-block:: yaml

    helm:
      client:
        kubectl:
          install: true
          download_url: https://dl.k8s.io/v1.6.7/kubernetes-client-linux-amd64.tar.gz
          download_hash: sha256=calculate_hash_here
          config:
            cluster:  # directly translated to cluster definition in kubeconfig
              server: https://3.141.59.265
              certificate-authority-data: base64_of_ca_certificate
            user:
              auth-provider:
                name: gcp
            gce_service_token: base64_of_json_token_downloaded_from_cloud_console


Development and testing
=======================

Development and test workflow with `Test Kitchen <http://kitchen.ci>`_ and
`kitchen-salt <https://github.com/simonmcc/kitchen-salt>`_ provisioner plugin.

Test Kitchen is a test harness tool to execute your configured code on one or more platforms in isolation.
There is a ``.kitchen.yml`` in main directory that defines *platforms* to be tested and *suites* to execute on them.

Kitchen CI can spin instances locally or remote, based on used *driver*.
For local development ``.kitchen.yml`` defines a `vagrant <https://github.com/test-kitchen/kitchen-vagrant>`_ or
`docker  <https://github.com/test-kitchen/kitchen-docker>`_ driver.

To use backend drivers or implement your CI follow the section `INTEGRATION.rst#Continuous Integration`__.

The `Busser <https://github.com/test-kitchen/busser>`_ *Verifier* is used to setup and run tests
implementated in `<repo>/test/integration`. It installs the particular driver to tested instance
(`Serverspec <https://github.com/neillturner/kitchen-verifier-serverspec>`_,
`InSpec <https://github.com/chef/kitchen-inspec>`_, Shell, Bats, ...) prior the verification is executed.

Usage:

.. code-block:: shell

  # list instances and status
  kitchen list

  # manually execute integration tests
  kitchen [test || [create|converge|verify|exec|login|destroy|...]] [instance] -t tests/integration

  # use with provided Makefile (ie: within CI pipeline)
  make kitchen



Read more
=========

* links
