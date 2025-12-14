# tuba.log

JSON 格式日志模块，兼容 Go tuba/log 输出格式。

## 快速开始

```python
from tuba import log

# 直接使用（默认 debug 模式）
log.info("hello", "world")
log.errorf("error code: %d", 500)
```

## 初始化配置

```python
log.init(log.Config(
    log_path="/var/log/app",  # 日志目录
    app_name="myapp",         # 应用名
    debug=True,               # 开启 debug 级别
    multi_file=False,         # 按级别分文件
))
```

## 日志级别

| 函数 | 格式化函数 | 说明 |
|------|-----------|------|
| `debug()` | `debugf()` | 调试日志 |
| `info()` | `infof()` | 信息日志 |
| `warn()` | `warnf()` | 警告日志 |
| `error()` | `errorf()` | 错误日志 |
| `fatal()` | `fatalf()` | 致命错误，会退出程序 |

## Trace ID

```python
# 方式一：上下文管理
token = log.with_trace_id("req-123")
log.info("processing")  # 自动携带 trace_id
log.reset_trace_id(token)

# 方式二：直接传入
log.ctx_info("req-123", "processing")
log.ctx_errorf("req-123", "failed: %s", err)
```

## 输出示例

```json
{"level":"info","event_time":"1702540800","msg":"hello world","trace_id":"req-123"}
```

