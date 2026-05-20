#!/usr/bin/env bash
# 批量认领 xray 告警事件
# 用法:
#   claim.sh --user <email>  [--start now-10m] [--end now] [--env prod] [--dry-run]
#   claim.sh --app  <path>   [--start now-10m] [--end now] [--env prod] [--dry-run]
# --dry-run: 只列出待认领清单，不执行 claim，供用户确认。
set -euo pipefail

install_xray_cli() {
  echo "==> 未检测到 xray-cli，开始安装（小红书内网 npm 源）..." >&2
  if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: 未找到 npm，请先安装 Node.js。" >&2
    return 1
  fi
  mkdir -p "$HOME/.npm-global"
  npm config set prefix "$HOME/.npm-global"
  npm install -g --registry http://npm.devops.xiaohongshu.com:7001/ @xray/xray-cli
  export PATH="$HOME/.npm-global/bin:$PATH"
  persist_path_to_rc
  echo "==> 安装完成。请跑一次: xray-cli auth login" >&2
}

# 把 export PATH 行写入用户 shell rc 文件（幂等：已存在则跳过）。
persist_path_to_rc() {
  local line='export PATH="$HOME/.npm-global/bin:$PATH"'
  local marker='# xray-cli npm-global path'
  local rc
  for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    [[ -f "$rc" ]] || continue
    if grep -Fq "$marker" "$rc" 2>/dev/null; then
      echo "==> $rc 已包含 PATH 配置，跳过。" >&2
    else
      printf '\n%s\n%s\n' "$marker" "$line" >> "$rc"
      echo "==> 已追加 PATH 配置到 $rc，新开 shell 生效。" >&2
    fi
  done
}

ensure_xray_cli() {
  if ! command -v xray-cli >/dev/null 2>&1; then
    install_xray_cli || exit 1
  fi
}

# alarm event claim 自 v0.0.27 起提供。比较版本字符串（去掉 v 前缀，按点分段数值比较）。
ensure_xray_cli_version() {
  local need="$1" got
  got=$(xray-cli --version 2>/dev/null | awk '{print $NF}' | sed 's/^v//')
  if [[ -z "$got" ]]; then
    echo "ERROR: 无法解析 xray-cli --version 输出。" >&2; exit 1
  fi
  # 用 sort -V 判断 got 是否 >= need
  if [[ "$(printf '%s\n%s\n' "$need" "$got" | sort -V | head -1)" != "$need" ]]; then
    echo "ERROR: xray-cli 版本 v$got 过低，alarm event claim 需要 v$need 及以上。" >&2
    echo "       请运行 xray-cli 触发自更新，或: npm install -g --registry http://npm.devops.xiaohongshu.com:7001/ @xray/xray-cli" >&2
    exit 1
  fi
}

USER_EMAIL=""
APP_PATH=""
START="now-10m"
END="now"
ENV="prod"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user)    USER_EMAIL="$2"; shift 2 ;;
    --app)     APP_PATH="$2";   shift 2 ;;
    --start)   START="$2";      shift 2 ;;
    --end)     END="$2";        shift 2 ;;
    --env)     ENV="$2";        shift 2 ;;
    --dry-run) DRY_RUN=1;       shift ;;
    -h|--help)
      sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$USER_EMAIL" && -z "$APP_PATH" ]]; then
  echo "must provide --user <email> or --app <path>" >&2; exit 2
fi
if [[ -n "$USER_EMAIL" && -n "$APP_PATH" ]]; then
  echo "--user and --app are mutually exclusive" >&2; exit 2
fi

ensure_xray_cli
ensure_xray_cli_version "0.0.27"

FILTER_FLAG=(); SCOPE=""
if [[ -n "$USER_EMAIL" ]]; then
  FILTER_FLAG=(--receive-users "$USER_EMAIL"); SCOPE="receive-users=$USER_EMAIL"
else
  FILTER_FLAG=(--apps "$APP_PATH"); SCOPE="apps=$APP_PATH"
fi

# 分页拉取所有事件（避免单页 page-size 上限导致截断）。
PAGE_SIZE=200
PAGE=1
TOTAL=0; CLAIMED=0; RESTORED=0; PENDING=0
IDS=""
DRY_LINES=""
while :; do
  PAGE_JSON=$(xray-cli --env "$ENV" --output-format json alarm event list \
    "${FILTER_FLAG[@]}" --start "$START" --end "$END" \
    --page "$PAGE" --page-size "$PAGE_SIZE")
  PAGE_COUNT=$(printf '%s' "$PAGE_JSON" | xray-cli tool jq '.events | length')
  [[ "$PAGE_COUNT" -eq 0 ]] && break

  TOTAL=$((TOTAL + PAGE_COUNT))
  CLAIMED=$((CLAIMED + $(printf '%s' "$PAGE_JSON" | xray-cli tool jq '[.events[] | select(.reacted==true)] | length')))
  RESTORED=$((RESTORED + $(printf '%s' "$PAGE_JSON" | xray-cli tool jq '[.events[] | select(.reacted==false) | select(.restore_time!="")] | length')))

  PAGE_IDS=$(printf '%s' "$PAGE_JSON" | xray-cli tool jq -r '.events[] | select(.reacted==false) | select(.restore_time=="") | .id')
  if [[ -n "$PAGE_IDS" ]]; then
    IDS+="${IDS:+$'\n'}$PAGE_IDS"
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    PAGE_DRY=$(printf '%s' "$PAGE_JSON" | xray-cli tool jq -r '
      .events[] | select(.reacted==false) | select(.restore_time=="") |
      "  \(.id)\t\(.level)\t\(.app)\t\(.trigger_time)\t\(.rule_name)"')
    if [[ -n "$PAGE_DRY" ]]; then
      DRY_LINES+="${DRY_LINES:+$'\n'}$PAGE_DRY"
    fi
  fi

  [[ "$PAGE_COUNT" -lt "$PAGE_SIZE" ]] && break
  PAGE=$((PAGE + 1))
done
PENDING=$(printf '%s' "$IDS" | grep -c . || true)

echo "认领窗口: $START ~ $END"
echo "范围: $SCOPE   (env=$ENV)"
echo "扫描事件: $TOTAL 条 (已认领: $CLAIMED / 已恢复未认领: $RESTORED / 待认领: $PENDING)"

if [[ "$PENDING" -eq 0 ]]; then
  echo "无待认领事件，退出。"; exit 0
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "--- 待认领清单 (dry-run) ---"
  printf '%s\n' "$DRY_LINES"
  echo "--- 未执行 claim。去掉 --dry-run 重新运行以认领。---"
  exit 0
fi

OK=0; FAIL=0; FAIL_IDS=()
for id in $IDS; do
  if xray-cli --env "$ENV" alarm event claim "$id" >/dev/null 2>&1; then
    echo "  ok   $id"; OK=$((OK+1))
  else
    echo "  FAIL $id"; FAIL=$((FAIL+1)); FAIL_IDS+=("$id")
  fi
done

echo "认领成功: $OK / 失败: $FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  echo "失败 id: ${FAIL_IDS[*]}"; exit 1
fi
