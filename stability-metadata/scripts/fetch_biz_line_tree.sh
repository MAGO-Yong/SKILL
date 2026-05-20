#!/usr/bin/env bash
# GET /api/meta/biz-line/tree?treeType=biz
set -euo pipefail
HA="${HA_DEVOPS_API_BASE:-https://ha.devops.xiaohongshu.com}"
HA="${HA%/}"
curl -sS -G "${HA}/api/meta/biz-line/tree" --data-urlencode "treeType=biz"
