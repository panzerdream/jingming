#!/usr/bin/env python3
"""
完整系统测试脚本
测试增强后的Agent RAG系统的所有功能
"""

import os
import sys
import time
import json

# 设置环境变量
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 添加项目路径
sys.path.insert(0, 'src')

from main import AgentRAG
from utils.logger import get_logger
from utils.monitor import get_system_summary, export_metrics

logger = get_logger()

def test_system_initialization():
    """测试系统初始化"""
    print("=== 测试1: 系统初始化 ===")
    try:
        agent = AgentRAG()
        print("✓ 系统初始化成功")
        return agent
    except Exception as e:
        print(f"✗ 系统初始化失败: {e}")
        return None

def test_tool_system(agent):
    """测试工具系统"""
    print("\n=== 测试2: 工具系统 ===")
    
    test_cases = [
        ("计算一下25乘以4", "应该触发计算器工具"),
        ("12加8等于多少", "应该触发计算器工具"),
        ("15-7", "应该触发计算器工具"),
        ("现在几点", "应该触发时间工具"),
        ("北京的天气", "应该触发天气工具"),
    ]
    
    for query, expected in test_cases:
        print(f"\n查询: {query}")
        print(f"预期: {expected}")
        
        try:
            start_time = time.time()
            response = agent.process_query(query)
            elapsed = time.time() - start_time
            
            print(f"响应: {response[:100]}...")
            print(f"耗时: {elapsed:.2f}秒")
            
            # 检查是否触发了工具
            if "（基于工具查询）" in response or "工具执行结果" in response:
                print("✓ 工具触发成功")
            else:
                print("⚠ 可能未触发工具")
                
        except Exception as e:
            print(f"✗ 查询失败: {e}")

def test_monitoring_system():
    """测试监控系统"""
    print("\n=== 测试3: 监控系统 ===")
    
    try:
        # 获取系统摘要
        summary = get_system_summary()
        print("系统摘要:")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        
        # 导出指标
        metrics = export_metrics()
        print(f"\n已收集 {len(metrics.get('query_metrics', []))} 个查询指标")
        print(f"已收集 {len(metrics.get('tool_usage', []))} 个工具使用记录")
        print(f"已收集 {len(metrics.get('errors', []))} 个错误记录")
        
        print("✓ 监控系统工作正常")
        
    except Exception as e:
        print(f"✗ 监控系统测试失败: {e}")

def test_logging_system():
    """测试日志系统"""
    print("\n=== 测试4: 日志系统 ===")
    
    try:
        # 检查日志文件是否存在
        log_files = [
            "logs/agent_rag.log",
            "logs/agent_rag_structured.json"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                print(f"✓ {log_file} 存在 ({size} 字节)")
            else:
                print(f"✗ {log_file} 不存在")
        
        # 测试日志记录
        logger.info("测试日志记录", test="logging_test")
        logger.error("测试错误日志", error_type="test_error")
        
        print("✓ 日志系统工作正常")
        
    except Exception as e:
        print(f"✗ 日志系统测试失败: {e}")

def test_api_performance(agent):
    """测试API性能"""
    print("\n=== 测试5: API性能测试 ===")
    
    test_queries = [
        "星露谷物语是什么游戏？",
        "谢恩喜欢什么礼物？",
        "如何解锁温室？",
    ]
    
    total_time = 0
    successful_queries = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n查询 {i}: {query}")
        
        try:
            start_time = time.time()
            response = agent.process_query(query)
            elapsed = time.time() - start_time
            
            total_time += elapsed
            successful_queries += 1
            
            print(f"响应长度: {len(response)} 字符")
            print(f"耗时: {elapsed:.2f}秒")
            
            if elapsed > 20:
                print("⚠ 响应时间较长")
            elif elapsed > 10:
                print("⚠ 响应时间中等")
            else:
                print("✓ 响应时间良好")
                
        except Exception as e:
            print(f"✗ 查询失败: {e}")
    
    if successful_queries > 0:
        avg_time = total_time / successful_queries
        print(f"\n平均响应时间: {avg_time:.2f}秒")
        
        if avg_time < 10:
            print("✓ API性能良好")
        elif avg_time < 15:
            print("⚠ API性能中等")
        else:
            print("⚠ API性能需要优化")

def main():
    """主测试函数"""
    print("=" * 60)
    print("Agent RAG 增强系统完整测试")
    print("=" * 60)
    
    # 测试系统初始化
    agent = test_system_initialization()
    if not agent:
        print("系统初始化失败，终止测试")
        return
    
    # 测试工具系统
    test_tool_system(agent)
    
    # 测试监控系统
    test_monitoring_system()
    
    # 测试日志系统
    test_logging_system()
    
    # 测试API性能
    test_api_performance(agent)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()