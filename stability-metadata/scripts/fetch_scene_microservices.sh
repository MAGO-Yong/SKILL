#!/usr/bin/env bash
# GET /api/v3/scene?with_microservices=true&id=
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: $0 <sceneId>" >&2
  exit 1
fi
HA="${HA_DEVOPS_API_BASE:-https://ha.devops.xiaohongshu.com}"
HA="${HA%/}"
curl -sS -G "${HA}/api/v3/scene" \
  --data-urlencode "with_microservices=true" \
  --data-urlencode "id=$1"
