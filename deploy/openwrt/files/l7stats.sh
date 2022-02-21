#!/bin/sh

PYTHON="$(which python3 2>/dev/null)"

if [ -z "$PYTHON" ]; then
    PYTHON="$(which python3.9 2>/dev/null)"
fi

if [ -z "$PYTHON" ]; then
    echo "Unable to locate Python3 interpreter."
    exit 1
fi

# Temporary workaround until OpenWrt start/stop fixed
mkdir -p /var/run/l7stats

exec $PYTHON -Es /usr/share/netify-fwa/l7stats
