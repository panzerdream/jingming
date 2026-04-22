#!/usr/bin/env python3
"""
调试脚本：检查系统各个组件，找出模型答非所问的原因
"""

import os
import sys
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

def check_environment():
    """检查环境配置"""
    print("=" * 60)
    print("1. 检查环境配置")
    print("=" * 60)
    
    # 检查配置文件
    env_file = project_root / "config" / ".env"
    if env_file.exists():
        print(f"✓ 配置文件存在: {env_file}")
        with open(env_file, 'r') as f:
            content = f.read()
            if "BAILIAN_API_KEY" in content:
                print("✓ API密钥已配置")
            else:
                print("✗ API密钥未配置")
    else:
        print(f"✗ 配置文件不存在: {env_file}")
    
    # 检查Python依赖
    try:
        import langchain
        print(f"✓ LangChain版本: {langchain.__version__}")
    except ImportError:
        print("✗ LangChain未安装")
    
    try:
        import requests
        print(f"✓ Requests版本: {requests.__version__}")
    except ImportError:
        print("✗ Requests未安装")

def check_knowledge_base():
    """检查知识库"""
    print("\n" + "=" * 60)
    print("2. 检查知识库")
    print("=" * 60)
    
    knowledge_dir = project_root / "data" / "knowledge"
    if knowledge_dir.exists():
        print(f"✓ 知识库目录存在: {knowledge_dir}")
        
        # 统计文件
        md_files = list(knowledge_dir.rglob("*.md"))
        print(f"✓ 找到 {len(md_files)} 个Markdown文件")
        
        # 检查居民详细目录
        residents_dir = knowledge_dir / "居民详细"
        if residents_dir.exists():
            resident_files = list(residents_dir.glob("*.md"))
            print(f"✓ 居民详细目录包含 {len(resident_files)} 个文件")
            
            # 读取一个示例文件
            if resident_files:
                sample_file = resident_files[0]
                with open(sample_file, 'r', encoding='utf-8') as f:
                    content = f.read(200)
                    print(f"✓ 示例文件内容（前200字符）: {content}")
        else:
            print("✗ 居民详细目录不存在")
    else:
        print(f"✗ 知识库目录不存在: {knowledge_dir}")

def check_vector_store():
    """检查向量存储"""
    print("\n" + "=" * 60)
    print("3. 检查向量存储")
    print("=" * 60)
    
    vector_db_dir = project_root / "data" / "vector_db"
    if vector_db_dir.exists():
        print(f"✓ 向量数据库目录存在: {vector_db_dir}")
        
        # 检查文件
        files = list(vector_db_dir.glob("*"))
        if files:
            print(f"✓ 向量数据库包含 {len(files)} 个文件")
            for f in files:
                print(f"  - {f.name} ({f.stat().st_size} bytes)")
        else:
            print("✗ 向量数据库为空")
    else:
        print(f"✗ 向量数据库目录不存在: {vector_db_dir}")
        print("  需要运行系统以创建向量数据库")

def test_retrieval():
    """测试检索功能"""
    print("\n" + "=" * 60)
    print("4. 测试检索功能")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from src.document_processing.markdown_processor import MarkdownProcessor
        from src.vector_store.vector_store import VectorStoreManager
        
        # 初始化处理器
        knowledge_path = project_root / "data" / "knowledge"
        processor = MarkdownProcessor(str(knowledge_path))
        
        # 测试文档处理
        print("测试文档处理...")
        documents = processor.process_all_documents()
        if documents:
            print(f"✓ 成功处理 {len(documents)} 个文档块")
            
            # 测试向量存储
            vector_path = project_root / "data" / "vector_db"
            vector_manager = VectorStoreManager(str(vector_path))
            
            # 测试检索
            test_queries = [
                "亚历克斯是谁？",
                "星露谷有哪些节日？",
                "如何获得铱矿？"
            ]
            
            for query in test_queries:
                print(f"\n测试查询: '{query}'")
                try:
                    results = vector_manager.search(query, k=3)
                    if results:
                        print(f"✓ 检索到 {len(results)} 个结果")
                        for i, doc in enumerate(results[:2]):  # 只显示前2个
                            print(f"  结果 {i+1}: {doc.page_content[:100]}...")
                    else:
                        print("✗ 未检索到结果")
                except Exception as e:
                    print(f"✗ 检索失败: {e}")
        else:
            print("✗ 未处理到任何文档")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_api_connection():
    """测试API连接"""
    print("\n" + "=" * 60)
    print("5. 测试API连接")
    print("=" * 60)
    
    try:
        from src.api.bailian_api import OptimizedBailianAPI
        
        # 从环境变量获取配置
        import dotenv
        dotenv.load_dotenv(project_root / "config" / ".env")
        
        api_key = os.getenv("BAILIAN_API_KEY")
        api_url = os.getenv("BAILIAN_API_URL")
        
        if api_key and api_key != "your_api_key_here":
            print(f"✓ API密钥已配置")
            print(f"✓ API URL: {api_url}")
            
            # 测试简单API调用
            api = OptimizedBailianAPI(api_key, api_url)
            
            # 测试简单查询
            test_prompt = "你好，请简单介绍一下自己。"
            print(f"测试API调用: '{test_prompt}'")
            
            try:
                response = api.generate(
                    prompt=test_prompt,
                    model_name="qwen-turbo",
                    temperature=0.3,
                    max_tokens=100
                )
                print(f"✓ API响应: {response[:200]}...")
            except Exception as e:
                print(f"✗ API调用失败: {e}")
        else:
            print("✗ API密钥未正确配置")
            
    except Exception as e:
        print(f"✗ API测试失败: {e}")

def test_full_system():
    """测试完整系统"""
    print("\n" + "=" * 60)
    print("6. 测试完整系统")
    print("=" * 60)
    
    try:
        from src.main_optimized import OptimizedAgentRAG
        
        print("初始化系统...")
        agent = OptimizedAgentRAG()
        print("✓ 系统初始化成功")
        
        # 测试查询
        test_queries = [
            ("亚历克斯是谁？", "应该返回亚历克斯的详细信息"),
            ("星露谷有哪些节日？", "应该返回节日列表"),
            ("如何获得铱矿？", "应该返回获取铱矿的方法")
        ]
        
        for query, expected in test_queries:
            print(f"\n测试查询: '{query}'")
            print(f"期望: {expected}")
            
            try:
                response = agent.process_query(query)
                print(f"实际响应: {response[:300]}...")
                
                # 简单检查响应质量
                if len(response) < 10:
                    print("⚠ 响应过短，可能有问题")
                elif "抱歉" in response or "不知道" in response:
                    print("⚠ 系统表示不知道答案")
                else:
                    print("✓ 响应看起来正常")
                    
            except Exception as e:
                print(f"✗ 查询处理失败: {e}")
                
    except Exception as e:
        print(f"✗ 系统测试失败: {e}")
        import traceback
        traceback.print_exc()

def analyze_prompt_template():
    """分析提示词模板"""
    print("\n" + "=" * 60)
    print("7. 分析提示词模板")
    print("=" * 60)
    
    try:
        from src.api.bailian_api import OptimizedBailianAPI
        
        # 创建测试上下文
        test_context = """检索到的相关信息：
亚历克斯是星露谷的居民之一，他住在镇上的房子里。他喜欢运动，特别是美式足球。

会话历史：
user: 你好
assistant: 你好！我是星露谷助手景明。
"""
        
        test_query = "亚历克斯是谁？"
        
        # 模拟上下文构建
        api = OptimizedBailianAPI("test_key", "test_url")
        compressed_context = api._compress_context(test_context, max_length=800)
        
        print("原始上下文:")
        print(test_context)
        print("\n压缩后的上下文:")
        print(compressed_context)
        
        # 显示生成的提示词
        prompt = f"""基于以下信息回答问题：

相关信息：
{compressed_context}

问题：{test_query}

回答："""
        
        print("\n生成的提示词:")
        print(prompt)
        
    except Exception as e:
        print(f"✗ 分析失败: {e}")

def main():
    """主函数"""
    print("开始调试星露谷助手RAG系统...")
    print("=" * 60)
    
    # 执行各项检查
    check_environment()
    check_knowledge_base()
    check_vector_store()
    test_retrieval()
    test_api_connection()
    analyze_prompt_template()
    test_full_system()
    
    print("\n" + "=" * 60)
    print("调试完成！")
    print("=" * 60)
    
    # 总结问题
    print("\n常见问题排查:")
    print("1. API密钥未配置 - 检查config/.env文件")
    print("2. 向量数据库未创建 - 首次运行需要创建向量数据库")
    print("3. 知识库文件为空 - 检查data/knowledge目录")
    print("4. 提示词模板问题 - 检查bailian_api.py中的提示词构建")
    print("5. 检索结果不相关 - 检查向量存储的搜索功能")

if __name__ == "__main__":
    main()