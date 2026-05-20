#!/usr/bin/env bash
# POST /api/llm-skill/direct-relations
# 获取服务上下游；可选 bizLines、scenes 做剪枝。Body 以后台为准。
# 用法:
#   $0 <path/to/request.json>
#   $0 -   # 从 stdin 读 JSON
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: $0 <request.json |->" >&2
  echo "  示例 Body: {\"svc\":\"searchapi-service-default\",\"direction\":\"both\",\"bizLines\":[\"search\"],\"scenes\":[\"shequsearch\"]}" >&2
  exit 1
fi
HA="${HA_DEVOPS_API_BASE:-https://ha.devops.xiaohongshu.com}"
HA="${HA%/}"

if [[ "$1" == - ]]; then
  body=$(cat)
else
  if [[ ! -f "$1" ]]; then
    echo "error: file not found: $1" >&2
    exit 1
  fi
  body=$(cat "$1")
fi

if ! body=$(printf '%s' "$body" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), separators=(',', ':')))" 2>/dev/null); then
  echo "error: invalid JSON body" >&2
  exit 1
fi

curl -sS -X POST "${HA}/api/llm-skill/direct-relations" \
  -H 'Content-Type: application/json' \
  -d "$body"
