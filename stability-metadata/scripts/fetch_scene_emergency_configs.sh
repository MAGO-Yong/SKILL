#!/usr/bin/env bash
# GET /api/meta/biz-line/scene/{scenePathSegment}/configs
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: $0 <scenePathSegment>" >&2
  exit 1
fi
seg="$1"
HA="${HA_DEVOPS_API_BASE:-https://ha.devops.xiaohongshu.com}"
HA="${HA%/}"
curl -sS "${HA}/api/meta/biz-line/scene/${seg}/configs"
