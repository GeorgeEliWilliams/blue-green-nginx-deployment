#!/bin/sh
# Recreate actual log files instead of using Docker symlinks
mkdir -p /var/log/nginx

# Remove symlinks to stdout/stderr (the default behavior)
rm -f /var/log/nginx/access.log /var/log/nginx/error.log

# Create real log files
touch /var/log/nginx/access.log /var/log/nginx/error.log

# Give permissions
chmod 666 /var/log/nginx/*.log

