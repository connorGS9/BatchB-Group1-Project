#!/bin/bash
# deploy/make-env.sh
# Creates the server's .env with fresh random secrets (run once, from the project folder).
# The file is readable only by you (chmod 600) and is never committed (.gitignore).
#   bash deploy/make-env.sh https://d123abc.cloudfront.net
set -euo pipefail
CLOUDFRONT_URL="${1:-}"
if [ -f .env ]; then echo ".env already exists - not overwriting it."; exit 0; fi
rand() { python3 -c "import secrets; print(secrets.token_urlsafe(32))"; }
cat > .env <<ENV
MONGO_USER=bankadmin
MONGO_PASSWORD=$(rand)
MONGO_URL=unused-in-docker
JWT_SECRET=$(rand)
API_KEY=$(rand)
CORS_ORIGINS=${CLOUDFRONT_URL:-http://localhost:5173}
ENV
chmod 600 .env
echo "Created .env (secrets hidden). API_KEY for Postman:"
grep '^API_KEY=' .env | cut -d= -f2
