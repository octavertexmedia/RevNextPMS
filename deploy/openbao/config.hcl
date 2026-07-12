# OpenBao development / single-node file storage config (non-dev mode).
# Used when running: bao server -config=/openbao/config
# Prefer docker-compose "openbao" service in -dev for local work.

ui = true
disable_mlock = true

storage "file" {
  path = "/openbao/file"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr     = "http://0.0.0.0:8200"
cluster_addr = "http://0.0.0.0:8201"
