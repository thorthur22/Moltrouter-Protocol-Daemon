# Canonical public MRP registry host (once deployed)
MRP_DEFAULT_REGISTRY_BASE = "https://www.moltrouter.dev"

# Fallback registry source (raw JSON list) when registry API is unavailable.
# Can be overridden with env var: MRP_BOOTSTRAP_REGISTRY_RAW
MRP_BOOTSTRAP_REGISTRY_RAW = "https://raw.githubusercontent.com/thorthur22/moltrouter-registry/main/data/registry.json"
