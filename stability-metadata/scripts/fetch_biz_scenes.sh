#!/usr/bin/env bash
# GET /api/meta/biz-line/{bizLineSegment}/scenes — 无 bizId Query，业务线由路径段决定
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: $0 <bizLineSegment>" >&2
  exit 1
fi
seg="$1"
HA="${HA_DEVOPS_API_BASE:-https://ha.devops.xiaohongshu.com}"
HA="${HA%/}"
curl -sS "${HA}/api/meta/biz-line/${seg}/scenes"
