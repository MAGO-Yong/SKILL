# XRay Logview API 参考文档

## 接口

```
GET {base_url}/open/skill/application/r/logview/{messageId}/json

Path参数:  messageId  - CAT消息ID，格式: {domain}-{ip}-{hour}-{index}
                        例: order-service-c0a80101-456789-1
Query参数: startTime  - (可选) 毫秒时间戳
           endTime    - (可选) 毫秒时间戳
```

## 返回值结构

```json
{
  "code": 0,
  "data": {
    "domain": "order-service",
    "hostName": "host-001",
    "ipAddress": "10.0.0.1",
    "zone": "cn-beijing-a",
    "startTime": "2024-01-01 12:00:00.000",
    "durationInMills": 150,
    "messageId": "order-service-c0a80101-456789-1",
    "parentMessageId": "gateway-c0a80102-456789-1",
    "rootMessageId": "gateway-c0a80102-456789-1",
    "threadId": "200",
    "threadName": "cat-io-1",
    "traceId": "abc123",
    "code": 200,
    "message": {}
  }
}
```

### code 含义

| code | 含义                               |
| ---- | ---------------------------------- |
| 200  | 成功                               |
| 1003 | 数据缺失（数据尚在保留期但未找到） |
| 1004 | 数据已过期归档                     |

## MessageDTO 消息树节点（递归结构）

```json
{
  "type": "PigeonCall",
  "name": "order-service.OrderService.createOrder",
  "status": "0",
  "timestamp": 1704067200000,
  "data": "slaLevel=2&strongDependence=true",
  "durationInMillis": 80,
  "durationInMicros": 80123,
  "error": false,
  "parentType": "URL",
  "parentName": "/api/order/create",
  "children": []
}
```

### 字段说明

| 字段             | 说明                                               |
| ---------------- | -------------------------------------------------- |
| type             | 消息类型（见下表）                                 |
| name             | 消息名称，Call类型为 `服务名.接口名`               |
| status           | "0"=成功，其他=失败                                |
| durationInMillis | 耗时(ms)，≥0 为 Transaction，-1 为 Event           |
| error            | type 为 Error/RuntimeException/Exception 时为 true |
| data             | KV字符串；Call节点额外含 slaLevel/strongDependence |
| children         | 子节点列表（递归）                                 |

### 常见 type 类型

| type              | 分类        | 说明                   |
| ----------------- | ----------- | ---------------------- |
| URL               | Transaction | HTTP 请求入口          |
| PigeonCall / Call | Transaction | RPC 下游调用           |
| SQL               | Transaction | 数据库查询             |
| Cache             | Transaction | 缓存操作               |
| HTTPClient        | Transaction | HTTP 外部调用          |
| Error             | Event       | Java 异常              |
| RuntimeException  | Event       | 运行时异常             |
| Exception         | Event       | 受检异常               |
| RemoteCall        | Event       | 跨服务 traceId 引用    |
| Trace             | Event       | 业务埋点日志           |
| Heartbeat         | Heartbeat   | 系统心跳（CPU/内存等） |

### data 字段解析（Call 节点）

```
slaLevel=2&strongDependence=true
```

| key              | 说明                                                |
| ---------------- | --------------------------------------------------- |
| slaLevel         | SLA 等级（1=P0核心, 2=P1重要, 3=P2一般, -1=未配置） |
| strongDependence | 是否强依赖（true=强依赖，false/空=弱依赖）          |

## 异常接口（补充）

```
GET {base_url}/open/skill/application/r/logview/{messageId}/exception
返回: type 为 Error/RuntimeException/Exception 的所有节点列表
```

```json
[
  {
    "name": "java.lang.NullPointerException",
    "timestamp": 1704067200000,
    "parentType": "PigeonCall",
    "parentName": "order-service.OrderService.createOrder"
  }
]
```
