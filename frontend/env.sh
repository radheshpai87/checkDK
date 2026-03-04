#!/bin/sh
# Generate /usr/share/nginx/html/env-config.js from runtime env vars.
# This script runs as the Docker ENTRYPOINT so the frontend can read
# CHECKDK_API_URL (and future vars) without a rebuild.

ENV_JS=/usr/share/nginx/html/env-config.js

cat <<EOF > "$ENV_JS"
window.__CHECKDK_ENV__ = {
  CHECKDK_API_URL: "${CHECKDK_API_URL:-}"
};
EOF

exec "$@"
