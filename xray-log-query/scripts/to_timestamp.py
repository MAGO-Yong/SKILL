#!/usr/bin/env python3
"""
通用 datetime → Unix 秒时间戳转换工具

支持多种输入格式，时区以当前机器本地时区为准。

支持的输入格式：
  1. Unix 秒时间戳（直接透传）     1700000000
  2. Unix 毫秒时间戳（自动识别）   1700000000000
  3. 日期时间字符串（多种格式）    "2024-03-25 14:00:00"
                                   "2024-03-25T14:00:00"
                                   "2024-03-25 14:00"
                                   "2024-03-25"
  4. 相对时间表达式                "now"
                                   "now-1h" / "now-30m" / "now-2d"
                                   "now+1h"

用法示例:
  # 查看当前时间戳
  python3 to_timestamp.py --time now

  # 日期字符串转时间戳
  python3 to_timestamp.py --time "2024-03-25 14:00:00"

  # 相对时间
  python3 to_timestamp.py --time "now-1h"

  # 时间范围字符串（用 " - " 或 "~" 分隔，两端可以是任意支持的格式）
  python3 to_timestamp.py --range "2024-03-25 14:00:00 - 2024-03-25 15:10:10"
  python3 to_timestamp.py --range "2024-03-25 14:00 ~ 2024-03-25 15:10"
  python3 to_timestamp.py --range "now-1h - now"

  # 分别指定开始和结束时间
  python3 to_timestamp.py --start "2024-03-25 10:00" --end "2024-03-25 11:00"
  python3 to_timestamp.py --start "now-1h" --end "now"
"""

import argparse
import re
import sys
import time
from datetime import datetime


# 支持的 datetime 格式列表（按优先级顺序尝试）
_DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
    "%Y%m%d%H%M%S",
    "%Y%m%d",
]

# 相对时间表达式：now[+-]<number><unit>
_RELATIVE_PATTERN = re.compile(
    r"^now\s*([+-])\s*(\d+)\s*(s|sec|m|min|h|hour|d|day)s?$",
    re.IGNORECASE,
)

_UNIT_SECONDS = {
    "s": 1,
    "sec": 1,
    "m": 60,
    "min": 60,
    "h": 3600,
    "hour": 3600,
    "d": 86400,
    "day": 86400,
}

# 时间范围分隔符：" - "、" ~ "、" to "（大小写不限），两侧允许有空格
# 注意：分隔符两侧必须有空白，避免误匹配 "now-1h" 中的 "-"
_RANGE_SEP = re.compile(r"\s+[-~]\s+|\s+to\s+", re.IGNORECASE)


def parse_range(text: str):
    """
    解析 "T1 - T2" / "T1 ~ T2" / "T1 to T2" 格式的时间范围字符串。

    Args:
        text: 时间范围字符串，如 "2024-03-25 14:00:00 - 2024-03-25 15:10:10"

    Returns:
        (start_ts, end_ts) 均为 Unix 秒（int）

    Raises:
        ValueError: 无法识别分隔符或任一端无法解析
    """
    parts = _RANGE_SEP.split(text.strip(), maxsplit=1)
    if len(parts) != 2:
        raise ValueError(
            f"无法从 {text!r} 中识别时间范围分隔符。\n"
            '支持的分隔符：" - "、" ~ "、" to "（两侧需有空格）\n'
            '示例："2024-03-25 14:00:00 - 2024-03-25 15:10:10"'
        )
    start_str, end_str = parts[0].strip(), parts[1].strip()
    start_ts = to_unix_seconds(start_str)
    end_ts = to_unix_seconds(end_str)
    return start_ts, end_ts


def _parse_relative(text: str) -> int:
    """解析相对时间表达式，返回 Unix 秒。"""
    m = _RELATIVE_PATTERN.match(text.strip())
    if not m:
        return None
    sign, amount, unit = m.group(1), int(m.group(2)), m.group(3).lower()
    delta = amount * _UNIT_SECONDS[unit]
    now = int(time.time())
    return now + delta if sign == "+" else now - delta


def _parse_unix_ts(text: str) -> int:
    """
    判断字符串是否为纯数字时间戳，返回秒级值；
    毫秒时间戳（13 位）自动除以 1000。
    """
    text = text.strip()
    if not re.fullmatch(r"\d+", text):
        return None
    ts = int(text)
    # 13 位及以上认为是毫秒时间戳
    if ts > 9_999_999_999:
        ts = ts // 1000
    return ts


def _parse_datetime_str(text: str) -> int:
    """逐一尝试已知格式解析 datetime 字符串，返回 Unix 秒（本地时区）。"""
    text = text.strip()
    for fmt in _DATETIME_FORMATS:
        try:
            dt = datetime.strptime(text, fmt)
            # 使用本地时区（mktime 会自动应用本地时区）
            return int(time.mktime(dt.timetuple()))
        except ValueError:
            continue
    return None


def to_unix_seconds(text: str) -> int:
    """
    将任意时间表示转换为 Unix 秒时间戳（本地时区）。

    Args:
        text: 时间字符串，支持：
              - "now"
              - 相对表达式："now-1h", "now+30m", "now-2d"
              - Unix 秒时间戳：1700000000
              - Unix 毫秒时间戳：1700000000000（自动识别）
              - 日期时间字符串："2024-03-25 14:00:00" 等多种格式

    Returns:
        Unix 秒时间戳（int）

    Raises:
        ValueError: 无法识别的格式
    """
    text = text.strip()

    # 1. "now"
    if text.lower() == "now":
        return int(time.time())

    # 2. 相对表达式
    result = _parse_relative(text)
    if result is not None:
        return result

    # 3. 纯数字时间戳（秒或毫秒）
    result = _parse_unix_ts(text)
    if result is not None:
        return result

    # 4. datetime 字符串
    result = _parse_datetime_str(text)
    if result is not None:
        return result

    raise ValueError(
        f"无法识别的时间格式: {text!r}\n"
        "支持：now / now-1h / now+30m / 1700000000 / 1700000000000 / "
        '"2024-03-25 14:00:00" 等'
    )


def _format_local(ts: int) -> str:
    """将 Unix 秒格式化为本地时间字符串，方便人工确认。"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def _print_range(start_str: str, end_str: str, start_ts: int, end_ts: int):
    """统一输出时间范围结果。输出的时间戳单位为秒（s），不是毫秒（ms）。"""
    if end_ts <= start_ts:
        print(
            f"[WARN] 结束时间 ({end_ts}s) 不晚于开始时间 ({start_ts}s)，请检查输入",
            file=sys.stderr,
        )
    print(
        f"start  : {start_str}  →  {_format_local(start_ts)}  →  {start_ts}  [单位: 秒(s), 非毫秒]"
    )
    print(f"end    : {end_str}  →  {_format_local(end_ts)}  →  {end_ts}  [单位: 秒(s), 非毫秒]")


def main():
    parser = argparse.ArgumentParser(
        description="将各种 datetime 格式转换为 Unix 秒时间戳（时区：本机本地时区）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 to_timestamp.py --time now
  python3 to_timestamp.py --time "now-1h"
  python3 to_timestamp.py --time "2024-03-25 14:00:00"
  python3 to_timestamp.py --time 1700000000000
  python3 to_timestamp.py --range "2024-03-25 14:00:00 - 2024-03-25 15:10:10"
  python3 to_timestamp.py --range "2024-03-25 14:00 ~ 2024-03-25 15:10"
  python3 to_timestamp.py --range "now-1h - now"
  python3 to_timestamp.py --start "2024-03-25 10:00" --end "2024-03-25 11:00"
  python3 to_timestamp.py --start "now-1h" --end "now"
""",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--time",
        metavar="TIME",
        help="单个时间表达式，输出对应的 Unix 秒时间戳",
    )
    group.add_argument(
        "--range",
        metavar="RANGE",
        help=(
            '时间范围字符串，用 " - "、" ~ " 或 " to " 分隔（两侧需有空格）。'
            '示例："2024-03-25 14:00:00 - 2024-03-25 15:10:10"'
        ),
    )
    group.add_argument(
        "--start",
        metavar="START",
        help="与 --end 配合使用，同时输出开始和结束的 Unix 秒时间戳",
    )
    parser.add_argument(
        "--end",
        metavar="END",
        help="与 --start 配合使用，同时输出开始和结束的 Unix 秒时间戳",
    )
    args = parser.parse_args()

    # 单值模式
    if args.time is not None:
        try:
            ts = to_unix_seconds(args.time)
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        print(f"input  : {args.time}")
        print(f"local  : {_format_local(ts)}")
        print(f"unix_s : {ts}  [单位: 秒(s), 非毫秒]")
        return

    # 范围字符串模式（--range）
    if args.range is not None:
        try:
            start_ts, end_ts = parse_range(args.range)
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        # 从原始字符串中还原两端用于展示
        parts = _RANGE_SEP.split(args.range.strip(), maxsplit=1)
        start_str, end_str = parts[0].strip(), parts[1].strip()
        _print_range(start_str, end_str, start_ts, end_ts)
        return

    # 双值模式（--start + --end）
    if args.start is None or args.end is None:
        parser.error("--start 和 --end 必须同时提供")

    errors = []
    start_ts = end_ts = None
    try:
        start_ts = to_unix_seconds(args.start)
    except ValueError as e:
        errors.append(f"--start: {e}")
    try:
        end_ts = to_unix_seconds(args.end)
    except ValueError as e:
        errors.append(f"--end: {e}")

    if errors:
        for err in errors:
            print(f"[ERROR] {err}", file=sys.stderr)
        sys.exit(1)

    _print_range(args.start, args.end, start_ts, end_ts)


if __name__ == "__main__":
    main()
