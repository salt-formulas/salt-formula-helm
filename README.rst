
============
Helm formula
============

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


More Information
================

* https://github.com/kubernetes/charts
* https://fabric8.io/helm/


Documentation and Bugs
======================

To learn how to install and update salt-formulas, consult the documentation
available online at:

    http://salt-formulas.readthedocs.io/

In the unfortunate event that bugs are discovered, they should be reported to
the appropriate issue tracker. Use Github issue tracker for specific salt
formula:

    https://github.com/salt-formulas/salt-formula-helm/issues

For feature requests, bug reports or blueprints affecting entire ecosystem,
use Launchpad salt-formulas project:

    https://launchpad.net/salt-formulas

You can also join salt-formulas-users team and subscribe to mailing list:

    https://launchpad.net/~salt-formulas-users

Developers wishing to work on the salt-formulas projects should always base
their work on master branch and submit pull request against specific formula.

    https://github.com/salt-formulas/salt-formula-home-assistant

Any questions or feedback is always welcome so feel free to join our IRC
channel:

    #salt-formulas @ irc.freenode.net
