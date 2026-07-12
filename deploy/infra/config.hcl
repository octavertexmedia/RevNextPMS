# OpenBao single-node file storage (production-style, not -dev).
# Mounted at /openbao/config/config.hcl in revnext_secrets_openbao.

ui = true

storage "file" {
  path = "/openbao/file"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true
}

api_addr     = "http://0.0.0.0:8200"
cluster_addr = "http://0.0.0.0:8201"
