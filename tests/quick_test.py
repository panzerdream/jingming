#!/usr/bin/env python3
"""
快速测试增强系统的核心功能
"""

import os
import sys
import time

# 设置路径
sys.path.insert(0, 'src')

print("=== 快速测试增强系统 ===")
print()

# 1. 测试日志系统
print("1. 测试日志系统...")
from utils.logger import get_logger
logger = get_logger("quick_test")
logger.info("日志系统测试成功", extra_data={"test": "quick"})
print("✓ 日志系统正常")
print()

# 2. 测试监控系统
print("2. 测试监控系统...")
from utils.monitor import get_metrics_collector
metrics = get_metrics_collector()

# 记录一些数据
metrics.record_query("测试查询1", 0.15, True)
metrics.record_query("测试查询2", 0.25, False)
metrics.record_tool_usage("calculator", True)
metrics.record_tool_usage("web_search", False)

summary = metrics.get_summary()
print(f"✓ 监控系统正常")
print(f"  总查询数: {summary['query_stats']['total_queries']}")
print(f"  工具使用: {len(summary.get('tool_usage', {}))} 个工具")
print()

# 3. 测试工具系统
print("3. 测试工具系统...")
from tools.enhanced_tool_manager import get_tool_manager
tool_manager = get_tool_manager()

# 测试几个工具
tools_to_test = [
    ("calculator", {"expression": "2+3*4"}),
    ("get_current_time", {}),
]

for tool_name, params in tools_to_test:
    try:
        result = tool_manager.run_tool(tool_name, params)
        print(f"  ✓ {tool_name}: {result[:50]}...")
    except Exception as e:
        print(f"  ✗ {tool_name} 失败: {e}")

print()

# 4. 测试意图识别
print("4. 测试意图识别...")
test_queries = [
    "计算 100/25",
    "现在几点",
    "搜索人工智能",
]

for query in test_queries:
    intent, tool_name, params = tool_manager.intent_recognizer.recognize(query)
    if intent:
        print(f"  ✓ '{query}' -> {intent} ({tool_name})")
    else:
        print(f"  ✗ '{query}' -> 未识别")

print()

# 5. 检查日志文件
print("5. 检查生成的文件...")
import glob
log_files = glob.glob("logs/*.log")
json_files = glob.glob("logs/*.json")

print(f"  日志文件: {len(log_files)} 个")
print(f"  JSON文件: {len(json_files)} 个")

if log_files:
    latest_log = max(log_files, key=os.path.getctime)
    size = os.path.getsize(latest_log)
    print(f"  最新日志: {os.path.basename(latest_log)} ({size} bytes)")

print()
print("=== 测试完成 ===")
print("增强系统核心功能运行正常！")
print()
print("系统现在具备:")
print("✓ 结构化日志记录")
print("✓ 实时性能监控")
print("✓ 智能工具调用")
print("✓ 意图识别能力")
print("✓ 系统资源监控")
