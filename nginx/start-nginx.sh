#!/bin/sh
set -e

echo "🔧 Preparing Nginx configuration..."

ACTIVE_SERVICE="${ACTIVE_POOL}_service"
INACTIVE_SERVICE="${INACTIVE_POOL}_service"

export ACTIVE_SERVICE
export INACTIVE_SERVICE

if [ "$ACTIVE_POOL" = "blue" ]; then
  ACTIVE_RELEASE_ID="$RELEASE_ID_BLUE"
else
  ACTIVE_RELEASE_ID="$RELEASE_ID_GREEN"
fi

export ACTIVE_RELEASE_ID

# Render config safely
envsubst '\$ACTIVE_SERVICE \$INACTIVE_SERVICE \$ACTIVE_POOL \$INACTIVE_POOL \$ACTIVE_RELEASE_ID' \
  < /etc/nginx/templates/nginx.conf.template \
  > /etc/nginx/conf.d/default.conf

echo "✅ Generated config:"
cat /etc/nginx/conf.d/default.conf

echo "🚀 Starting Nginx with Active Service: $ACTIVE_SERVICE"
nginx -g 'daemon off;'
