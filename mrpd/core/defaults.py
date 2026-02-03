# Canonical public MRP registry host (once deployed)
MRP_DEFAULT_REGISTRY_BASE = "https://www.moltrouter.dev"

# Fallback registry source (raw JSON list). Use ONLY if explicitly configured.
# We default to the hosted registry API on https://www.moltrouter.dev.
# Env var: MRP_BOOTSTRAP_REGISTRY_RAW (supports file:// for local testing)
MRP_BOOTSTRAP_REGISTRY_RAW = None
