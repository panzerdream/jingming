#!/usr/bin/env python3
"""
增强系统演示 - 修复版
"""

import os
import sys
import time
import json

# 设置路径
sys.path.insert(0, 'src')

print("=" * 60)
print("Agent RAG 增强系统演示")
print("=" * 60)
print()

# 1. 初始化系统
print("1. 初始化增强系统...")
from utils.logger import get_logger
from utils.monitor import get_metrics_collector
from tools.enhanced_tool_manager import get_tool_manager

logger = get_logger("demo")
metrics = get_metrics_collector()
tool_manager = get_tool_manager()

logger.info("增强系统初始化完成")
print("✓ 系统初始化完成")
print()

# 2. 演示日志系统
print("2. 日志系统演示...")
logger.debug("这是一条DEBUG日志")
logger.info("这是一条INFO日志", extra_data={"user": "demo_user", "action": "demo"})
logger.warning("这是一条WARNING日志")
logger.error("这是一条ERROR日志", extra_data={"error_code": 500})
print("✓ 日志已记录到 logs/app.log 和 logs/error.log")
print()

# 3. 演示监控系统
print("3. 监控系统演示...")
# 模拟一些API调用
for i in range(5):
    success = i < 4  # 4次成功，1次失败
    query_time = 0.1 + i * 0.05
    metrics.record_query(f"测试查询{i+1}", query_time, success)
    time.sleep(0.01)

# 记录一些工具使用
metrics.record_tool_usage("calculator", success=True)
metrics.record_tool_usage("web_search", success=False)

# 获取监控摘要
summary = metrics.get_summary()
print(f"✓ 查询统计: {summary['query_stats']['total_queries']} 次查询")
latency = summary['query_stats']['latency_stats']
print(f"✓ 平均响应时间: {latency['avg']:.3f}s (min: {latency['min']:.3f}s, max: {latency['max']:.3f}s)")
print()

# 4. 演示工具系统
print("4. 工具系统演示...")

test_cases = [
    ("计算器", "计算 2+3*4"),
    ("时间查询", "现在几点"),
    ("天气查询", "北京天气"),
    ("搜索", "搜索人工智能"),
]

for name, query in test_cases:
    print(f"\n  {name}演示:")
    print(f"    用户输入: \"{query}\"")
    
    # 意图识别
    intent, tool_name, params = tool_manager.intent_recognizer.recognize(query)
    if intent:
        print(f"    识别结果: 意图={intent}, 工具={tool_name}")
        
        # 执行工具
        start_time = time.time()
        result = tool_manager.run_tool(tool_name, params)
        execution_time = time.time() - start_time
        
        print(f"    执行时间: {execution_time:.3f}s")
        print(f"    结果: {result[:80]}...")
    else:
        print(f"    ✗ 未识别意图")

print()

# 5. 演示系统资源监控
print("5. 系统资源监控演示...")
resource_stats = summary['system_metrics']
print(f"✓ CPU使用率: {resource_stats['cpu_percent']:.1f}%")
print(f"✓ 内存使用率: {resource_stats['memory_percent']:.1f}% ({resource_stats['memory_used_gb']:.1f}GB / {resource_stats['memory_total_gb']:.0f}GB)")
print(f"✓ 磁盘使用率: {resource_stats['disk_percent']:.1f}% ({resource_stats['disk_used_gb']:.1f}GB / {resource_stats['disk_total_gb']:.0f}GB)")
print()

# 6. 查看日志文件
print("6. 查看生成的日志文件...")
import glob
log_files = glob.glob("logs/*.log")
if log_files:
    print(f"✓ 找到 {len(log_files)} 个日志文件:")
    for log_file in sorted(log_files):
        file_size = os.path.getsize(log_file)
        print(f"    - {os.path.basename(log_file)} ({file_size} bytes)")
    
    # 显示最新日志内容
    print("\n  最新日志内容:")
    try:
        with open("logs/app.log", "r") as f:
            lines = f.readlines()[-5:]  # 最后5行
            for line in lines:
                # 解析JSON日志
                try:
                    log_entry = json.loads(line.strip())
                    level = log_entry.get("level", "UNKNOWN")
                    message = log_entry.get("message", "")
                    timestamp = log_entry.get("timestamp", "")
                    print(f"    [{timestamp}] {level}: {message[:60]}...")
                except:
                    print(f"    {line[:80]}...")
    except Exception as e:
        print(f"    读取日志失败: {e}")
else:
    print("✗ 未找到日志文件")

print()
print("=" * 60)
print("演示完成!")
print("=" * 60)
print()
print("系统状态总结:")
print(f"- 日志系统: ✓ 运行正常")
print(f"- 监控系统: ✓ 收集了 {summary['query_stats']['total_queries']} 次查询数据")
print(f"- 工具系统: ✓ 测试了 {len(test_cases)} 个工具")
print(f"- 资源监控: ✓ CPU {resource_stats['cpu_percent']:.1f}%, 内存 {resource_stats['memory_percent']:.1f}%")
print()
print("要查看完整日志:")
print("  tail -f logs/app.log")
print()
print("要查看监控数据:")
print("  python3 -c \"import sys; sys.path.insert(0,'src'); from utils.monitor import get_metrics_collector; m=get_metrics_collector(); import json; print(json.dumps(m.get_summary(), indent=2, ensure_ascii=False))\"")
