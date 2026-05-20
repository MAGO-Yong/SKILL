#!/usr/bin/env bash
# GET /api/llm-skill/std-alias?svc= — 查询服务标准名与别名
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: $0 <svc>" >&2
  echo "  示例: $0 com.xiaohongshu.ads.sdk.AdsService" >&2
  exit 1
fi
HA="${HA_DEVOPS_API_BASE:-https://ha.devops.xiaohongshu.com}"
HA="${HA%/}"
curl -sS -G "${HA}/api/llm-skill/std-alias" --data-urlencode "svc=$1"
