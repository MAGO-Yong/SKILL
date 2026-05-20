#!/usr/bin/env bash
# GET /api/v3/employee/query?key= — key：花名、邮箱、姓名、姓名拼音等（见 stability-metadata/SKILL.md §2）
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: $0 <key>" >&2
  exit 1
fi
HA="${HA_DEVOPS_API_BASE:-https://ha.devops.xiaohongshu.com}"
HA="${HA%/}"
curl -sS -G "${HA}/api/v3/employee/query" --data-urlencode "key=$1"
