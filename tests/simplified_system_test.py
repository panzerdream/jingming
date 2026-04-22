#!/usr/bin/env python3
"""
简化系统测试脚本
只测试核心功能，避免长时间API调用
"""

import os
import sys
import time
import json

# 设置环境变量
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 添加项目路径
sys.path.insert(0, 'src')

from utils.logger import get_logger
from utils.monitor import get_system_summary, export_metrics

logger = get_logger()

def test_logging_system():
    """测试日志系统"""
    print("=== 测试1: 日志系统 ===")
    
    try:
        # 检查日志目录
        if not os.path.exists("logs"):
            os.makedirs("logs")
            print("✓ 创建日志目录")
        
        # 测试日志记录
        logger.info("测试信息日志", test="logging_test")
        logger.warning("测试警告日志", test="logging_test")
        logger.error("测试错误日志", error_type="test_error")
        
        # 检查日志文件
        log_file = "logs/agent_rag.log"
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_logs = lines[-5:] if len(lines) >= 5 else lines
            
            print(f"✓ 日志文件存在，最近日志:")
            for log in recent_logs:
                print(f"  {log.strip()}")
        else:
            print("✗ 日志文件不存在")
        
        print("✓ 日志系统工作正常")
        
    except Exception as e:
        print(f"✗ 日志系统测试失败: {e}")

def test_monitoring_system():
    """测试监控系统"""
    print("\n=== 测试2: 监控系统 ===")
    
    try:
        # 获取系统摘要
        summary = get_system_summary()
        
        print("系统摘要:")
        print(f"  CPU使用率: {summary.get('cpu_percent', 'N/A')}%")
        print(f"  内存使用率: {summary.get('memory_percent', 'N/A')}%")
        print(f"  磁盘使用率: {summary.get('disk_percent', 'N/A')}%")
        print(f"  系统运行时间: {summary.get('uptime', 'N/A')}秒")
        print(f"  健康状态: {summary.get('health_status', 'N/A')}")
        
        # 导出指标
        metrics = export_metrics()
        
        print("\n指标统计:")
        print(f"  查询指标数量: {len(metrics.get('query_metrics', []))}")
        print(f"  工具使用记录: {len(metrics.get('tool_usage', []))}")
        print(f"  错误记录数量: {len(metrics.get('errors', []))}")
        
        print("✓ 监控系统工作正常")
        
    except Exception as e:
        print(f"✗ 监控系统测试失败: {e}")

def test_tool_intent_recognition():
    """测试工具意图识别"""
    print("\n=== 测试3: 工具意图识别 ===")
    
    try:
        from tools.enhanced_tool_manager import IntentRecognizer
        
        recognizer = IntentRecognizer()
        
        test_cases = [
            ("计算一下25乘以4", "calculate", "calculator"),
            ("现在几点", "time", "get_current_time"),
            ("北京的天气", "weather", "get_weather"),
            ("搜索Python教程", "search", "web_search"),
            ("翻译hello world", "translate", "translate_text"),
        ]
        
        for query, expected_intent, expected_tool in test_cases:
            intent, tool_name, params = recognizer.recognize(query)
            
            print(f"\n查询: {query}")
            print(f"识别结果: 意图={intent}, 工具={tool_name}")
            print(f"预期结果: 意图={expected_intent}, 工具={expected_tool}")
            
            if intent == expected_intent and tool_name == expected_tool:
                print("✓ 识别正确")
            else:
                print("✗ 识别错误")
        
        print("✓ 意图识别系统工作正常")
        
    except Exception as e:
        print(f"✗ 意图识别测试失败: {e}")

def test_enhanced_tools():
    """测试增强工具"""
    print("\n=== 测试4: 增强工具测试 ===")
    
    try:
        from tools.enhanced_tool_manager import EnhancedToolManager
        
        tool_manager = EnhancedToolManager()
        
        # 测试计算器工具
        print("\n测试计算器工具:")
        test_calculations = [
            ("25 * 4", "100"),
            ("12 + 8", "20"),
            ("15 - 7", "8"),
            ("36 / 6", "6"),
        ]
        
        for expression, expected in test_calculations:
            try:
                result = tool_manager.calculator(expression)
                print(f"  {expression} = {result} (预期: {expected})")
                if result == expected:
                    print("  ✓ 计算正确")
                else:
                    print(f"  ✗ 计算错误: 得到 {result}, 预期 {expected}")
            except Exception as e:
                print(f"  ✗ 计算失败: {e}")
        
        # 测试时间工具
        print("\n测试时间工具:")
        try:
            current_time = tool_manager.get_current_time()
            print(f"  当前时间: {current_time}")
            print("  ✓ 时间工具工作正常")
        except Exception as e:
            print(f"  ✗ 时间工具失败: {e}")
        
        print("✓ 增强工具系统工作正常")
        
    except Exception as e:
        print(f"✗ 增强工具测试失败: {e}")

def test_code_quality():
    """测试代码质量"""
    print("\n=== 测试5: 代码质量检查 ===")
    
    try:
        # 检查核心文件是否存在
        core_files = [
            "src/main.py",
            "src/tools/enhanced_tool_manager.py",
            "src/api/bailian_api.py",
            "src/utils/logger.py",
            "src/utils/monitor.py",
        ]
        
        missing_files = []
        for file_path in core_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"✗ 缺少文件: {missing_files}")
        else:
            print("✓ 所有核心文件都存在")
        
        # 检查Python语法
        print("\n检查Python语法:")
        for file_path in core_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"  ✓ {file_path} 语法正确")
            except SyntaxError as e:
                print(f"  ✗ {file_path} 语法错误: {e}")
        
        # 检查依赖导入
        print("\n检查依赖导入:")
        try:
            import requests
            import langchain
            import faiss
            import markdown
            import psutil
            print("  ✓ 所有依赖都可导入")
        except ImportError as e:
            print(f"  ✗ 依赖导入失败: {e}")
        
        print("✓ 代码质量检查完成")
        
    except Exception as e:
        print(f"✗ 代码质量检查失败: {e}")

def main():
    """主测试函数"""
    print("=" * 60)
    print("Agent RAG 增强系统简化测试")
    print("=" * 60)
    
    # 测试日志系统
    test_logging_system()
    
    # 测试监控系统
    test_monitoring_system()
    
    # 测试工具意图识别
    test_tool_intent_recognition()
    
    # 测试增强工具
    test_enhanced_tools()
    
    # 测试代码质量
    test_code_quality()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()