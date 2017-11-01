
============
Helm formula
============

This formula installs Helm client, installs Tiller on Kubernetes cluster and
manages releases in it.

Availale States
===============

The default state applied by this formula (e.g. if just applying `helm`) will
apply the `helm.releases_managed` state.

`kubectl_installed`
------------------

Optionally installs the kubectl binary per the configured pillar values,
such as the version of `kubectl` to instlal and the path where the binary should
be installed.

`kubectl_configured`
------------------

Manages a kubectl configuration file and gce_token json file per the configured
pillar values. Note that the available configuration values allow the path of
the kube config file to be placed at a different location than the default 
installation path; this is recommended to avoid confusion if the kubectl 
binary on the minion might be manually used with multiple contexts.

**includes**:
* `kubectl_installed`

`client_installed`
------------------

Installs the helm client binary per the configured pillar values, such as where 
helm home should be, which version of the helm binary to install and that path
for the helm binary.

**includes**:
* `kubectl_installed

`tiller_installed`
------------------

Optionally installs a Tiller deployment to the kubernetes cluster per the
`helm:client:tiller:install` pillar value. If the pillar value is set to 
install tiller to the cluster, the version of the tiller installation will
match the version of the Helm client installed per the `helm:client:version`
configuration parameter

**includes**:
* `client_installed`
* `kubectl_configured`

`repos_managed`
------------------

Ensures the repositories configured per the pillar (and only those repositories) 
are registered at the configured helm home, and synchronizes the local cache 
with the remote repository with each state execution.

**includes**:
* `client_installed`

`releases_managed`
------------------

Ensures the releases configured with the pillar are in the expected state with
the Kubernetes cluster. This state includes change detection to determine 
whether the pillar configurations match the release's state in the cluster.

Note that changes to an existing release's namespace will trigger a deletion and 
re-installation of the release to the cluster.

**includes**:
* `client_installed`
* `tiller_installed`
* `kubectl_configured`
* `repos_managed`

Availale Modules
===============

To view documentation on the available modules, run: 

`salt '{{ tgt }}' sys.doc helm`


Sample pillars
==============

See the [default reclass pillar configuration](metadata/service/client.yml) for 
a documented example pillar file.

Example Configurations
======================

_The following examples demonstrate configuring the formula for different
use cases._

The default pillar configuration will install the helm client on the target 
node, and Tiller to the Kubernetes cluster (assuming kubectl config or local 
cluster endpoint have already been configured.

Change version of helm being downloaded and installed:

.. code-block:: yaml

    helm:
      client:
        version: 2.6.0  # defaults to 2.6.2 currently
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
            # directly translated to cluster definition in kubeconfig
            cluster: 
              server: https://kubernetes.example.com
              certificate-authority-data: base64_of_ca_certificate
            cluster_name: kubernetes.example
            # directly translated to user definition in kubeconfig
            user:
              username: admin
              password: uberadminpass
            user_name: admin 

Change kubectl download URL and use it with GKE-based cluster:

.. code-block:: yaml

    helm:
      client:
        kubectl:
          install: true
          download_url: https://dl.k8s.io/v1.6.7/kubernetes-client-linux-amd64.tar.gz
          download_hash: sha256=calculate_hash_here
          config:
            # directly translated to cluster definition in kubeconfig
            cluster:
              server: https://3.141.59.265
              certificate-authority-data: base64_of_ca_certificate
            # directly translated to user definition in kubeconfig
            user:
              auth-provider:
                name: gcp
            user_name: gce_user
            gce_service_token: base64_of_json_token_downloaded_from_cloud_console

Known Issues
============

1. Unable to remove all user supplied values

If a release previously has had user supplied value overrides (via the 
release's `values` key in the pillar), subsequently removing all `values`
overrides (so that there is no more `values` key for the release in the 
pillar) will not actually update the Helm deployment. To get around this,
specify a fake key/value pair in the release's pillar; Tiller will override
all previously user-supplied values with the new fake key and value. For 
example:


.. code-block:: yaml
    helm:
      client:
        releases:
          zoo1:
            enabled: true
            ...
            values:
              fake_key: fake_value


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
