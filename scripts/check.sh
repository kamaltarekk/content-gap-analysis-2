#!/usr/bin/env bash
set -euo pipefail
(
  cd apps/api
  python -m compileall app
  pytest -q
)
(
  cd apps/web
  npm run typecheck
  npm run build
)
