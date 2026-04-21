# 系统增强功能说明

## 新增功能概述

本次更新为 Agent RAG 系统添加了三个核心增强功能：

1. **完善的日志系统** - 结构化日志记录，支持多级别日志和JSON格式输出
2. **系统监控功能** - 实时监控系统性能指标和健康状态
3. **增强的工具系统** - 智能意图识别和丰富的工具集

## 1. 日志系统

### 功能特性
- **多级别日志**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **结构化输出**: 支持JSON格式日志，便于日志分析
- **日志轮转**: 自动轮转日志文件，防止磁盘空间耗尽
- **上下文信息**: 自动记录文件名、行号、时间戳等信息
- **专用日志类型**: 查询日志、工具使用日志、API调用日志等

### 使用方法
```python
from utils.logger import get_logger, info, error

logger = get_logger()
logger.info("系统启动")
logger.error("发生错误", error_type="api_error")

# 便捷函数
info("信息日志")
error("错误日志")
```

### 日志文件
- `logs/agent_rag.log` - 标准文本日志
- `logs/agent_rag_structured.json` - JSON格式结构化日志

## 2. 监控系统

### 功能特性
- **系统指标监控**: CPU、内存、磁盘使用率
- **应用指标监控**: 查询延迟、工具使用统计、错误率
- **健康度评估**: 自动评估系统健康状态
- **实时监控**: 后台线程定期收集指标
- **指标导出**: 支持JSON格式导出

### 使用方法
```python
from utils.monitor import start_monitoring, get_system_summary, export_metrics

# 启动监控（60秒间隔）
start_monitoring(interval=60)

# 获取系统状态
status = get_system_summary()
print(json.dumps(status, indent=2))

# 导出指标
export_metrics("system_metrics.json")
```

### 监控指标
- **查询统计**: 总数、平均延迟、成功率
- **工具使用**: 各工具调用次数
- **系统资源**: CPU、内存、磁盘使用率
- **错误统计**: 各类错误发生次数
- **运行时间**: 系统运行时长

## 3. 增强的工具系统

### 功能特性
- **智能意图识别**: 基于正则表达式的意图识别
- **丰富工具集**: 10+个内置工具
- **参数自动提取**: 自动从查询中提取工具参数
- **错误处理**: 完善的工具执行错误处理
- **指标集成**: 工具使用情况自动记录到监控系统

### 可用工具列表
1. **web_search** - 网页搜索（模拟）
2. **calculator** - 数学计算器
3. **get_current_time** - 获取当前时间
4. **get_weather** - 获取天气信息
5. **wikipedia_search** - 维基百科搜索
6. **translate_text** - 文本翻译
7. **unit_converter** - 单位转换
8. **currency_converter** - 货币转换

### 使用方法
```python
from tools.enhanced_tool_manager import (
    get_tool_manager, 
    should_use_tool, 
    parse_tool_call, 
    run_tool
)

# 判断是否需要工具
if should_use_tool(query):
    # 解析工具调用
    tool_name, params = parse_tool_call(query)
    # 执行工具
    result = run_tool(tool_name, params)
```

### 支持的查询示例
- "搜索星露谷物语攻略" → web_search工具
- "计算2+3*4" → calculator工具
- "现在几点" → get_current_time工具
- "北京的天气" → get_weather工具
- "翻译你好世界" → translate_text工具
- "100厘米等于多少米" → unit_converter工具

## 4. 主系统增强

### 新增功能
- **系统状态查询**: 输入"状态"查看系统运行状态
- **工具列表查看**: 输入"工具"查看可用工具
- **指标导出**: 输入"导出"导出系统指标
- **错误处理**: 完善的异常处理和错误恢复
- **性能监控**: 自动记录查询处理时间

### 使用示例
```
用户：状态
Agent：系统状态信息（JSON格式）

用户：工具
Agent：可用工具列表

用户：导出
Agent：系统指标已导出到 system_metrics.json

用户：搜索星露谷物语
Agent：（基于工具查询）搜索结果...

用户：计算圆的面积
Agent：（基于工具查询）计算结果...
```

## 5. 测试脚本

提供了完整的测试脚本 `test_enhanced_system.py`：

```bash
# 运行测试
python test_enhanced_system.py

# 测试内容
1. 日志系统测试
2. 监控系统测试
3. 工具系统测试
4. 集成功能测试
```

## 6. 配置说明

### 新增依赖
```txt
psutil>=5.9.0  # 系统监控
```

### 环境变量
无需新增环境变量，所有功能使用现有配置。

## 7. 文件结构更新

```
src/
├── utils/
│   ├── logger.py          # 日志系统
│   └── monitor.py         # 监控系统
├── tools/
│   ├── enhanced_tool_manager.py  # 增强工具管理器
│   └── tool_manager.py    # 原始工具管理器（保留）
```

## 8. 性能考虑

1. **日志性能**: 异步日志写入，不影响主程序性能
2. **监控开销**: 监控线程低频率运行（默认60秒）
3. **内存使用**: 指标数据有大小限制，防止内存泄漏
4. **磁盘空间**: 日志轮转机制防止磁盘空间耗尽

## 9. 扩展建议

1. **日志分析**: 集成ELK栈进行日志分析
2. **告警系统**: 添加阈值告警功能
3. **仪表盘**: 创建Web监控仪表盘
4. **更多工具**: 集成更多实用工具
5. **API集成**: 集成真实的搜索、翻译等API

## 10. 故障排除

### 常见问题
1. **日志文件过大**: 检查日志级别设置，适当调整轮转配置
2. **监控数据不准确**: 检查psutil安装和权限
3. **工具识别错误**: 调整意图识别模式
4. **性能下降**: 调整监控间隔，减少日志输出

### 调试方法
```python
# 设置详细日志
import logging
logging.getLogger().setLevel(logging.DEBUG)

# 检查系统状态
from utils.monitor import get_system_summary
print(get_system_summary())
```

---

**注意**: 所有新增功能都与原有系统兼容，不会影响现有功能的使用。