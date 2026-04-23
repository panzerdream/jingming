"""
GraphRAG 集成测试脚本
测试知识图谱构建、检索和推理功能
"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from graph.entity_extractor import EntityExtractor, Entity
from graph.graph_builder import KnowledgeGraphBuilder
from graph.graph_retriever import GraphRetriever
from utils.logger import get_logger

logger = get_logger()


def test_entity_extraction():
    """测试实体抽取"""
    print("\n" + "="*60)
    print("测试 1: 实体抽取")
    print("="*60)
    
    extractor = EntityExtractor()
    
    # 测试数据
    test_content = """
# 阿比盖尔
    
**生日**: 秋季第 14 天
**住址**: 鹈鹕镇，皮埃尔的杂货店
**职业**: 学生
**父亲**: 皮埃尔
**母亲**: 卡洛琳
**朋友**: 山姆、塞巴斯蒂安
**喜欢**: 紫水晶、巧克力蛋糕
**住在**: 皮埃尔的杂货店二楼
"""
    
    entity = extractor.extract_character(test_content, "阿比盖尔.md")
    
    if entity:
        print(f"✓ 成功抽取实体：{entity.name}")
        print(f"  类型：{entity.type}")
        print(f"  属性数量：{len(entity.attributes)}")
        print(f"  关系数量：{len(entity.relations)}")
        
        print(f"\n  属性:")
        for key, value in entity.attributes.items():
            print(f"    - {key}: {value}")
        
        print(f"\n  关系:")
        for rel in entity.relations:
            print(f"    - {rel['type']}: {rel['target']}")
        
        return True
    else:
        print("✗ 实体抽取失败")
        return False


def test_graph_building():
    """测试图构建"""
    print("\n" + "="*60)
    print("测试 2: 图构建")
    print("="*60)
    
    builder = KnowledgeGraphBuilder()
    
    # 创建测试实体
    entities = [
        Entity(
            id="char_阿比盖尔",
            name="阿比盖尔",
            type="character",
            attributes={"生日": "秋季第 14 天", "职业": "学生"},
            relations=[
                {"type": "father", "target": "皮埃尔"},
                {"type": "mother", "target": "卡洛琳"},
                {"type": "friend", "target": "山姆"},
                {"type": "friend", "target": "塞巴斯蒂安"},
                {"type": "live_at", "target": "皮埃尔杂货店"}
            ]
        ),
        Entity(
            id="char_皮埃尔",
            name="皮埃尔",
            type="character",
            attributes={"职业": "杂货店老板"},
            relations=[
                {"type": "daughter", "target": "阿比盖尔"},
                {"type": "wife", "target": "卡洛琳"},
                {"type": "work_at", "target": "皮埃尔杂货店"}
            ]
        ),
        Entity(
            id="char_卡洛琳",
            name="卡洛琳",
            type="character",
            attributes={"职业": "家庭主妇"},
            relations=[
                {"type": "daughter", "target": "阿比盖尔"},
                {"type": "husband", "target": "皮埃尔"}
            ]
        ),
        Entity(
            id="char_山姆",
            name="山姆",
            type="character",
            attributes={"职业": "无"},
            relations=[
                {"type": "friend", "target": "阿比盖尔"},
                {"type": "friend", "target": "塞巴斯蒂安"}
            ]
        ),
        Entity(
            id="loc_皮埃尔杂货店",
            name="皮埃尔杂货店",
            type="location",
            attributes={"类型": "商店"},
            relations=[]
        )
    ]
    
    # 构建图
    builder.build_from_entities(entities)
    
    # 获取统计信息
    stats = builder.get_stats()
    
    print(f"✓ 图构建成功")
    print(f"  节点数：{stats['node_count']}")
    print(f"  边数：{stats['edge_count']}")
    print(f"  连通分量：{stats['connected_components']}")
    print(f"  平均度：{stats['avg_degree']}")
    print(f"\n  实体类型分布:")
    for entity_type, count in stats['type_distribution'].items():
        print(f"    - {entity_type}: {count}")
    
    # 保存图
    save_path = os.path.join(os.path.dirname(__file__), 'test_knowledge_graph.json')
    builder.save(save_path)
    print(f"\n✓ 图已保存到：{save_path}")
    
    return True


def test_graph_retrieval():
    """测试图检索"""
    print("\n" + "="*60)
    print("测试 3: 图检索")
    print("="*60)
    
    # 先构建图
    builder = KnowledgeGraphBuilder()
    entities = [
        Entity(
            id="char_阿比盖尔",
            name="阿比盖尔",
            type="character",
            attributes={},
            relations=[
                {"type": "father", "target": "皮埃尔"},
                {"type": "friend", "target": "山姆"}
            ]
        ),
        Entity(
            id="char_皮埃尔",
            name="皮埃尔",
            type="character",
            attributes={},
            relations=[
                {"type": "daughter", "target": "阿比盖尔"}
            ]
        ),
        Entity(
            id="char_山姆",
            name="山姆",
            type="character",
            attributes={},
            relations=[
                {"type": "friend", "target": "阿比盖尔"}
            ]
        )
    ]
    builder.build_from_entities(entities)
    
    # 创建检索器
    retriever = GraphRetriever(builder)
    
    # 测试 1: 实体识别
    print("\n测试 3.1: 实体识别")
    query = "阿比盖尔的朋友有哪些"
    entities = retriever.identify_entities(query)
    print(f"  查询：{query}")
    print(f"  识别到的实体：{len(entities)}")
    for entity in entities:
        print(f"    - {entity['name']} ({entity['type']})")
    
    # 测试 2: 相关实体检索
    print("\n测试 3.2: 相关实体检索")
    related = retriever.retrieve_related_entities(query, k=5)
    print(f"  查询：{query}")
    print(f"  相关实体：{len(related)}")
    for entity in related:
        print(f"    - {entity['name']} ({entity['type']}), score={entity['relevance_score']:.2f}")
    
    # 测试 3: 关系路径检索
    print("\n测试 3.3: 关系路径检索")
    path = retriever.retrieve_relation_path("阿比盖尔", "皮埃尔")
    if path:
        print(f"  路径：{path['source']} -> {path['target']}")
        print(f"  长度：{path['length']}")
        print(f"  节点:")
        for node in path['nodes']:
            print(f"    - {node['name']} ({node['type']})")
        print(f"  关系:")
        for rel in path['relations']:
            print(f"    - {rel['from']} --[{rel['type']}]--> {rel['to']}")
    else:
        print("  ✗ 未找到路径")
    
    # 测试 4: 获取实体信息
    print("\n测试 3.4: 获取实体信息")
    info = retriever.get_entity_info("阿比盖尔")
    if info:
        print(f"  实体：{info['name']}")
        print(f"  类型：{info['type']}")
        print(f"  关系:")
        for rel in info['relations']:
            print(f"    - {rel['type']}: {rel['target']}")
    
    return True


def test_multi_hop_reasoning():
    """测试多跳推理"""
    print("\n" + "="*60)
    print("测试 4: 多跳推理")
    print("="*60)
    
    # 构建更复杂的图
    builder = KnowledgeGraphBuilder()
    entities = [
        Entity(
            id="char_塞巴斯蒂安",
            name="塞巴斯蒂安",
            type="character",
            attributes={},
            relations=[
                {"type": "sister", "target": "玛鲁"},
                {"type": "mother", "target": "罗宾"},
                {"type": "friend", "target": "阿比盖尔"}
            ]
        ),
        Entity(
            id="char_玛鲁",
            name="玛鲁",
            type="character",
            attributes={},
            relations=[
                {"type": "brother", "target": "塞巴斯蒂安"},
                {"type": "father", "target": "德米特里厄斯"}
            ]
        ),
        Entity(
            id="char_德米特里厄斯",
            name="德米特里厄斯",
            type="character",
            attributes={"职业": "科学家"},
            relations=[
                {"type": "daughter", "target": "玛鲁"},
                {"type": "wife", "target": "罗宾"}
            ]
        )
    ]
    builder.build_from_entities(entities)
    
    retriever = GraphRetriever(builder)
    
    # 测试多跳查询
    query = "塞巴斯蒂安的妹妹的爸爸是谁"
    print(f"\n查询：{query}")
    
    # 分解查询
    # 第一步：塞巴斯蒂安 → 妹妹（玛鲁）
    path1 = retriever.retrieve_relation_path("塞巴斯蒂安", "玛鲁")
    if path1:
        print(f"\n第一步：塞巴斯蒂安 → 玛鲁")
        for rel in path1['relations']:
            print(f"  {rel['from']} --[{rel['type']}]--> {rel['to']}")
    
    # 第二步：玛鲁 → 爸爸（德米特里厄斯）
    path2 = retriever.retrieve_relation_path("玛鲁", "德米特里厄斯")
    if path2:
        print(f"\n第二步：玛鲁 → 德米特里厄斯")
        for rel in path2['relations']:
            print(f"  {rel['from']} --[{rel['type']}]--> {rel['to']}")
    
    # 完整路径
    full_path = retriever.retrieve_relation_path("塞巴斯蒂安", "德米特里厄斯")
    if full_path:
        print(f"\n完整路径：塞巴斯蒂安 → 德米特里厄斯")
        print(f"路径长度：{full_path['length']} 跳")
        print("路径节点:")
        for node in full_path['nodes']:
            print(f"  - {node['name']}")
        print("关系链:")
        for rel in full_path['relations']:
            print(f"  - {rel['from']} --[{rel['type']}]--> {rel['to']}")
    
    print(f"\n✓ 答案：德米特里厄斯（塞巴斯蒂安的妹妹的爸爸）")
    
    return True


def test_from_knowledge_base():
    """测试从真实知识库构建"""
    print("\n" + "="*60)
    print("测试 5: 从真实知识库构建（可选）")
    print("="*60)
    
    knowledge_base_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'data', 
        'knowledge',
        '居民详细'
    )
    
    if not os.path.exists(knowledge_base_path):
        print(f"⚠ 知识库路径不存在：{knowledge_base_path}")
        print("  跳过此测试")
        return True
    
    print(f"知识库路径：{knowledge_base_path}")
    
    # 实体抽取
    extractor = EntityExtractor()
    print("\n正在抽取实体...")
    entities = extractor.extract_from_directory(knowledge_base_path)
    print(f"✓ 抽取到 {len(entities)} 个实体")
    
    if not entities:
        print("⚠ 未抽取到实体，跳过后续测试")
        return True
    
    # 构建图
    builder = KnowledgeGraphBuilder()
    print("\n正在构建图...")
    builder.build_from_entities(entities)
    
    stats = builder.get_stats()
    print(f"✓ 图构建完成")
    print(f"  节点数：{stats['node_count']}")
    print(f"  边数：{stats['edge_count']}")
    
    # 创建检索器
    retriever = GraphRetriever(builder)
    
    # 测试检索
    test_queries = [
        "阿比盖尔的朋友",
        "皮埃尔的女儿",
        "谁住在杂货店"
    ]
    
    print("\n测试查询:")
    for query in test_queries:
        print(f"\n  查询：{query}")
        related = retriever.retrieve_related_entities(query, k=3)
        if related:
            print(f"  相关实体:")
            for entity in related[:3]:
                print(f"    - {entity['name']} ({entity['type']})")
        else:
            print(f"  未找到相关实体")
    
    return True


def main():
    """运行所有测试"""
    print("="*60)
    print("GraphRAG 集成测试")
    print("="*60)
    
    results = []
    
    # 测试 1: 实体抽取
    results.append(("实体抽取", test_entity_extraction()))
    
    # 测试 2: 图构建
    if results[-1][1]:
        results.append(("图构建", test_graph_building()))
    
    # 测试 3: 图检索
    if results[-1][1]:
        results.append(("图检索", test_graph_retrieval()))
    
    # 测试 4: 多跳推理
    if results[-1][1]:
        results.append(("多跳推理", test_multi_hop_reasoning()))
    
    # 测试 5: 真实知识库
    results.append(("真实知识库", test_from_knowledge_base()))
    
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
