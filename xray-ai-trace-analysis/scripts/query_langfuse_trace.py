#!/usr/bin/env python3
"""
Langfuse Trace Observation Query & Analysis Data Preparation Tool

Queries observations from Langfuse ClickHouse via the openapi endpoint,
saves raw data and builds an analysis prompt for LLM consumption.

Usage:
  # Save project_id for future use
  python3 query_langfuse_trace.py --save_project_id <id>

  # Generic query (default: last 1h, all fields, limit 10)
  python3 query_langfuse_trace.py --query '<JSON request body>'

  # Single trace (uses saved project_id)
  python3 query_langfuse_trace.py --trace_id <id>

  # Single trace with explicit project_id
  python3 query_langfuse_trace.py --project_id <id> --trace_id <id>

  # With time range
  python3 query_langfuse_trace.py --trace_id <id> \\
      --from "2025-04-01T00:00:00Z" --to "2025-04-07T23:59:59Z"

  # Compare two traces
  python3 query_langfuse_trace.py --trace_id <id_a> --trace_id_b <id_b>

  # Session analysis (default: last 1 day, max 20 traces)
  python3 query_langfuse_trace.py --session_id <session_id>

  # Session analysis with custom trace limit
  python3 query_langfuse_trace.py --session_id <session_id> --trace_limit 10
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ============================================================================
# Configuration
# ============================================================================
BASE_URL = "http://xray-ai.devops.xiaohongshu.com/open/skill/langfuse"
DEFAULT_LIMIT = 1000
DEFAULT_QUERY_LIMIT = 10   # Default limit for --query mode
DEFAULT_QUERY_HOURS = 1    # Default time range for query: last 1 hour
MAX_QUERY_DAYS = 7         # Max time span for --query mode
MAX_PROMPT_OBSERVATIONS = 500
TOP_LATENCY_COUNT = 100

# Session analysis defaults
SESSION_DEFAULT_DAYS = 1           # Default time range for session: last 1 day
SESSION_DEFAULT_TRACE_LIMIT = 20   # Default max traces per session
MAX_SESSION_OBSERVATIONS = 2000    # Total observation cap for session analysis
MAX_SESSION_PROMPT_PER_TRACE = 100 # Max observations per trace in session prompt

# Config file path (stored alongside the script)
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, ".langfuse_config.json")

# Output directory: <skill_dir>/tmp/
SKILL_DIR = os.path.dirname(CONFIG_DIR)  # scripts/ -> skill root
TMP_DIR = os.path.join(SKILL_DIR, "tmp")

# Fields to extract for prompt (excluding input, output, metadata)
KEY_FIELDS = [
    "id", "trace_id", "parent_observation_id", "type", "name",
    "start_time", "end_time", "completion_start_time",
    "level", "status_message",
    "provided_model_name", "model_parameters",
    "usage_details", "cost_details", "total_cost",
    "prompt_name", "prompt_version",
    "version", "environment",
]

# ============================================================================
# Project ID Persistence
# ============================================================================

def load_config():
    """Load saved configuration from disk."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config):
    """Save configuration to disk."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"WARNING: 无法保存配置文件: {e}", file=sys.stderr)


def get_project_id(args_project_id, args_save_project_id):
    """
    Resolve project_id with priority:
      1. --save_project_id (save and use)
      2. --project_id (use without saving)
      3. saved config (load from file)
    """
    config = load_config()

    # --save_project_id: save and use
    if args_save_project_id:
        config["project_id"] = args_save_project_id
        save_config(config)
        print(f"已保存 project_id: {args_save_project_id}", file=sys.stderr)
        return args_save_project_id

    # --project_id: use directly (also update saved config for convenience)
    if args_project_id:
        config["project_id"] = args_project_id
        save_config(config)
        return args_project_id

    # Load from saved config
    saved_id = config.get("project_id")
    if saved_id:
        print(f"使用已保存的 project_id: {saved_id}", file=sys.stderr)
        return saved_id

    return None


# ============================================================================
# API Client
# ============================================================================

def _api_request(project_id, body):
    """Send a POST request to the observation query API."""
    url = f"{BASE_URL}/{project_id}/observation/query"
    headers = {
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: HTTP {e.code} from API: {error_body}", file=sys.stderr)
        raise
    except URLError as e:
        print(f"ERROR: Cannot connect to {BASE_URL}: {e.reason}", file=sys.stderr)
        raise


def query_observations(project_id, trace_id, from_time, to_time):
    """Query observations for a given trace_id via the openapi endpoint."""
    body = {
        "from": from_time,
        "to": to_time,
        "filter": [{"column": "trace_id", "operator": "=", "value": trace_id}],
        "order_by": [{"column": "start_time", "order": "asc"}],
        "limit": DEFAULT_LIMIT,
    }
    return _api_request(project_id, body)


# ============================================================================
# Time Helpers
# ============================================================================

# Beijing timezone (UTC+8)
_TZ_BEIJING = timezone(timedelta(hours=8))


def _format_time_beijing(dt_str):
    """Convert a datetime string to Beijing time (UTC+8) for display."""
    dt = parse_datetime(dt_str)
    if dt is None:
        return dt_str or ""
    # Assume UTC if no tz info
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_TZ_BEIJING).strftime("%Y-%m-%d %H:%M:%S")


# ============================================================================
# Generic Query Mode
# ============================================================================

def compute_query_statistics(rows):
    """
    Compute summary statistics from raw query result rows.
    Adapts to whatever fields are present in the data.
    """
    if not rows:
        return {"total_rows": 0}

    stats = {"total_rows": len(rows)}

    # Detect available fields from the first row's keys (+ scan all for robustness)
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())

    # --- Type distribution ---
    if "type" in all_keys:
        type_dist = {}
        for r in rows:
            t = r.get("type", "UNKNOWN")
            type_dist[t] = type_dist.get(t, 0) + 1
        stats["type_distribution"] = type_dist

    # --- Level distribution ---
    if "level" in all_keys:
        level_dist = {}
        for r in rows:
            lv = r.get("level", "DEFAULT")
            level_dist[lv] = level_dist.get(lv, 0) + 1
        stats["level_distribution"] = level_dist

    # --- Cost ---
    if "total_cost" in all_keys:
        costs = []
        for r in rows:
            c = r.get("total_cost")
            if c is not None:
                try:
                    costs.append(float(c))
                except (ValueError, TypeError):
                    pass
        if costs:
            stats["cost"] = {
                "total": round(sum(costs), 8),
                "min": round(min(costs), 8),
                "max": round(max(costs), 8),
                "avg": round(sum(costs) / len(costs), 8),
            }

    # --- Model distribution ---
    if "provided_model_name" in all_keys:
        model_dist = {}
        for r in rows:
            m = r.get("provided_model_name")
            if m:
                model_dist[m] = model_dist.get(m, 0) + 1
        if model_dist:
            stats["model_distribution"] = model_dist

    # --- Trace count ---
    if "trace_id" in all_keys:
        trace_ids = set()
        for r in rows:
            tid = r.get("trace_id")
            if tid:
                trace_ids.add(tid)
        stats["distinct_trace_count"] = len(trace_ids)

    # --- Name distribution (top 10) ---
    if "name" in all_keys:
        name_dist = {}
        for r in rows:
            n = r.get("name")
            if n:
                name_dist[n] = name_dist.get(n, 0) + 1
        if name_dist:
            sorted_names = sorted(name_dist.items(), key=lambda x: x[1], reverse=True)
            stats["name_distribution_top10"] = dict(sorted_names[:10])

    # --- Time range in results ---
    if "start_time" in all_keys:
        times = []
        for r in rows:
            dt = parse_datetime(r.get("start_time"))
            if dt:
                times.append(dt)
        if times:
            stats["result_time_range"] = {
                "earliest": _format_time_beijing(min(times).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
                "latest": _format_time_beijing(max(times).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
            }

    return stats


def run_generic_query(project_id, query_body_json):
    """
    Execute a generic observation query.

    Args:
        project_id: Langfuse project ID
        query_body_json: JSON string of the request body

    Returns:
        Prints statistics to stdout, saves full results to observations.txt
    """
    now = datetime.now(timezone.utc)

    # Parse the JSON body
    try:
        body = json.loads(query_body_json)
    except json.JSONDecodeError as e:
        print(f"ERROR: --query 参数 JSON 解析失败: {e}")
        sys.exit(1)

    if not isinstance(body, dict):
        print("ERROR: --query 参数必须是一个 JSON 对象")
        sys.exit(1)

    # Apply defaults
    if "from" not in body:
        body["from"] = (now - timedelta(hours=DEFAULT_QUERY_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if "to" not in body:
        body["to"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    if "limit" not in body:
        body["limit"] = DEFAULT_QUERY_LIMIT

    # Validate time span: max 7 days
    from_dt = parse_datetime(body["from"])
    to_dt = parse_datetime(body["to"])
    if from_dt and to_dt:
        span = to_dt - from_dt
        if span.days > MAX_QUERY_DAYS:
            print(f"ERROR: 查询时间跨度 {span.days} 天超过上限 {MAX_QUERY_DAYS} 天，请缩小时间范围。")
            sys.exit(1)

    print(f"Querying observations (project={project_id}) ...", file=sys.stderr)
    print(f"  from={body['from']} to={body['to']} limit={body['limit']}", file=sys.stderr)

    result = _api_request(project_id, body)
    rows = result.get("data", [])
    meta = result.get("meta", {})

    if not rows:
        print(f"EMPTY: 在时间范围 [{body['from']}, {body['to']}] 内未查询到匹配数据。")
        sys.exit(1)

    # Save raw results to tmp/observations.json
    os.makedirs(TMP_DIR, exist_ok=True)
    output_file = os.path.join(TMP_DIR, "observations.json")
    file_data = {
        "query_time_ms": meta.get("query_time_ms"),
        "total_rows": len(rows),
        "time_range": {"from": body["from"], "to": body["to"]},
        "data": rows,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(file_data, f, ensure_ascii=False, indent=2)

    # Compute and output statistics
    stats = compute_query_statistics(rows)
    stats["query_time_ms"] = meta.get("query_time_ms", 0)
    stats["time_range"] = {"from": body["from"], "to": body["to"]}
    stats["output_file"] = os.path.abspath(output_file)

    output = {
        "status": "SUCCESS",
        "statistics": stats,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ============================================================================
# Session Analysis Mode
# ============================================================================

SESSION_PROMPT_TEMPLATE = """## 分析任务

请对以下 Langfuse Session 会话数据进行深入分析。该会话包含 {trace_count} 条 trace，共 {total_observations} 个 observation。

## 分析维度

### 会话级分析
1. **会话流程**：按时间线梳理用户的交互过程，每条 trace 做了什么、间隔多久
2. **性能趋势**：各 trace 的耗时变化，是否有逐渐变慢/波动异常
3. **成本趋势**：各 trace 的成本分布和累计成本
4. **错误分析**：哪些 trace 有错误，错误是否有聚集趋势
5. **模型使用**：各 trace 使用的模型是否一致，参数是否合理

### 单 trace 分析（对异常 trace 重点展开）
1. **调用链拓扑**：根据 id 和 parent_observation_id 重建调用树
2. **性能瓶颈**：耗时最长的步骤
3. **错误与异常**：ERROR/WARNING 节点的根因

### 综合建议
- 基于会话整体表现给出优化建议
- 识别系统性问题（如特定步骤在多条 trace 中都慢）

## 注意事项

- 完整原始数据（含 input/output）已保存在 tmp/langfuse_session.json，可通过 trace_id + observation id 查找详情
- 以下为提取的关键字段数据（不含 input/output/metadata），latency_ms 和 ttft_ms 为计算值

## Session 概览

{session_summary}

## Trace 时间线

{trace_timeline}

{filter_notice}

## 各 Trace 数据

{traces_data}
"""


def compute_session_summary(trace_summaries, session_id):
    """Compute session-level summary from per-trace summaries."""
    total_cost = 0
    total_observations = 0
    total_errors = 0
    total_warnings = 0
    total_input_tokens = 0
    total_output_tokens = 0
    all_models = set()
    durations = []

    for ts in trace_summaries:
        total_cost += ts["summary"].get("total_cost", 0)
        total_observations += ts["summary"].get("total_observations", 0)
        total_errors += ts["summary"].get("error_count", 0)
        total_warnings += ts["summary"].get("warning_count", 0)
        total_input_tokens += ts["summary"].get("total_input_tokens", 0)
        total_output_tokens += ts["summary"].get("total_output_tokens", 0)
        for m in ts["summary"].get("models_used", []):
            all_models.add(m)
        dur = ts["summary"].get("total_duration_ms")
        if dur is not None:
            durations.append(dur)

    # Session time span
    start_times = [ts["start_time"] for ts in trace_summaries if ts.get("start_time")]
    end_times = [ts["end_time"] for ts in trace_summaries if ts.get("end_time")]

    session_span_ms = None
    if start_times and end_times:
        earliest = min(parse_datetime(t) for t in start_times if parse_datetime(t))
        latest = max(parse_datetime(t) for t in end_times if parse_datetime(t))
        if earliest and latest:
            session_span_ms = round((latest - earliest).total_seconds() * 1000, 2)

    return {
        "session_id": session_id,
        "trace_count": len(trace_summaries),
        "total_observations": total_observations,
        "session_span_ms": session_span_ms,
        "total_cost": round(total_cost, 8),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "models_used": sorted(all_models),
        "avg_trace_duration_ms": round(sum(durations) / len(durations), 2) if durations else None,
        "max_trace_duration_ms": max(durations) if durations else None,
        "min_trace_duration_ms": min(durations) if durations else None,
    }


def build_trace_timeline(trace_summaries):
    """Build a textual timeline of traces in the session."""
    lines = []
    lines.append("| # | trace_id | name | 开始时间 (北京) | 耗时(ms) | 成本 | 错误 | 模型 |")
    lines.append("|---|----------|------|----------------|----------|------|------|------|")
    for i, ts in enumerate(trace_summaries, 1):
        tid = ts["trace_id"]
        name = ts.get("root_name", "-")
        start = _format_time_beijing(ts.get("start_time", ""))
        dur = ts["summary"].get("total_duration_ms", "-")
        cost = ts["summary"].get("total_cost", 0)
        errors = ts["summary"].get("error_count", 0)
        models = ", ".join(ts["summary"].get("models_used", [])) or "-"
        error_mark = f"**{errors}**" if errors > 0 else "0"
        lines.append(f"| {i} | `{tid}` | {name} | {start} | {dur} | {cost} | {error_mark} | {models} |")
    return "\n".join(lines)


def build_session_prompt(session_summary, trace_timeline, trace_details, filter_notice=""):
    """Build the session analysis prompt."""
    traces_data_parts = []
    for i, td in enumerate(trace_details, 1):
        part = f"### Trace {i}: {td['trace_id']}\n\n"
        part += f"**概览**: {json.dumps(td['summary'], ensure_ascii=False)}\n\n"
        part += f"```json\n{json.dumps(td['key_observations'], ensure_ascii=False, indent=2)}\n```\n"
        traces_data_parts.append(part)

    return SESSION_PROMPT_TEMPLATE.format(
        trace_count=session_summary["trace_count"],
        total_observations=session_summary["total_observations"],
        session_summary=json.dumps(session_summary, ensure_ascii=False, indent=2),
        trace_timeline=trace_timeline,
        filter_notice=filter_notice,
        traces_data="\n".join(traces_data_parts),
    )


def run_session_analysis(project_id, session_id, from_time, to_time, trace_limit):
    """
    Analyze a session by querying all traces and their observations.

    Steps:
      1. Query root spans (parent_observation_id IS NULL) for the session
      2. Batch query all observations for discovered trace_ids
      3. Group by trace_id, extract key fields, compute summaries
      4. Build session prompt and save files
    """
    print(f"Session analysis: session_id={session_id} (project={project_id})", file=sys.stderr)
    print(f"  from={from_time} to={to_time} trace_limit={trace_limit}", file=sys.stderr)

    # --- Step 1: Query root spans to discover trace_ids ---
    print("Step 1: Discovering trace_ids ...", file=sys.stderr)
    root_body = {
        "from": from_time,
        "to": to_time,
        "select": [
            "trace_id", "name", "start_time", "end_time",
            "level", "total_cost", "status_message",
        ],
        "filter": [
            {"column": "session_id", "operator": "=", "value": session_id},
            {"column": "parent_observation_id", "operator": "is null"},
        ],
        "order_by": [{"column": "start_time", "order": "asc"}],
        "limit": trace_limit,
    }
    root_result = _api_request(project_id, root_body)
    root_rows = root_result.get("data", [])

    if not root_rows:
        print(f"EMPTY: session_id={session_id} 在时间范围 [{from_time}, {to_time}] 内未找到任何 trace。")
        print("请确认：1) session_id 是否正确  2) 时间范围是否覆盖该会话")
        sys.exit(1)

    # Extract trace_ids and root span info
    trace_ids = []
    root_info = {}  # trace_id -> root span info
    for row in root_rows:
        tid = row.get("trace_id")
        if tid and tid not in root_info:
            trace_ids.append(tid)
            root_info[tid] = {
                "name": row.get("name", ""),
                "start_time": row.get("start_time", ""),
                "end_time": row.get("end_time", ""),
                "level": row.get("level", ""),
                "total_cost": row.get("total_cost"),
                "status_message": row.get("status_message", ""),
            }

    print(f"  Found {len(trace_ids)} traces", file=sys.stderr)

    # --- Step 2: Batch query all observations for these trace_ids ---
    print("Step 2: Querying observations for all traces ...", file=sys.stderr)
    obs_body = {
        "from": from_time,
        "to": to_time,
        "filter": [
            {"column": "trace_id", "operator": "in", "value": trace_ids},
        ],
        "order_by": [{"column": "start_time", "order": "asc"}],
        "limit": MAX_SESSION_OBSERVATIONS,
    }
    obs_result = _api_request(project_id, obs_body)
    all_observations = obs_result.get("data", [])
    obs_query_time = obs_result.get("meta", {}).get("query_time_ms", 0)

    print(f"  Fetched {len(all_observations)} observations", file=sys.stderr)

    # --- Step 3: Group by trace_id ---
    trace_groups = {}
    for obs in all_observations:
        tid = obs.get("trace_id")
        if tid:
            trace_groups.setdefault(tid, []).append(obs)

    # --- Step 4: Process each trace ---
    os.makedirs(TMP_DIR, exist_ok=True)
    trace_summaries = []  # For session summary and timeline
    trace_details = []    # For prompt (key observations)
    raw_session_data = [] # For raw data file

    total_filtered = False
    for tid in trace_ids:
        observations = trace_groups.get(tid, [])
        if not observations:
            continue

        # Extract key fields
        key_observations = [extract_key_fields(obs) for obs in observations]
        original_count = len(key_observations)

        # Filter if too many per trace
        if len(key_observations) > MAX_SESSION_PROMPT_PER_TRACE:
            key_observations, was_filtered = filter_observations_for_prompt(key_observations)
            if was_filtered:
                total_filtered = True
        else:
            was_filtered = False

        # Compute per-trace summary
        all_key_obs = [extract_key_fields(obs) for obs in observations]
        summary = compute_trace_summary(all_key_obs)

        ri = root_info.get(tid, {})
        trace_summaries.append({
            "trace_id": tid,
            "root_name": ri.get("name", ""),
            "start_time": ri.get("start_time", ""),
            "end_time": ri.get("end_time", ""),
            "summary": summary,
        })

        trace_details.append({
            "trace_id": tid,
            "summary": summary,
            "key_observations": key_observations,
            "original_count": original_count,
            "was_filtered": was_filtered,
        })

        raw_session_data.append({
            "trace_id": tid,
            "total_observations": len(observations),
            "observations": observations,
        })

    # --- Step 5: Build session summary ---
    session_summary = compute_session_summary(trace_summaries, session_id)
    trace_timeline = build_trace_timeline(trace_summaries)

    filter_notice = ""
    if total_filtered:
        filter_notice = (
            f"> **注意**：部分 trace 的 observation 数量超过 {MAX_SESSION_PROMPT_PER_TRACE} 条阈值，"
            f"已裁剪为 ERROR/WARNING 全保留 + 耗时 TOP {TOP_LATENCY_COUNT}。"
            f"完整数据请参阅 tmp/langfuse_session.json。"
        )

    # --- Step 6: Build prompt and save files ---
    prompt = build_session_prompt(session_summary, trace_timeline, trace_details, filter_notice)

    # Save raw data
    raw_file = os.path.join(TMP_DIR, "langfuse_session.json")
    raw_output = {
        "session_id": session_id,
        "trace_count": len(trace_ids),
        "total_observations": len(all_observations),
        "query_time_ms": obs_query_time,
        "time_range": {"from": from_time, "to": to_time},
        "traces": raw_session_data,
    }
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(raw_output, f, ensure_ascii=False, indent=2)

    # Save prompt
    prompt_file = os.path.join(TMP_DIR, "langfuse_session_prompt.txt")
    save_prompt(prompt_file, prompt)

    # Output success
    print(f"SUCCESS: 会话分析数据准备完成")
    print(f"  Session: {session_id}")
    print(f"  Traces: {len(trace_ids)} 条")
    print(f"  Observations: {len(all_observations)} 个")
    print(f"  时间范围: {from_time} ~ {to_time}")
    print(f"  总成本: {session_summary['total_cost']}")
    print(f"  总错误: {session_summary['total_errors']}")
    print(f"  原始数据: {os.path.abspath(raw_file)}")
    print(f"  分析提示: {os.path.abspath(prompt_file)}")


# ============================================================================
# Data Processing
# ============================================================================

def parse_datetime(dt_str):
    """Parse datetime string from ClickHouse response. Handles multiple formats."""
    if not dt_str:
        return None
    # Try ISO format with Z
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ]:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def compute_latency_ms(obs):
    """Compute latency in milliseconds from start_time and end_time."""
    start = parse_datetime(obs.get("start_time"))
    end = parse_datetime(obs.get("end_time"))
    if start and end:
        return round((end - start).total_seconds() * 1000, 2)
    return None


def compute_ttft_ms(obs):
    """Compute Time to First Token in milliseconds."""
    start = parse_datetime(obs.get("start_time"))
    comp = parse_datetime(obs.get("completion_start_time"))
    if start and comp:
        return round((comp - start).total_seconds() * 1000, 2)
    return None


def extract_key_fields(obs):
    """Extract key fields from an observation, adding computed metrics."""
    result = {}
    for field in KEY_FIELDS:
        val = obs.get(field)
        # Skip None/empty values to keep prompt compact
        if val is not None and val != "" and val != {} and val != []:
            result[field] = val

    # Add computed metrics
    latency = compute_latency_ms(obs)
    if latency is not None:
        result["latency_ms"] = latency

    ttft = compute_ttft_ms(obs)
    if ttft is not None:
        result["ttft_ms"] = ttft

    return result


def filter_observations_for_prompt(observations):
    """
    If observations > MAX_PROMPT_OBSERVATIONS, keep all error/warning spans
    plus top TOP_LATENCY_COUNT by latency. Returns (filtered_list, was_filtered).
    """
    if len(observations) <= MAX_PROMPT_OBSERVATIONS:
        return observations, False

    # Separate errors/warnings and normal observations
    errors = [o for o in observations if o.get("level") in ("ERROR", "WARNING")]
    normals = [o for o in observations if o.get("level") not in ("ERROR", "WARNING")]

    # Sort normals by latency descending
    normals.sort(key=lambda x: x.get("latency_ms") or 0, reverse=True)
    top_latency = normals[:TOP_LATENCY_COUNT]

    # Merge, deduplicate by id, sort by start_time
    seen_ids = set()
    merged = []
    for o in errors + top_latency:
        oid = o.get("id")
        if oid not in seen_ids:
            seen_ids.add(oid)
            merged.append(o)

    merged.sort(key=lambda x: x.get("start_time", ""))
    return merged, True


def compute_trace_summary(observations):
    """Compute summary statistics for a list of observations."""
    if not observations:
        return {}

    total_cost = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    error_count = 0
    warning_count = 0
    generation_count = 0
    span_count = 0
    models_used = set()
    max_latency_obs = None
    max_latency = 0

    for obs in observations:
        # Cost
        cost = obs.get("total_cost")
        if cost is not None:
            try:
                total_cost += float(cost)
            except (ValueError, TypeError):
                pass

        # Tokens
        usage = obs.get("usage_details") or {}
        if isinstance(usage, dict):
            for key in ("input", "promptTokens"):
                if key in usage:
                    try:
                        total_input_tokens += int(usage[key])
                    except (ValueError, TypeError):
                        pass
            for key in ("output", "completionTokens"):
                if key in usage:
                    try:
                        total_output_tokens += int(usage[key])
                    except (ValueError, TypeError):
                        pass
            for key in ("total", "totalTokens"):
                if key in usage:
                    try:
                        total_tokens += int(usage[key])
                    except (ValueError, TypeError):
                        pass

        # Level
        level = obs.get("level", "")
        if level == "ERROR":
            error_count += 1
        elif level == "WARNING":
            warning_count += 1

        # Type
        obs_type = obs.get("type", "")
        if obs_type == "GENERATION":
            generation_count += 1
        elif obs_type == "SPAN":
            span_count += 1

        # Model
        model = obs.get("provided_model_name")
        if model:
            models_used.add(model)

        # Max latency
        latency = obs.get("latency_ms") or 0
        if latency > max_latency:
            max_latency = latency
            max_latency_obs = obs

    # Total duration from first start to last end
    start_times = [parse_datetime(o.get("start_time")) for o in observations]
    end_times = [parse_datetime(o.get("end_time")) for o in observations]
    start_times = [t for t in start_times if t]
    end_times = [t for t in end_times if t]

    total_duration_ms = None
    if start_times and end_times:
        total_duration_ms = round(
            (max(end_times) - min(start_times)).total_seconds() * 1000, 2
        )

    return {
        "total_observations": len(observations),
        "generation_count": generation_count,
        "span_count": span_count,
        "total_duration_ms": total_duration_ms,
        "total_cost": round(total_cost, 8) if total_cost else 0,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "error_count": error_count,
        "warning_count": warning_count,
        "models_used": sorted(models_used),
        "slowest_step": {
            "name": max_latency_obs.get("name") if max_latency_obs else None,
            "latency_ms": max_latency,
        },
    }


# ============================================================================
# Prompt Builder
# ============================================================================

SINGLE_TRACE_PROMPT_TEMPLATE = """## 分析任务

请对以下 Langfuse Trace 链路数据进行深入分析。

## 分析维度

1. **调用链拓扑**：根据 id 和 parent_observation_id 重建父子调用树，以树状图展示完整调用链（含节点类型、模型名、耗时、成本），分析调用深度和扇出度
2. **性能瓶颈**：识别耗时最长的步骤（瓶颈 TOP N），计算 TTFT（首 Token 延迟），分析串行/并行关系，计算框架开销（父节点耗时 - 子节点耗时之和）
3. **Token 与成本**：各步骤的 token 消耗和成本分布，识别成本热点，分析 token 效率（output/input 比率）
4. **错误与异常**：检查 level=ERROR/WARNING 的节点，分析错误传播路径和根因
5. **模型使用**：各步骤使用的模型是否合理，参数设置是否恰当
6. **优化建议**：基于以上分析给出具体可操作的优化建议

## 注意事项

- 完整原始数据（含 input/output）已保存在 tmp/langfuse_trace.json，如需查看某个 observation 的详细输入输出内容，可通过 id 字段查找对应节点
- 以下为提取的关键字段数据（不含 input/output/metadata），latency_ms 和 ttft_ms 为计算值

## Trace 概览

{summary}

{filter_notice}

## Trace 数据: {trace_id}

```json
{observations_json}
```
"""

COMPARE_PROMPT_TEMPLATE = """## 分析任务

请对以下两条 Langfuse Trace 链路数据进行对比分析。

## 分析维度

### 单链路分析（分别对 Trace A 和 Trace B 进行）
1. **调用链拓扑**：根据 id 和 parent_observation_id 重建父子调用树，以树状图展示
2. **性能瓶颈**：识别耗时最长的步骤，计算 TTFT
3. **Token 与成本**：各步骤 token 消耗和成本分布
4. **错误与异常**：检查 ERROR/WARNING 节点

### 对比分析
1. **拓扑差异**：调用结构是否一致，是否有步骤增减
2. **性能差异**：各步骤耗时对比，瓶颈变化，整体耗时对比
3. **成本差异**：总成本对比，各步骤成本变化
4. **模型差异**：是否使用了不同模型或不同参数
5. **异常差异**：是否有一条成功另一条失败
6. **结论与建议**：差异的根本原因分析和具体优化建议

## 注意事项

- 完整原始数据（含 input/output）已保存在 tmp/langfuse_trace.json，如需查看详细输入输出可通过 id 字段查找对应节点
- 以下为提取的关键字段数据（不含 input/output/metadata）

## Trace A 概览

{summary_a}

{filter_notice_a}

## Trace A 数据: {trace_id_a}

```json
{observations_json_a}
```

## Trace B 概览

{summary_b}

{filter_notice_b}

## Trace B 数据: {trace_id_b}

```json
{observations_json_b}
```
"""


def build_filter_notice(was_filtered, original_count):
    if was_filtered:
        return (
            f"> **注意**：原始数据共 {original_count} 条 observation，超过 {MAX_PROMPT_OBSERVATIONS} 条阈值。"
            f"此处仅展示所有 ERROR/WARNING 节点 + 耗时 TOP {TOP_LATENCY_COUNT} 节点。"
            f"完整数据请参阅 tmp/langfuse_trace.json。"
        )
    return ""


def build_single_prompt(trace_id, key_observations, was_filtered, original_count, summary):
    """Build prompt for single trace analysis."""
    return SINGLE_TRACE_PROMPT_TEMPLATE.format(
        trace_id=trace_id,
        summary=json.dumps(summary, ensure_ascii=False, indent=2),
        filter_notice=build_filter_notice(was_filtered, original_count),
        observations_json=json.dumps(key_observations, ensure_ascii=False, indent=2),
    )


def build_compare_prompt(
    trace_id_a, key_obs_a, filtered_a, count_a, summary_a,
    trace_id_b, key_obs_b, filtered_b, count_b, summary_b,
):
    """Build prompt for two-trace comparison analysis."""
    return COMPARE_PROMPT_TEMPLATE.format(
        trace_id_a=trace_id_a,
        summary_a=json.dumps(summary_a, ensure_ascii=False, indent=2),
        filter_notice_a=build_filter_notice(filtered_a, count_a),
        observations_json_a=json.dumps(key_obs_a, ensure_ascii=False, indent=2),
        trace_id_b=trace_id_b,
        summary_b=json.dumps(summary_b, ensure_ascii=False, indent=2),
        filter_notice_b=build_filter_notice(filtered_b, count_b),
        observations_json_b=json.dumps(key_obs_b, ensure_ascii=False, indent=2),
    )


# ============================================================================
# File Output
# ============================================================================

def save_raw_data(filepath, trace_data_list):
    """Save raw observation data as structured JSON."""
    output = []
    for entry in trace_data_list:
        output.append({
            "trace_id": entry["trace_id"],
            "total_observations": len(entry["data"]),
            "query_time_ms": entry["query_time_ms"],
            "observations": entry["data"],
        })
    # Single trace: unwrap the array for simplicity
    data = output[0] if len(output) == 1 else output
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_prompt(filepath, prompt_content):
    """Save analysis prompt to file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(prompt_content)


# ============================================================================
# Main
# ============================================================================

def process_trace(project_id, trace_id, from_time, to_time):
    """Query and process a single trace. Returns (raw_data, key_observations, was_filtered, count, summary)."""
    result = query_observations(project_id, trace_id, from_time, to_time)
    observations = result.get("data", [])

    if not observations:
        return None, [], False, 0, {}

    raw_entry = {
        "trace_id": trace_id,
        "data": observations,
        "query_time_ms": result.get("meta", {}).get("query_time_ms", 0),
    }

    # Extract key fields
    key_observations = [extract_key_fields(obs) for obs in observations]
    original_count = len(key_observations)

    # Filter if too many
    key_observations, was_filtered = filter_observations_for_prompt(key_observations)

    # Compute summary from all key fields (before filtering)
    all_key_obs = [extract_key_fields(obs) for obs in observations]
    summary = compute_trace_summary(all_key_obs)

    return raw_entry, key_observations, was_filtered, original_count, summary


def main():
    parser = argparse.ArgumentParser(description="Langfuse Trace Analysis Tool")
    parser.add_argument("--project_id", help="Langfuse project ID (可选，优先使用已保存的)")
    parser.add_argument("--save_project_id", help="保存 project_id 供后续使用")
    # Generic query mode
    parser.add_argument("--query",
                        help="通用查询模式：传入 JSON 请求体，直接调用 observation query API")
    # Trace analysis mode
    parser.add_argument("--trace_id", help="Trace ID to analyze")
    parser.add_argument("--trace_id_b", help="Second trace ID for comparison")
    # Session analysis mode
    parser.add_argument("--session_id", help="Session ID to analyze (会话分析模式)")
    parser.add_argument("--trace_limit", type=int, default=SESSION_DEFAULT_TRACE_LIMIT,
                        help=f"Max traces to analyze in session mode (default: {SESSION_DEFAULT_TRACE_LIMIT})")
    # Common
    parser.add_argument("--from", dest="from_time", help="Start time (ISO 8601)")
    parser.add_argument("--to", dest="to_time", help="End time (ISO 8601)")
    args = parser.parse_args()

    # Resolve project_id
    project_id = get_project_id(args.project_id, args.save_project_id)

    # If only saving project_id (no trace_id, no query, no session_id), exit early
    if args.save_project_id and not args.trace_id and not args.query and not args.session_id:
        print(f"SUCCESS: project_id 已保存为 {args.save_project_id}")
        sys.exit(0)

    if not project_id:
        print("ERROR: 未提供 project_id，且无已保存的配置。请通过 --project_id 或 --save_project_id 指定。")
        sys.exit(1)

    # ---------------------------------------------------------------
    # Mode: generic query
    # ---------------------------------------------------------------
    if args.query:
        try:
            run_generic_query(project_id, args.query)
            sys.exit(0)
        except (HTTPError, URLError) as e:
            print(f"ERROR: API 请求失败 - {e}")
            sys.exit(2)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.exit(2)

    # ---------------------------------------------------------------
    # Mode: session analysis
    # ---------------------------------------------------------------
    if args.session_id:
        now = datetime.now(timezone.utc)
        if not args.from_time:
            args.from_time = (now - timedelta(days=SESSION_DEFAULT_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not args.to_time:
            args.to_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            run_session_analysis(
                project_id, args.session_id,
                args.from_time, args.to_time, args.trace_limit,
            )
            sys.exit(0)
        except (HTTPError, URLError) as e:
            print(f"ERROR: API 请求失败 - {e}")
            sys.exit(2)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.exit(2)

    # ---------------------------------------------------------------
    # Mode: trace analysis
    # ---------------------------------------------------------------
    if not args.trace_id:
        print("ERROR: 未提供操作模式。请使用 --query、--session_id 或 --trace_id 之一。")
        sys.exit(1)

    # Default time range: last 3 days
    now = datetime.now(timezone.utc)
    if not args.from_time:
        args.from_time = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not args.to_time:
        args.to_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    os.makedirs(TMP_DIR, exist_ok=True)
    raw_trace_file = os.path.join(TMP_DIR, "langfuse_trace.json")
    prompt_file = os.path.join(TMP_DIR, "langfuse_trace_prompt.txt")

    is_compare = bool(args.trace_id_b)

    try:
        # Process trace A
        print(f"Querying trace: {args.trace_id} (project: {project_id}) ...", file=sys.stderr)
        raw_a, key_obs_a, filtered_a, count_a, summary_a = process_trace(
            project_id, args.trace_id, args.from_time, args.to_time
        )

        if raw_a is None:
            print(f"EMPTY: trace_id={args.trace_id} 在时间范围 [{args.from_time}, {args.to_time}] 内未查询到任何 observation 数据。")
            print(f"请确认：1) project_id 是否正确  2) trace_id 是否正确  3) 时间范围是否覆盖该 trace 的执行时间")
            sys.exit(1)

        raw_entries = [raw_a]

        if is_compare:
            # Process trace B
            print(f"Querying trace: {args.trace_id_b} ...", file=sys.stderr)
            raw_b, key_obs_b, filtered_b, count_b, summary_b = process_trace(
                project_id, args.trace_id_b, args.from_time, args.to_time
            )

            if raw_b is None:
                print(f"EMPTY: trace_id_b={args.trace_id_b} 在时间范围 [{args.from_time}, {args.to_time}] 内未查询到任何 observation 数据。")
                print(f"请确认：1) project_id 是否正确  2) trace_id_b 是否正确  3) 时间范围是否覆盖该 trace 的执行时间")
                sys.exit(1)

            raw_entries.append(raw_b)

            # Build compare prompt
            prompt = build_compare_prompt(
                args.trace_id, key_obs_a, filtered_a, count_a, summary_a,
                args.trace_id_b, key_obs_b, filtered_b, count_b, summary_b,
            )
        else:
            # Build single prompt
            prompt = build_single_prompt(
                args.trace_id, key_obs_a, filtered_a, count_a, summary_a,
            )

        # Save files
        save_raw_data(raw_trace_file, raw_entries)
        save_prompt(prompt_file, prompt)

        # Output success
        mode = "对比分析" if is_compare else "单链路分析"
        trace_info = f"{args.trace_id}" + (f" vs {args.trace_id_b}" if is_compare else "")
        print(f"SUCCESS: {mode} 数据准备完成")
        print(f"  Trace: {trace_info}")
        print(f"  时间范围: {args.from_time} ~ {args.to_time}")
        print(f"  原始数据: {os.path.abspath(raw_trace_file)}")
        print(f"  分析提示: {os.path.abspath(prompt_file)}")
        if not is_compare:
            print(f"  观测数: {count_a} | 成本: {summary_a.get('total_cost', 0)} | "
                  f"错误: {summary_a.get('error_count', 0)} | "
                  f"总耗时: {summary_a.get('total_duration_ms', 'N/A')}ms")
        else:
            print(f"  Trace A 观测数: {count_a} | Trace B 观测数: {count_b}")

    except (HTTPError, URLError) as e:
        print(f"ERROR: API 请求失败 - {e}")
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
