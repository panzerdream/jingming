#!/usr/bin/env python3
"""
API参数优化测试
测试优化后的性能表现
"""

import os
import sys
import time
import json

# 设置环境变量
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 添加项目路径
sys.path.insert(0, 'src')

from main_optimized import OptimizedAgentRAG
from utils.logger import get_logger

logger = get_logger()

def test_optimized_performance():
    """测试优化后的性能"""
    print("=" * 80)
    print("API参数优化测试")
    print("=" * 80)
    
    print(f"当前配置 (从.env文件读取):")
    print(f"  API_TIMEOUT: {os.getenv('API_TIMEOUT', '15')}秒")
    print(f"  MAX_RESPONSE_TOKENS: {os.getenv('MAX_RESPONSE_TOKENS', '150')}")
    print(f"  TEMPERATURE: {os.getenv('TEMPERATURE', '0.2')}")
    
    try:
        # 初始化系统
        print("\n初始化优化系统...")
        start_init = time.time()
        agent = OptimizedAgentRAG()
        init_time = time.time() - start_init
        print(f"✓ 系统初始化完成，耗时: {init_time:.2f}秒")
        
        print(f"\n系统实际配置:")
        print(f"  API超时: {agent.api_timeout}秒")
        print(f"  最大响应token: {agent.max_response_tokens}")
        print(f"  温度: {agent.temperature}")
        print(f"  模型: {agent.model_name}")
        
        # 测试用例
        test_cases = [
            {
                "name": "工具查询-简单计算",
                "query": "25乘以4",
                "expected_time": 5,
                "type": "tool"
            },
            {
                "name": "工具查询-复杂计算", 
                "query": "123乘以456除以789",
                "expected_time": 5,
                "type": "tool"
            },
            {
                "name": "知识查询-简单",
                "query": "星露谷在哪里",
                "expected_time": 10,
                "type": "knowledge"
            },
            {
                "name": "知识查询-复杂",
                "query": "星露谷的农场在哪里？请详细说明位置和如何到达",
                "expected_time": 15,
                "type": "knowledge"
            },
            {
                "name": "混合查询",
                "query": "今天是几号？另外星露谷的天气怎么样",
                "expected_time": 8,
                "type": "mixed"
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"测试 {i}: {test['name']}")
            print(f"{'='*60}")
            print(f"查询类型: {test['type']}")
            print(f"查询内容: {test['query']}")
            print(f"期望时间: <{test['expected_time']}秒")
            
            try:
                start_time = time.time()
                response = agent.process_query(test['query'])
                elapsed = time.time() - start_time
                
                print(f"实际耗时: {elapsed:.2f}秒")
                print(f"响应预览: {response[:80]}...")
                
                # 性能评估
                if elapsed > agent.api_timeout:
                    status = "❌ 超时"
                    print(f"状态: {status} (超过API超时设置)")
                elif elapsed > test['expected_time']:
                    status = "⚠ 较慢"
                    print(f"状态: {status} (超过期望时间)")
                elif elapsed < 3:
                    status = "✅ 优秀"
                    print(f"状态: {status} (响应迅速)")
                elif elapsed < test['expected_time'] * 0.7:
                    status = "✅ 良好"
                    print(f"状态: {status} (在期望时间内)")
                else:
                    status = "⚠ 一般"
                    print(f"状态: {status} (接近期望时间)")
                
                # 质量评估
                if len(response) < 10:
                    quality = "⚠ 响应过短"
                elif "已收到您的查询" in response or "好的，我了解了" in response:
                    quality = "⚠ 备用回复"
                elif "工具执行结果" in response or "计算结果是" in response:
                    quality = "✅ 工具结果"
                else:
                    quality = "✅ 正常回复"
                
                print(f"质量: {quality}")
                
                # 记录结果
                results.append({
                    "name": test['name'],
                    "type": test['type'],
                    "query": test['query'],
                    "expected_time": test['expected_time'],
                    "actual_time": elapsed,
                    "status": status,
                    "quality": quality,
                    "response_preview": response[:100]
                })
                
            except Exception as e:
                print(f"❌ 查询失败: {e}")
                results.append({
                    "name": test['name'],
                    "type": test['type'],
                    "query": test['query'],
                    "error": str(e),
                    "status": "❌ 失败"
                })
        
        # 生成性能报告
        print(f"\n{'='*80}")
        print("性能优化测试报告")
        print(f"{'='*80}")
        
        successful_tests = [r for r in results if 'actual_time' in r]
        if successful_tests:
            total_time = sum(r['actual_time'] for r in successful_tests)
            avg_time = total_time / len(successful_tests)
            
            print(f"测试总数: {len(test_cases)}")
            print(f"成功测试: {len(successful_tests)}")
            print(f"平均响应时间: {avg_time:.2f}秒")
            
            # 按类型分析
            tool_tests = [r for r in successful_tests if r['type'] == 'tool']
            knowledge_tests = [r for r in successful_tests if r['type'] == 'knowledge']
            mixed_tests = [r for r in successful_tests if r['type'] == 'mixed']
            
            if tool_tests:
                tool_avg = sum(r['actual_time'] for r in tool_tests) / len(tool_tests)
                print(f"\n工具查询性能:")
                print(f"  测试数: {len(tool_tests)}")
                print(f"  平均时间: {tool_avg:.2f}秒")
                if tool_avg < 3:
                    print(f"  ✅ 工具系统性能优秀")
                elif tool_avg < 5:
                    print(f"  ✅ 工具系统性能良好")
                else:
                    print(f"  ⚠ 工具系统性能一般")
            
            if knowledge_tests:
                knowledge_avg = sum(r['actual_time'] for r in knowledge_tests) / len(knowledge_tests)
                print(f"\n知识查询性能:")
                print(f"  测试数: {len(knowledge_tests)}")
                print(f"  平均时间: {knowledge_avg:.2f}秒")
                if knowledge_avg < 8:
                    print(f"  ✅ 知识查询性能优秀")
                elif knowledge_avg < 12:
                    print(f"  ✅ 知识查询性能良好")
                elif knowledge_avg < 15:
                    print(f"  ⚠ 知识查询性能一般")
                else:
                    print(f"  ⚠ 知识查询性能较差")
            
            # 超时分析
            timeout_tests = [r for r in successful_tests if r['actual_time'] > agent.api_timeout]
            if timeout_tests:
                print(f"\n⚠ 超时测试 ({len(timeout_tests)}个):")
                for test in timeout_tests:
                    print(f"  - {test['name']}: {test['actual_time']:.2f}秒 (超时: {agent.api_timeout}秒)")
            
            # 优化效果评估
            print(f"\n优化效果评估:")
            if avg_time < 8:
                print(f"  ✅ 整体性能优秀 (平均{avg_time:.2f}秒)")
                print(f"  ✅ API参数优化效果显著")
            elif avg_time < 12:
                print(f"  ✅ 整体性能良好 (平均{avg_time:.2f}秒)")
                print(f"  ✅ API参数优化有效")
            elif avg_time < 15:
                print(f"  ⚠ 整体性能一般 (平均{avg_time:.2f}秒)")
                print(f"  ⚠ 可能需要进一步优化")
            else:
                print(f"  ⚠ 整体性能较差 (平均{avg_time:.2f}秒)")
                print(f"  ⚠ 需要重新评估优化策略")
        
        # 保存详细结果
        report_file = "optimization_report.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "config": {
                        "api_timeout": agent.api_timeout,
                        "max_response_tokens": agent.max_response_tokens,
                        "temperature": agent.temperature,
                        "model_name": agent.model_name
                    },
                    "results": results,
                    "summary": {
                        "total_tests": len(test_cases),
                        "successful_tests": len(successful_tests),
                        "average_time": avg_time if successful_tests else 0
                    }
                }, f, ensure_ascii=False, indent=2)
            print(f"\n📊 详细报告已保存到: {report_file}")
        except Exception as e:
            print(f"\n⚠ 无法保存报告: {e}")
            
    except Exception as e:
        print(f"\n❌ 系统初始化失败: {e}")

def compare_optimization():
    """比较优化前后的效果"""
    print(f"\n{'='*80}")
    print("优化前后对比")
    print(f"{'='*80}")
    
    print("优化前 (基于日志分析):")
    print("  - API超时: 20秒")
    print("  - 实际响应时间: 12-20秒")
    print("  - 经常触发备用回复")
    print("  - 用户体验: 较差")
    
    print("\n优化后 (目标):")
    print("  - API超时: 15秒")
    print("  - 目标响应时间: 8-12秒")
    print("  - 减少备用回复使用")
    print("  - 用户体验: 改善")
    
    print("\n优化措施:")
    print("  1. 减少API超时从20秒到15秒")
    print("  2. 保持较低的token限制 (150)")
    print("  3. 保持较低的温度参数 (0.2)")
    print("  4. 使用压缩的提示词模板")
    print("  5. 实现动态备用回复机制")
    
    print("\n预期效果:")
    print("  - 工具查询: 2-5秒 ✓")
    print("  - 简单知识查询: 5-10秒 ⚠")
    print("  - 复杂知识查询: 10-15秒 ⚠")
    print("  - 整体平均: 8-12秒")

def main():
    """主测试函数"""
    print("=" * 80)
    print("API参数优化验证测试")
    print("=" * 80)
    
    print("\n📈 优化目标:")
    print("  将API响应时间从25-30秒降低到10-15秒")
    print("  性能提升: 2-3倍")
    
    # 比较优化前后
    compare_optimization()
    
    # 运行性能测试
    test_optimized_performance()
    
    print(f"\n{'='*80}")
    print("测试完成")
    print(f"{'='*80}")
    
    print("\n🎯 下一步建议:")
    print("  1. 监控实际生产环境性能")
    print("  2. 根据测试结果调整参数")
    print("  3. 考虑实现查询缓存")
    print("  4. 添加更多性能监控指标")

if __name__ == "__main__":
    main()