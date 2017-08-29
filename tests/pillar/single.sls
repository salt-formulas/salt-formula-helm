helm:
  client:
    enabled: true
    version: 2.6.0
    download_url: https://storage.googleapis.com/kubernetes-helm/helm-v2.6.0-linux-amd64.tar.gz
    download_hash: sha256=506e477a9eb61730a2fb1af035357d35f9581a4ffbc093b59e2c2af7ea3beb41
    bind:
      address: 0.0.0.0
    tiller:
      install: false
      host: 10.11.12.13:14151
    kubectl:
      install: true  # installs kubectl 1.6.7 by default
      download_url: https://dl.k8s.io/v1.6.7/kubernetes-client-linux-amd64.tar.gz
      download_hash: sha256=54947ef84181e89f9dbacedd54717cbed5cc7f9c36cb37bc8afc9097648e2c91
      tarball_path: kubernetes/client/bin/kubectl
      config:
        cluster:  # directly translated to cluster definition in kubeconfig
          server: https://kubernetes.example.com
          certificate-authority-data: Y2FfY2VydGlmaWNhdGU=
        user:  # same for user
          username: admin
          password: uberadminpass
        gce_service_token: anNvbl90b2tlbg==
    repos:
      mirantisworkloads: https://mirantisworkloads.storage.googleapis.com/
    releases:
      zoo1:
        enabled: false