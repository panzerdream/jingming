"""
GraphRAG 集成测试
测试完整的 GraphRAG 功能集成到主系统
"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main_optimized import OptimizedAgentRAG
from utils.logger import get_logger

logger = get_logger()


def test_graphrag_initialization():
    """测试 GraphRAG 初始化"""
    print("\n" + "="*60)
    print("测试 1: GraphRAG 初始化")
    print("="*60)
    
    try:
        agent = OptimizedAgentRAG()
        
        print(f"✓ AgentRAG 初始化成功")
        print(f"  - 模型：{agent.model_name}")
        print(f"  - GraphRAG 启用：{agent.use_graphrag}")
        
        if agent.use_graphrag:
            stats = agent.get_graph_stats()
            print(f"\n  知识图谱统计:")
            print(f"    - 节点数：{stats.get('node_count', 0)}")
            print(f"    - 边数：{stats.get('edge_count', 0)}")
            print(f"    - 连通分量：{stats.get('connected_components', 0)}")
            print(f"    - 平均度：{stats.get('avg_degree', 0)}")
        else:
            print(f"⚠ GraphRAG 未启用")
        
        return True
        
    except Exception as e:
        print(f"✗ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_entity_query():
    """测试实体查询"""
    print("\n" + "="*60)
    print("测试 2: 实体查询")
    print("="*60)
    
    try:
        agent = OptimizedAgentRAG()
        
        if not agent.use_graphrag:
            print("⚠ GraphRAG 未启用，跳过测试")
            return True
        
        # 测试查询
        test_queries = [
            "阿比盖尔是谁",
            "皮埃尔的女儿喜欢什么",
            "塞巴斯蒂安的朋友有哪些"
        ]
        
        for query in test_queries:
            print(f"\n查询：{query}")
            
            # 处理查询
            response = agent.process_query(query)
            print(f"回复：{response[:200]}...")
            
            # 获取实体信息
            if "阿比盖尔" in query:
                entity_info = agent.get_entity_info("阿比盖尔")
                if entity_info:
                    print(f"实体信息:")
                    print(f"  - 名称：{entity_info.get('name')}")
                    print(f"  - 类型：{entity_info.get('type')}")
                    print(f"  - 关系数：{len(entity_info.get('relations', []))}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_relation_path():
    """测试关系路径查询"""
    print("\n" + "="*60)
    print("测试 3: 关系路径查询")
    print("="*60)
    
    try:
        agent = OptimizedAgentRAG()
        
        if not agent.use_graphrag:
            print("⚠ GraphRAG 未启用，跳过测试")
            return True
        
        # 测试关系路径
        test_paths = [
            ("阿比盖尔", "皮埃尔"),
            ("塞巴斯蒂安", "玛鲁"),
        ]
        
        for source, target in test_paths:
            print(f"\n查找路径：{source} → {target}")
            
            path = agent.find_relation_path(source, target)
            
            if path:
                print(f"✓ 找到路径，长度：{path.get('length', 0)}")
                print(f"节点:")
                for node in path.get('nodes', []):
                    print(f"  - {node.get('name')} ({node.get('type')})")
                print(f"关系:")
                for rel in path.get('relations', []):
                    print(f"  - {rel.get('from')} --[{rel.get('type')}]--> {rel.get('to')}")
            else:
                print(f"✗ 未找到路径")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_hop_query():
    """测试多跳查询"""
    print("\n" + "="*60)
    print("测试 4: 多跳查询")
    print("="*60)
    
    try:
        agent = OptimizedAgentRAG()
        
        if not agent.use_graphrag:
            print("⚠ GraphRAG 未启用，跳过测试")
            return True
        
        # 多跳查询
        query = "塞巴斯蒂安的妹妹的爸爸是谁"
        print(f"查询：{query}")
        
        response = agent.process_query(query)
        print(f"回复：{response[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_search():
    """测试混合检索"""
    print("\n" + "="*60)
    print("测试 5: 混合检索（向量 + 图）")
    print("="*60)
    
    try:
        agent = OptimizedAgentRAG()
        
        if not agent.use_graphrag:
            print("⚠ GraphRAG 未启用，跳过测试")
            return True
        
        # 测试查询
        query = "阿比盖尔喜欢什么礼物"
        print(f"查询：{query}")
        
        response = agent.process_query(query)
        print(f"回复：{response[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("GraphRAG 集成测试")
    print("="*60)
    
    results = []
    
    # 测试 1: 初始化
    results.append(("GraphRAG 初始化", test_graphrag_initialization()))
    
    # 测试 2: 实体查询
    if results[-1][1]:
        results.append(("实体查询", test_entity_query()))
    
    # 测试 3: 关系路径
    if results[-1][1]:
        results.append(("关系路径", test_relation_path()))
    
    # 测试 4: 多跳查询
    if results[-1][1]:
        results.append(("多跳查询", test_multi_hop_query()))
    
    # 测试 5: 混合检索
    if results[-1][1]:
        results.append(("混合检索", test_hybrid_search()))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
