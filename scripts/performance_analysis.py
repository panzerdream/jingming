#!/usr/bin/env python3
"""
性能分析脚本 - 分析系统各组件耗时
"""

import sys
import os
import time
import cProfile
import pstats
from io import StringIO

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def profile_system():
    """分析系统性能"""
    print("🔧 系统性能分析")
    print("=" * 50)
    
    # 导入必要的模块
    from api.bailian_api import OptimizedBailianAPI
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv(dotenv_path='config/.env')
    
    api_key = os.getenv("BAILIAN_API_KEY")
    api_url = os.getenv("BAILIAN_API_URL")
    
    if not api_key:
        print("❌ API密钥未设置")
        return
    
    # 创建API实例
    api = OptimizedBailianAPI(api_key, api_url)
    
    # 测试用例
    test_cases = [
        {
            "name": "简单问候",
            "query": "你好",
            "context": "简单问候测试"
        },
        {
            "name": "工具查询",
            "query": "现在几点",
            "context": "时间查询测试"
        },
        {
            "name": "知识查询",
            "query": "星露谷是什么",
            "context": "星露谷是一款农场模拟角色扮演游戏。"
        }
    ]
    
    for test in test_cases:
        print(f"\n📊 测试: {test['name']}")
        print(f"查询: {test['query']}")
        
        # 使用cProfile进行性能分析
        pr = cProfile.Profile()
        pr.enable()
        
        try:
            start_time = time.time()
            response = api.generate_with_context(
                query=test['query'],
                context=test['context'],
                model_name="qwen3.6-plus"
            )
            elapsed = time.time() - start_time
            
            pr.disable()
            
            # 分析性能数据
            s = StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
            ps.print_stats(10)  # 显示前10个最耗时的函数
            
            print(f"✅ 成功 - 总时间: {elapsed:.2f}秒")
            print(f"响应长度: {len(response)} 字符")
            print(f"响应预览: {response[:80]}...")
            
            # 显示性能分析结果
            print("\n⏱️  性能分析 (前10个最耗时函数):")
            analysis = s.getvalue().split('\n')[:15]
            for line in analysis:
                if line.strip():
                    print(f"  {line}")
                    
        except Exception as e:
            print(f"❌ 失败: {e}")

def analyze_bottlenecks():
    """分析系统瓶颈"""
    print("\n" + "=" * 50)
    print("🔍 系统瓶颈分析")
    print("=" * 50)
    
    print("可能的瓶颈点:")
    print("1. 🔄 向量检索 - 从向量数据库检索相关文档")
    print("2. 🌐 API调用 - 阿里云百炼API响应时间")
    print("3. 🛠️  工具执行 - 工具系统的执行时间")
    print("4. 📝 上下文构建 - 构建API请求的上下文")
    print("5. 🗃️  会话管理 - 维护和检索会话历史")
    
    print("\n💡 优化建议:")
    print("1. 启用向量检索缓存")
    print("2. 进一步优化API参数:")
    print("   - 减少 max_tokens 到 200")
    print("   - 降低 temperature 到 0.2")
    print("   - 启用流式响应")
    print("3. 预加载常用工具")
    print("4. 实现异步处理")
    print("5. 添加响应缓存")

def test_individual_components():
    """测试各个组件"""
    print("\n" + "=" * 50)
    print("🧪 组件级测试")
    print("=" * 50)
    
    # 测试API调用
    print("测试API调用...")
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='config/.env')
    
    api_key = os.getenv("BAILIAN_API_KEY")
    
    if api_key:
        import requests
        import json
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        test_data = {
            "model": "qwen3.6-plus",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 50,
            "temperature": 0.3
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers=headers,
                json=test_data,
                timeout=15
            )
            api_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ 纯API调用时间: {api_time:.2f}秒")
            else:
                print(f"❌ API调用失败: {response.status_code}")
        except Exception as e:
            print(f"❌ API调用错误: {e}")
    else:
        print("⚠️  API密钥未设置")

def main():
    """主函数"""
    print("🚀 Agent RAG系统性能分析")
    print("=" * 50)
    
    # 分析系统性能
    profile_system()
    
    # 分析瓶颈
    analyze_bottlenecks()
    
    # 测试组件
    test_individual_components()
    
    print("\n" + "=" * 50)
    print("分析完成！")

if __name__ == "__main__":
    main()