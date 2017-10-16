helm:
  client:
    enabled: true
    version: 2.6.0
    download_hash: sha256=506e477a9eb61730a2fb1af035357d35f9581a4ffbc093b59e2c2af7ea3beb41
    tiller:
      install: false
      host: 10.11.12.13:14151
    kubectl:
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