#!/usr/bin/env bash
# POST /api/v3/dependence/governance
# 从 JSON 文件或 stdin 读完整 Body，避免为每个新增字段维护 positional 组合。
# 用法:
#   $0 <path/to/request.json>
#   $0 -   # 从 stdin 读 JSON，例如: jq -n --arg s mysvc '{source:$s}' | $0 -
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "usage: $0 <request.json |->" >&2
  echo "  Body 字段以后台为准（如 source、scene、isValid 及后续扩展）；编辑 JSON 即可，无需改脚本。" >&2
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

# 校验 JSON；顺带压缩空白，便于 curl
if ! body=$(printf '%s' "$body" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), separators=(',', ':')))" 2>/dev/null); then
  echo "error: invalid JSON body" >&2
  exit 1
fi

curl -sS -X POST "${HA}/api/v3/dependence/governance" \
  -H 'Content-Type: application/json' \
  -d "$body"
