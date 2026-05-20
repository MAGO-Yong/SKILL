#!/usr/bin/env bash
set -euo pipefail

if [[ -d "/opt/homebrew/opt/openjdk@11" ]]; then
  export JAVA_HOME="/opt/homebrew/opt/openjdk@11"
elif [[ -d "/usr/local/opt/openjdk@11" ]]; then
  export JAVA_HOME="/usr/local/opt/openjdk@11"
else
  export JAVA_HOME="$(/usr/libexec/java_home -v 11 2>/dev/null || true)"
fi

if [[ -z "${JAVA_HOME:-}" || ! -x "$JAVA_HOME/bin/java" ]]; then
  echo "Java 11 is not available. Install it with: brew install openjdk@11" >&2
  return 1 2>/dev/null || exit 1
fi

export PATH="$JAVA_HOME/bin:$PATH"
