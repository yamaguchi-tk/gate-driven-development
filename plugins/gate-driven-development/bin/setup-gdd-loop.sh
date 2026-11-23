#!/usr/bin/env bash
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$PLUGIN_ROOT/scripts/setup-gdd-loop.sh" "$@"
