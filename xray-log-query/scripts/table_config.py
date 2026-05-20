#!/usr/bin/env python3
"""
Xray 日志查询 - 表配置注册中心

新增一张表只需在 TABLE_CONFIGS 中添加一个 key，无需修改任何脚本逻辑。

每条 nl_field_rules 条目结构：
  {
      "field":       str,   # 目标字段名（Lucene 字段）
      "patterns":    list,  # 正则列表，任一命中即提取
      "value_group": int,   # 从哪个捕获组取值，默认 1
      "op":          str,   # 操作符，默认 ":"（精确），也支持":>" ":>=" 等
      "quote":       bool,  # 值是否加双引号，默认 False
      "set_search_trace_app": bool,  # （可选）命中时自动设置 searchTraceApp=True，默认 False
      "value_map":           dict,   # （可选）捕获值到最终值的映射表（如中英文同义词），默认不做映射
  }

环境配置说明：
  - prod：生产环境，支持所有日志表（application / rgw / flink / larc / event / audit / edith / pv / measurement）
  - beta：测试环境，仅支持 application 表
"""

import copy

# ── 环境配置 ──────────────────────────────────────────────────────────────────

ENV_CONFIGS = {
    "prod": {
        "base_url_prefix": "https://xray-ai.devops.xiaohongshu.com/open/skill/log/api/v1/tables",
        "supported_tables": None,  # None 表示所有表都支持
        "description": "生产环境，支持所有日志表",
    },
    "beta": {
        "base_url_prefix": "https://xray-ai.devops.beta.xiaohongshu.com/open/skill/log/api/v1/tables",
        "supported_tables": ["application"],  # beta 环境只支持 application 表
        "description": "测试环境，仅支持 application 表",
    },
}

VALID_ENVS = list(ENV_CONFIGS.keys())
DEFAULT_ENV = "prod"


def get_env_config(env: str) -> dict:
    """
    获取环境配置。

    Args:
        env: 环境名，如 "prod"、"beta"

    Returns:
        环境配置 dict

    Raises:
        ValueError: 未知的环境名
    """
    if env not in ENV_CONFIGS:
        supported = ", ".join(VALID_ENVS)
        raise ValueError(f"不支持的环境：'{env}'。当前支持的环境：{supported}")
    return copy.deepcopy(ENV_CONFIGS[env])


def get_base_url(env: str, endpoint: str) -> str:
    """
    根据环境和接口路径，构建完整的 API URL。

    Args:
        env:      环境名，如 "prod"、"beta"
        endpoint: 接口端点，如 "logs"、"charts"、"cluster-logs"

    Returns:
        完整 API URL
    """
    env_cfg = get_env_config(env)
    return f"{env_cfg['base_url_prefix']}/{endpoint}"


def validate_env_table(env: str, table: str) -> tuple:
    """
    校验环境和表名的组合是否合法。

    Args:
        env:   环境名
        table: 表名

    Returns:
        (is_valid, error_message)
        is_valid: True 表示合法
        error_message: 失败时的错误说明（合法时为 None）
    """
    try:
        env_cfg = get_env_config(env)
    except ValueError as e:
        return False, str(e)

    supported_tables = env_cfg["supported_tables"]
    if supported_tables is not None and table not in supported_tables:
        return (
            False,
            f"beta 环境仅支持 application 表，不支持 '{table}' 表。"
            f"如需查询其他日志表，请切换到 prod 环境（去掉 --env beta 参数或改为 --env prod）",
        )

    return True, None


TABLE_CONFIGS = {
    "application": {
        "table": "application",
        "cluster_supported": True,
        # API 校验层字段（query 中必须含其一）；nl_field_rules 仅覆盖 NL 能识别的子集，两层职责不同
        "required_fields": [
            "subApplication",
            "xrayTraceId",
            "_pod_name_",
            "traceId",
            "ID",
            "catMsgId",
            "catRootId",
            "userId",
            "ext.uid",  # nl_field_rules 中 userId 对应的实际字段名
        ],
        "common_fields": ["subApplication", "level"],
        "display_fields": [
            "_time_second_",
            "level",
            "msg",
            "subApplication",
            "xrayTraceId",
            "_pod_name_",
        ],
        "nl_field_rules": [
            {
                "field": "xrayTraceId",
                "patterns": [
                    r"(?:xrayTraceId|traceId|trace[_\s]?id)\s*[=:]\s*([0-9a-fA-F]{32})",
                    r"\b([0-9a-fA-F]{32})\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
                "set_search_trace_app": True,
            },
            {
                "field": "subApplication",
                "patterns": [
                    r"(?:subApplication|app)\s*[=:]\s*([\w\-\.]+)",
                    r"([\w][\w\-\.]*[\w])\s*(?:服务|service)",
                    r"(?:^|[\s，,。！!？?])([\w][\w]*[-\.][\w][\w\-\.]*)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "level",
                "patterns": [
                    r"\b(error|错误|err)\b",
                    r"\b(warn|warning|告警)\b",
                    r"\b(info|信息)\b",
                    r"\b(debug|调试)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
                "value_map": {
                    "错误": "error",
                    "err": "error",
                    "warning": "warn",
                    "告警": "warn",
                    "信息": "info",
                    "调试": "debug",
                },
            },
            {
                "field": "_pod_name_",
                "patterns": [
                    r"(?:pod|_pod_name_)\s*[=:]?\s*([\w\-]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "ext.uid",
                "patterns": [
                    r"(?:userId|uid|用户[Ii][Dd]?)\s*[=:]\s*(\d+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "catMsgId",
                "patterns": [
                    r"(?:catMsgId|cat\s*message\s*id|cat\s*msg\s*id)\s*[=:]?\s*([\w\-\.]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
            {
                "field": "ext.caller",
                "patterns": [
                    r"(?:ext\.caller|caller|接口名|接口)\s*[=:]?\s*([\w\-\.]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
            {
                "field": "ext.xrayEntry",
                "patterns": [
                    r"(?:ext\.xrayEntry|xrayEntry|入口\s*[Uu][Rr][Ll]|入口路径)\s*[=:]?\s*[\"']?([^\s\"'，,]+)[\"']?",
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
            {
                "field": "stack_trace",
                "patterns": [
                    r"(?:stack_trace|异常|exception|报错|堆栈)\s*[=:]?\s*[\"']?([^\s\"'，,]+)[\"']?",
                    r"\b([a-zA-Z][a-zA-Z0-9]*(?:\.[a-zA-Z][a-zA-Z0-9]*)*Exception)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
            {
                "field": "_region_",
                "patterns": [
                    r"(?:地域|region|_region_)\s*[=:]?\s*([\w\-]+)",
                    r"\b(qc-sh|qc-nj|al-sh|al-hz)\b",
                    r"(腾讯上海|腾讯南京|阿里上海|阿里杭州|自建机房)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
                "value_map": {
                    "腾讯上海": "qc-sh",
                    "腾讯南京": "qc-nj",
                    "阿里上海": "al-sh",
                    "阿里杭州": "al-hz",
                    "自建机房": "al-sh",
                },
            },
            {
                "field": "_k8s_",
                "patterns": [
                    r"(?:部署区|_k8s_|k8s)\s*[=:]?\s*([\w\-]+)",
                    r"\b(qcsh\d+-\d+|alsh\d+-\d+|qcnj\d+-\d+)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "msg",
                "patterns": [
                    r'(?:关键词|keyword|包含|msg|message)\s*[=:]?\s*["\']?([^\s"\'，,]+)["\']?',
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
        ],
    },
    "rgw": {
        "table": "rgw",
        "cluster_supported": False,
        "required_fields": [],
        "common_fields": ["subApplication", "http_host"],
        "display_fields": None,
        "nl_field_rules": [
            {
                "field": "http_host",
                "patterns": [
                    r"(?:域名|host|http_host)\s*[=:]?\s*([\w\-\.]+\.(?:com|cn|net|io)[\w\-\.]*)",
                    r"\b([\w\-]+\.xiaohongshu\.com)\b",
                    r"\b([\w\-]+\.xhs\.cn)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "subApplication",
                "patterns": [
                    r"(?:subApplication|app)\s*[=:]\s*([\w\-\.]+)",
                    r"([\w][\w\-\.]*[\w])\s*(?:服务|service)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "request_uri",
                "patterns": [
                    r"(?:接口|路径|uri|request_uri|path)\s*[=:]?\s*(/[\w\-/\.]+)",
                    r"(/api/[\w\-/\.]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
            {
                "field": "request_method",
                "patterns": [
                    r"\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "response_status",
                "patterns": [
                    r"(?:状态码|status|response_status|http\s*status)\s*[=:]?\s*([45]\d{2})",
                    r"\b(5\d{2}|4\d{2})\s*(?:错误|error|报错)?(?=\b)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "clientIP",
                "patterns": [
                    r"(?:clientIP|客户端\s*IP|client\s*ip)\s*[=:]?\s*(\d{1,3}(?:\.\d{1,3}){3})",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "x-xray-traceid",
                "patterns": [
                    r"(?:xray[-_]?traceid|x-xray-traceid)\s*[=:]?\s*([0-9a-fA-F]{32})",
                    r"\b([0-9a-fA-F]{32})\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "request_time",
                "patterns": [
                    r"(?:耗时|request_time|慢请求|响应时间)\s*(?:大于|超过|>)\s*(\d+(?:\.\d+)?)\s*s",
                    r"(?:slower\s+than|latency\s*>)\s*(\d+(?:\.\d+)?)",
                ],
                "value_group": 1,
                "op": ":>",
                "quote": False,
            },
        ],
    },
    "flink": {
        "table": "flink",
        "cluster_supported": False,
        "required_fields": ["release"],
        "common_fields": ["release", "component"],
        "display_fields": [
            "_time_second_",
            "release",
            "component",
            "msg",
            "_pod_name_",
        ],
        "nl_field_rules": [
            {
                "field": "release",
                "patterns": [
                    # 显式写法：release=xxx / job=xxx / 任务=xxx
                    r"(?:release|job|任务)\s*[=:]?\s*((?:baichuan|bc)-[a-z0-9]+(?:-[a-z0-9]+)*)",
                    # 裸任务名：baichuan-xxx 或 bc-xxx 格式，用 ASCII 边界避免匹配中文前缀
                    r"(?<![a-zA-Z0-9\-])((?:baichuan|bc)-[a-z0-9]+(?:-[a-z0-9]+)*)(?![a-zA-Z0-9\-])",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "component",
                "patterns": [
                    r"\b(jobmanager|taskmanager)\b",
                    r"(?:component)\s*[=:]\s*([\w\-]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "_pod_name_",
                "patterns": [
                    r"(?:pod|_pod_name_)\s*[=:]?\s*([\w\-]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "msg",
                "patterns": [
                    r'(?:关键词|keyword|包含|msg|message)\s*[=:]?\s*["\'\']?([^\s"\'\'，,]+)["\'\']?',
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
        ],
    },
    "larc": {
        "table": "larc",
        "cluster_supported": False,
        "required_fields": ["subApplication"],
        "common_fields": ["subApplication"],
        "display_fields": [
            "_time_second_",
            "subApplication",
            "log",
            "_pod_name_",
            "_namespace_",
        ],
        "nl_field_rules": [
            {
                "field": "subApplication",
                "patterns": [
                    # 显式写法：subApplication=xxx / app=xxx / 任务=xxx
                    r"(?:subApplication|app|任务)\s*[=:]\s*([a-z]+-\d+-[a-z0-9]+-\d+)",
                    # 裸任务名：精确匹配 word-digits-word-digits 四段格式（如 main-934050079-g7o-96）
                    # 用 ASCII 边界防止误匹配中文前后缀
                    r"(?<![a-zA-Z0-9\-])([a-z]+-\d+-[a-z0-9]+-\d+)(?![a-zA-Z0-9\-])",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "_pod_name_",
                "patterns": [
                    r"(?:pod|_pod_name_)\s*[=:]?\s*([\w\-]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "_namespace_",
                "patterns": [
                    r"(?:namespace|_namespace_|命名空间)\s*[=:]?\s*([\w\-]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "log",
                "patterns": [
                    r'(?:关键词|keyword|包含|log|日志内容)\s*[=:]?\s*["\'\']?([^\s"\'\'，,]+)["\'\']?',
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
        ],
    },
    "event": {
        "table": "event",
        "cluster_supported": False,
        "required_fields": ["cluster"],
        "common_fields": ["cluster", "level"],
        "display_fields": [
            "_time_second_",
            "cluster",
            "level",
            "reason",
            "msg",
            "name",
            "namespace",
            "kind",
            "component",
        ],
        "nl_field_rules": [
            {
                "field": "cluster",
                "patterns": [
                    # 显式写法：cluster=xxx / 集群 xxx
                    r"(?:cluster|集群)\s*[=:]\s*([\w][\w\-]*[\w])",
                    # 枚举匹配：直接识别已知集群名
                    r"(?<![a-zA-Z0-9\-])(alsh\-offline\-training\-3|ali\-offline\-training\-2|qcsh8\-redis\-mixlarge\-1|rcsh1\-redoss\-preonline|qcnj2\-redis\-mixlarge\-1|alihz\-redis\-mixlarge\-1|qcsh5\-flink\-feature\-1|alsh1\-flink\-feature\-1|qcsh8\-flink\-feature\-1|alsh1\-rdma\-gpu\-prod|qcsh5\-istio\-staging|kubeservicemeshsit|alsh1\-istio\-master|ali\-offline\-train|qcsh\-redgraph\-sit|alsh1\-spark\-shequ|qcrdma\-aiplatform|qcsh4\-istio\-slave|qcsh8\-redis\-test|qcsh4\-database\-2|qchpc\-aiplatform|alsh1\-spark\-gray|alsh1\-spark\-data|mesh\-sh4\-staging|qcsh4\-redfaasprd|alsh1\-gpu\-gray\-1|rcsh\-spark\-shequ|rcsh1\-redindex\-1|alsh1\-flink\-gray|alsh1\-istio\-gray|qcsh5\-aiplatform|qcsh\-redtable\-1|ID_cls\-1nqvxujd|alsh\-redtable\-1|alsh1\-spark\-ads|ID_cls\-9gm2i653|ID_cls\-e6wai3a7|ID_cls\-ke3q1ye4|ID_cls\-6q1dku54|qcsh4\-redkv8\-1|qcsh5\-ray\-gray|qcsh4\-database|qcsh5\-gpu\-rdma|qcnj1\-database|qcsh8\-redhub\-1|qcsh4\-redis8\-1|rcsh1\-redoss\-2|rcsh\-spark\-rss|alsh1\-database|rcsh1\-redoss\-3|qcsh5\-database|qcsh4\-dedicate|rcsh1\-redoss\-4|qcsh8\-flink\-2|qcsh\-redtao\-1|qcsh8\-flink\-3|alsh1\-flink\-2|qcsh8\-redis\-1|qcsh5\-airflow|qcsh5\-flink\-3|isito\-sh4\-sit|qcsh3\-tools\-2|qcsh5\-flink\-2|alish\-redis\-5|alihz\-redis\-5|qcsh8\-kafka\-1|alish\-redis\-4|qcsh5\-redis\-a|rcsh1\-infra\-1|alsh1\-redkv\-3|alsh1\-reddb\-1|alish\-redis\-3|qcsh8\-redis\-2|alihz\-redis\-6|alhz\-database|alihz\-istio\-2|alsh1\-redkv\-2|qcsh5\-gpu\-ray|alsh1\-redkv\-4|qcsh\-redkv\-1|qcsh4\-secwxb|alhz\-redkv\-1|alsh\-fluss\-1|qcnj\-redis\-4|qcnj\-istio\-2|qcnj\-kafka\-1|rcsh1\-redoss|qcnj\-redis\-5|qcnj\-redis\-6|qcsh4\-lambda|qcsh\-flink\-1|qcsh4\-istio|qcsh8\-infra|alsh1\-ray\-3|qcsh4\-redkv|alsh2\-redis|qcnj2\-redkv|qcsh8\-dts\-1|alsh1\-infra|alsh1\-redkv|qcsh5\-istio|qcsh5\-flink|alhz1\-infra|alsh1\-spark|qcsh5\-redis|qcsh5\-redkv|alhz2\-redis|alhz1\-redis|rsi\-fed\-gpu|rcsh1\-redkv|alihz\-istio|rcjp\-redoss|qcsh4\-flink|qcsh3\-tools|qcnj2\-infra|alsh1\-ray\-2|alsh\-olap\-1|alsh1\-istio|alsh1\-dts\-1|rcsh1\-redis|qcnj2\-xray|alhz\-dts\-1|qcsh4\-xray|qcsh5\-olap|qcsh5\-meta|qcnj2\-eaas|qcsh5\-xray|rcsh\-lve\-1|alsh1\-gray|alhz1\-xray|alsh1\-meta|qcsh8\-olap|alsh1\-eaas|qcnj\-istio|qcnj\-gpu\-1|redisqcnj3|qcnj2\-meta|qcsh4\-mesh|rcsh1\-gray|fed\-qcsh4|qcbj1\-prd|qcsh5\-agi|rsi\-alhz1|rcsh1\-gpu|ali\-flink|alsh1\-gpu|alhz1\-new|qcsh4\-dts|qcsh5\-gpu|qcsh5\-new|rsi\-qcsh4|rsi\-rcsh1|rsi\-qcnj2|alsh1\-mix|rcsh1\-mix|rsi\-alsh1|rsi\-qcsh5|fed\-qcsh5|qcsh4\-new|alsh1\-ray|alsh1\-asl|qcsh\-sit|rcjp\-gpu|qcsh4new|alsh1\-it|sit\-faas|qcsh5\-3|alsh1\-5|qcsh4\-4|qcnj2\-6|alsh1\-6|qcsh5\-2|qcnj2\-4|rcsh1\-6|qcnj2\-2|qcnj2\-3|rcsh1\-5|qcnj2\-5|alsh1\-8|rcsh1\-3|alsh1\-7|rcsh1\-7|qcsh4\-3|alsh1\-2|qcsh4\-2|rcsh1\-2|alhz1\-5|kubeqa|qcsh4f|qcsh4e|qcsh4d|qcsh5|alhz1|qcsh4|qcnj1|rcsh1)(?![a-zA-Z0-9\-])",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "level",
                "patterns": [
                    r"\b(Warning|warning|告警|警告)\b",
                    r"\b(Normal|normal|正常)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
                "value_map": {
                    "warning": "Warning",
                    "告警": "Warning",
                    "警告": "Warning",
                    "normal": "Normal",
                    "正常": "Normal",
                },
            },
            {
                "field": "namespace",
                "patterns": [
                    r"(?:namespace|命名空间)\s*[=:]?\s*([\w\-]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "kind",
                "patterns": [
                    r"\b(Pod|Node|Deployment|StatefulSet|DaemonSet|ReplicaSet|Service|ConfigMap)\b",
                    r"(?:kind)\s*[=:]\s*([\w]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "reason",
                "patterns": [
                    r"(?:reason|原因)\s*[=:]?\s*([\w]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "component",
                "patterns": [
                    r"(?:component)\s*[=:]\s*([\w\-]+)",
                    r"\b(kubelet|kube-scheduler|kube-controller-manager)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
        ],
    },
    "audit": {
        "table": "audit",
        "cluster_supported": False,
        "required_fields": ["cluster"],
        "common_fields": ["cluster", "user.username"],
        "display_fields": [
            "_time_second_",
            "cluster",
            "user.username",
            "verb",
            "requestURI",
            "objectRef.resource",
            "responseStatus.code",
            "auditID",
        ],
        "nl_field_rules": [
            {
                "field": "cluster",
                "patterns": [
                    # 显式写法：cluster=xxx / 集群 xxx
                    r"(?:cluster|集群)\s*[=:]\s*([\w][\w\-]*[\w])",
                    # 枚举匹配：直接识别已知集群名
                    r"(?<![a-zA-Z0-9\-])(alsh\-offline\-training\-3|ali\-offline\-training\-2|qcsh8\-redis\-mixlarge\-1|rcsh1\-redoss\-preonline|qcnj2\-redis\-mixlarge\-1|alihz\-redis\-mixlarge\-1|qcsh5\-flink\-feature\-1|alsh1\-flink\-feature\-1|qcsh8\-flink\-feature\-1|alsh1\-rdma\-gpu\-prod|qcsh5\-istio\-staging|kubeservicemeshsit|alsh1\-istio\-master|ali\-offline\-train|qcsh\-redgraph\-sit|alsh1\-spark\-shequ|qcrdma\-aiplatform|qcsh4\-istio\-slave|qcsh8\-redis\-test|qcsh4\-database\-2|qchpc\-aiplatform|alsh1\-spark\-gray|alsh1\-spark\-data|mesh\-sh4\-staging|qcsh4\-redfaasprd|alsh1\-gpu\-gray\-1|rcsh\-spark\-shequ|rcsh1\-redindex\-1|alsh1\-flink\-gray|alsh1\-istio\-gray|qcsh5\-aiplatform|qcsh\-redtable\-1|ID_cls\-1nqvxujd|alsh\-redtable\-1|alsh1\-spark\-ads|ID_cls\-9gm2i653|ID_cls\-e6wai3a7|ID_cls\-ke3q1ye4|ID_cls\-6q1dku54|qcsh4\-redkv8\-1|qcsh5\-ray\-gray|qcsh4\-database|qcsh5\-gpu\-rdma|qcnj1\-database|qcsh8\-redhub\-1|qcsh4\-redis8\-1|rcsh1\-redoss\-2|rcsh\-spark\-rss|alsh1\-database|rcsh1\-redoss\-3|qcsh5\-database|qcsh4\-dedicate|rcsh1\-redoss\-4|qcsh8\-flink\-2|qcsh\-redtao\-1|qcsh8\-flink\-3|alsh1\-flink\-2|qcsh8\-redis\-1|qcsh5\-airflow|qcsh5\-flink\-3|isito\-sh4\-sit|qcsh3\-tools\-2|qcsh5\-flink\-2|alish\-redis\-5|alihz\-redis\-5|qcsh8\-kafka\-1|alish\-redis\-4|qcsh5\-redis\-a|rcsh1\-infra\-1|alsh1\-redkv\-3|alsh1\-reddb\-1|alish\-redis\-3|qcsh8\-redis\-2|alihz\-redis\-6|alhz\-database|alihz\-istio\-2|alsh1\-redkv\-2|qcsh5\-gpu\-ray|alsh1\-redkv\-4|qcsh\-redkv\-1|qcsh4\-secwxb|alhz\-redkv\-1|alsh\-fluss\-1|qcnj\-redis\-4|qcnj\-istio\-2|qcnj\-kafka\-1|rcsh1\-redoss|qcnj\-redis\-5|qcnj\-redis\-6|qcsh4\-lambda|qcsh\-flink\-1|qcsh4\-istio|qcsh8\-infra|alsh1\-ray\-3|qcsh4\-redkv|alsh2\-redis|qcnj2\-redkv|qcsh8\-dts\-1|alsh1\-infra|alsh1\-redkv|qcsh5\-istio|qcsh5\-flink|alhz1\-infra|alsh1\-spark|qcsh5\-redis|qcsh5\-redkv|alhz2\-redis|alhz1\-redis|rsi\-fed\-gpu|rcsh1\-redkv|alihz\-istio|rcjp\-redoss|qcsh4\-flink|qcsh3\-tools|qcnj2\-infra|alsh1\-ray\-2|alsh\-olap\-1|alsh1\-istio|alsh1\-dts\-1|rcsh1\-redis|qcnj2\-xray|alhz\-dts\-1|qcsh4\-xray|qcsh5\-olap|qcsh5\-meta|qcnj2\-eaas|qcsh5\-xray|rcsh\-lve\-1|alsh1\-gray|alhz1\-xray|alsh1\-meta|qcsh8\-olap|alsh1\-eaas|qcnj\-istio|qcnj\-gpu\-1|redisqcnj3|qcnj2\-meta|qcsh4\-mesh|rcsh1\-gray|fed\-qcsh4|qcbj1\-prd|qcsh5\-agi|rsi\-alhz1|rcsh1\-gpu|ali\-flink|alsh1\-gpu|alhz1\-new|qcsh4\-dts|qcsh5\-gpu|qcsh5\-new|rsi\-qcsh4|rsi\-rcsh1|rsi\-qcnj2|alsh1\-mix|rcsh1\-mix|rsi\-alsh1|rsi\-qcsh5|fed\-qcsh5|qcsh4\-new|alsh1\-ray|alsh1\-asl|qcsh\-sit|rcjp\-gpu|qcsh4new|alsh1\-it|sit\-faas|qcsh5\-3|alsh1\-5|qcsh4\-4|qcnj2\-6|alsh1\-6|qcsh5\-2|qcnj2\-4|rcsh1\-6|qcnj2\-2|qcnj2\-3|rcsh1\-5|qcnj2\-5|alsh1\-8|rcsh1\-3|alsh1\-7|rcsh1\-7|qcsh4\-3|alsh1\-2|qcsh4\-2|rcsh1\-2|alhz1\-5|kubeqa|qcsh4f|qcsh4e|qcsh4d|qcsh5|alhz1|qcsh4|qcnj1|rcsh1)(?![a-zA-Z0-9\-])",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "user.username",
                "patterns": [
                    r"(?:user\.username|用户名|操作用户|username)\s*[=:]?\s*([\w\-\.]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "verb",
                "patterns": [
                    r"\b(get|list|create|update|patch|delete|watch|deletecollection)\b",
                    r"(?:verb|操作动词|操作)\s*[=:]\s*([\w]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "objectRef.resource",
                "patterns": [
                    r"(?:resource|objectRef\.resource|资源类型)\s*[=:]\s*([\w]+)",
                    r"\b(pods|nodes|configmaps|secrets|deployments|services|namespaces)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "responseStatus.code",
                "patterns": [
                    r"(?:responseStatus\.code|状态码|响应码)\s*[=:]?\s*([2345]\d{2})",
                    r"\b([45]\d{2})\s*(?:错误|error)?(?=\b)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
        ],
    },
    "edith": {
        "table": "edith",
        "cluster_supported": False,
        "required_fields": ["subApplication"],
        "common_fields": ["subApplication", "level"],
        "display_fields": [
            "_time_second_",
            "subApplication",
            "level",
            "msg",
            "http_host",
            "request_uri",
            "response_status",
            "method",
            "_pod_name_",
        ],
        "nl_field_rules": [
            {
                "field": "subApplication",
                "patterns": [
                    # 显式写法：subApplication=xxx / app=xxx
                    r"(?:subApplication|app)\s*[=:]\s*(karen-gateway-[a-z0-9]+(?:-[a-z0-9]+)*)",
                    # 裸网关名：karen-gateway-xxx 格式，用 ASCII 边界
                    r"(?<![a-zA-Z0-9\-])(karen-gateway-[a-z0-9]+(?:-[a-z0-9]+)*)(?![a-zA-Z0-9\-])",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "level",
                "patterns": [
                    r"\b(error|错误|err)\b",
                    r"\b(warn|warning|告警)\b",
                    r"\b(info|信息)\b",
                    r"\b(debug|调试)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
                "value_map": {
                    "错误": "error",
                    "err": "error",
                    "warning": "warn",
                    "告警": "warn",
                    "信息": "info",
                    "调试": "debug",
                },
            },
            {
                "field": "http_host",
                "patterns": [
                    r"(?:域名|host|http_host)\s*[=:]?\s*([\w\-\.]+\.(?:com|cn|net|io)[\w\-\.]*)",
                    r"\b([\w\-]+\.xiaohongshu\.com)\b",
                    r"\b([\w\-]+\.xhs\.cn)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "request_uri",
                "patterns": [
                    r"(?:接口|路径|uri|request_uri|path)\s*[=:]?\s*(/[\w\-/\.]+)",
                    r"(/api/[\w\-/\.]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
            {
                "field": "response_status",
                "patterns": [
                    r"(?:状态码|status|response_status|http\s*status)\s*[=:]?\s*([45]\d{2})",
                    r"\b(5\d{2}|4\d{2})\s*(?:错误|error|报错)?(?=\b)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "method",
                "patterns": [
                    r"\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "_pod_name_",
                "patterns": [
                    r"(?:pod|_pod_name_)\s*[=:]?\s*([\w\-]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "msg",
                "patterns": [
                    r'(?:关键词|keyword|包含|msg|message)\s*[=:]?\s*["\'\'\']?([^\s"\'\'\'，,]+)["\'\'\']?',
                ],
                "value_group": 1,
                "op": ":",
                "quote": True,
            },
        ],
    },
    "pv": {
        "table": "pv",
        "cluster_supported": False,
        # context_artifactName 为必填字段
        "required_fields": ["context_artifactName"],
        "common_fields": ["context_artifactName", "measurement_name"],
        "display_fields": [
            "_time_second_",
            "context_artifactName",
            "measurement_name",
            "page_instance",
            "context_platform",
            "context_userId",
            "context_appVersion",
            "dtm",
        ],
        "nl_field_rules": [
            {
                "field": "context_artifactName",
                "patterns": [
                    r"(?:context_artifactName|artifactName|artifact|埋点应用|应用名)\s*[=:]?\s*([\w\-\.]+)",
                    # 常见应用名直接识别
                    r"(?<![a-zA-Z0-9\-])(xhs[-_]apm|xhs[-_]pc[-_]web|xhs[-_]ios|xhs[-_]android|com\.xingin\.xhs)(?![a-zA-Z0-9\-])",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "measurement_name",
                "patterns": [
                    r"(?:measurement_name|measurement|点位名|埋点名)\s*[=:]?\s*([\w\-\.]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "page_instance",
                "patterns": [
                    r"(?:page_instance|页面实例|页面)\s*[=:]?\s*([\w\-\.]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "context_platform",
                "patterns": [
                    r"(?:context_platform|platform|平台)\s*[=:]?\s*(Android|iOS|PC|Web|H5)",
                    r"\b(Android|iOS|PC|Web|H5)\b(?=\s*(?:端|平台|设备|用户|客户端))",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "context_userId",
                "patterns": [
                    r"(?:context_userId|userId|uid|用户[Ii][Dd]?)\s*[=:]?\s*([0-9a-fA-F]{24})",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "context_appVersion",
                "patterns": [
                    r"(?:context_appVersion|appVersion|版本)\s*[=:]?\s*([\d\.]+(?:-[\w]+)?)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "context_networkType",
                "patterns": [
                    r"(?:context_networkType|networkType|网络类型)\s*[=:]?\s*(wifi|5g|4g|3g|2g|unknown)",
                    r"\b(wifi|5[Gg]|4[Gg])\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
                "value_map": {
                    "5G": "5g",
                    "4G": "4g",
                    "WIFI": "wifi",
                },
            },
        ],
    },
    "measurement": {
        "table": "measurement",
        "cluster_supported": False,
        # context_artifactName 为必填字段
        "required_fields": ["context_artifactName"],
        "common_fields": ["context_artifactName", "measurement_name"],
        "display_fields": [
            "_time_second_",
            "context_artifactName",
            "measurement_name",
            "measurement_data",
            "context_platform",
            "context_userId",
            "context_appVersion",
            "dtm",
        ],
        "nl_field_rules": [
            {
                "field": "context_artifactName",
                "patterns": [
                    r"(?:context_artifactName|artifactName|artifact|应用名)\s*[=:]?\s*([\w\-\.]+)",
                    r"(?<![a-zA-Z0-9\-])(xhs[-_]apm|xhs[-_]pc[-_]web|xhs[-_]ios|xhs[-_]android|com\.xingin\.xhs)(?![a-zA-Z0-9\-])",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "measurement_name",
                "patterns": [
                    r"(?:measurement_name|measurement|指标名|流量名)\s*[=:]?\s*([\w\-\.]+)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "context_platform",
                "patterns": [
                    r"(?:context_platform|platform|平台)\s*[=:]?\s*(Android|iOS|PC|Web|H5)",
                    r"\b(Android|iOS|PC|Web|H5)\b(?=\s*(?:端|平台|设备|用户|客户端))",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "context_userId",
                "patterns": [
                    r"(?:context_userId|userId|uid|用户[Ii][Dd]?)\s*[=:]?\s*([0-9a-fA-F]{24})",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "context_appVersion",
                "patterns": [
                    r"(?:context_appVersion|appVersion|版本)\s*[=:]?\s*([\d\.]+(?:-[\w]+)?)",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
            },
            {
                "field": "context_networkType",
                "patterns": [
                    r"(?:context_networkType|networkType|网络类型)\s*[=:]?\s*(wifi|5g|4g|3g|2g|unknown)",
                    r"\b(wifi|5[Gg]|4[Gg])\b",
                ],
                "value_group": 1,
                "op": ":",
                "quote": False,
                "value_map": {
                    "5G": "5g",
                    "4G": "4g",
                    "WIFI": "wifi",
                },
            },
        ],
    },
}


def get_table_config(table: str) -> dict:
    """
    获取指定表的配置。

    Args:
        table: 表名，如 "application"、"rgw"、"flink"、"larc"、"event"、"audit"、"edith"

    Returns:
        表配置 dict

    Raises:
        ValueError: 未知的表名
    """
    if table not in TABLE_CONFIGS:
        supported = ", ".join(TABLE_CONFIGS.keys())
        raise ValueError(f"不支持的表名：'{table}'。当前支持的表：{supported}")
    return copy.deepcopy(TABLE_CONFIGS[table])
