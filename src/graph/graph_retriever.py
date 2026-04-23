"""
图检索器
基于知识图谱进行实体检索和关系推理
"""
import re
from typing import Dict, List, Tuple, Optional, Any, Set
from .graph_builder import KnowledgeGraphBuilder
from .entity_extractor import Entity, EntityExtractor

# 导入日志模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger()


class GraphRetriever:
    """图检索器"""
    
    def __init__(self, graph_builder: KnowledgeGraphBuilder = None):
        """
        初始化图检索器
        
        Args:
            graph_builder: 知识图谱构建器实例
        """
        self.graph_builder = graph_builder
        self.graph = graph_builder.graph if graph_builder else None
        
        # 实体识别模式
        self.entity_patterns = self._compile_entity_patterns()
        
        logger.info("GraphRetriever initialized")
    
    def _compile_entity_patterns(self) -> Dict[str, re.Pattern]:
        """编译实体识别正则表达式"""
        patterns = {}
        
        # 人物名称模式（中文名字）
        patterns['person'] = re.compile(
            r'([A-Z][a-z]*|[A-Z]{2,}|[\u4e00-\u9fa5]{2,4})'
        )
        
        # 查询中的实体提及模式
        patterns['entity_mention'] = re.compile(
            r'(?:的 | 是 | 有 | 在 | 和 | 与|跟 | 同)([\u4e00-\u9fa5A-Za-z]+?)(?:的 | 朋友 | 家人 | 爸爸 | 妈妈 | 女儿 | 儿子 | 工作 | 住 | 喜欢|爱)'
        )
        
        return patterns
    
    def set_graph(self, graph_builder: KnowledgeGraphBuilder) -> None:
        """
        设置知识图谱
        
        Args:
            graph_builder: 知识图谱构建器
        """
        self.graph_builder = graph_builder
        self.graph = graph_builder.graph
        logger.info("Graph updated")
    
    def identify_entities(self, query: str) -> List[Dict[str, str]]:
        """
        从查询中识别实体
        
        Args:
            query: 用户查询
            
        Returns:
            识别到的实体列表 [{"name": str, "type": str, "confidence": float}, ...]
        """
        entities = []
        
        # 简单实现：基于规则匹配
        # 实际应该使用 NER 模型
        
        # 查找可能的人名
        matches = self.entity_patterns['person'].findall(query)
        for match in matches:
            # 检查是否是已知实体
            entity_id = self._find_entity_by_name(match)
            if entity_id:
                entity_data = self.graph.nodes[entity_id]
                entities.append({
                    "name": match,
                    "type": entity_data.get('type', 'unknown'),
                    "id": entity_id,
                    "confidence": 0.9
                })
        
        logger.debug(f"Identified {len(entities)} entities in query: {query}")
        return entities
    
    def _find_entity_by_name(self, name: str) -> Optional[str]:
        """
        根据名称查找实体 ID
        
        Args:
            name: 实体名称
            
        Returns:
            实体 ID，未找到返回 None
        """
        if not self.graph:
            return None
        
        for node_id, data in self.graph.nodes(data=True):
            if data.get('name') == name:
                return node_id
        
        return None
    
    def retrieve_related_entities(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        检索与查询相关的实体
        
        Args:
            query: 用户查询
            k: 返回数量
            
        Returns:
            相关实体列表
        """
        # 1. 识别查询中的实体
        query_entities = self.identify_entities(query)
        
        if not query_entities:
            logger.debug("No entities identified in query")
            return []
        
        # 2. 获取这些实体的邻居
        related = []
        seen_ids = set()
        
        for entity in query_entities:
            entity_id = entity['id']
            
            # 获取 k 跳邻居
            neighbors = self.graph_builder.get_neighbors(entity_id, k=2)
            
            for neighbor_id, neighbor_data in neighbors:
                if neighbor_id not in seen_ids:
                    seen_ids.add(neighbor_id)
                    
                    # 计算相关性分数
                    relevance_score = self._calculate_relevance(
                        entity_id, neighbor_id, query
                    )
                    
                    related.append({
                        "id": neighbor_id,
                        "name": neighbor_data.get('name'),
                        "type": neighbor_data.get('type'),
                        "attributes": neighbor_data.get('attributes', {}),
                        "relevance_score": relevance_score
                    })
        
        # 3. 按相关性排序
        related.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # 4. 返回 Top K
        return related[:k]
    
    def _calculate_relevance(self, source_id: str, target_id: str, 
                            query: str) -> float:
        """
        计算实体相关性分数
        
        Args:
            source_id: 源实体 ID
            target_id: 目标实体 ID
            query: 用户查询
            
        Returns:
            相关性分数 (0-1)
        """
        score = 0.5  # 基础分
        
        # 因素 1: 距离越近分数越高
        try:
            path = nx.shortest_path(self.graph, source=source_id, target=target_id)
            distance = len(path) - 1
            
            if distance == 1:
                score += 0.3
            elif distance == 2:
                score += 0.2
            elif distance == 3:
                score += 0.1
        except:
            pass
        
        # 因素 2: 关系类型匹配查询意图
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['朋友', '好友']):
            # 检查是否有朋友关系
            if self._has_relation_type(source_id, target_id, 'friend'):
                score += 0.2
        
        if any(word in query_lower for word in ['爸爸', '父亲', '妈妈', '母亲', '女儿', '儿子']):
            # 检查是否有家庭关系
            if self._has_relation_type(source_id, target_id, 'family'):
                score += 0.2
        
        if any(word in query_lower for word in ['工作', '上班']):
            # 检查工作关系
            if self._has_relation_type(source_id, target_id, 'work_at'):
                score += 0.2
        
        if any(word in query_lower for word in ['喜欢', '爱']):
            # 检查喜好关系
            if self._has_relation_type(source_id, target_id, 'like'):
                score += 0.2
        
        return min(score, 1.0)
    
    def _has_relation_type(self, source_id: str, target_id: str, 
                          relation_type: str) -> bool:
        """
        检查两个实体之间是否有指定类型的关系
        
        Args:
            source_id: 源实体 ID
            target_id: 目标实体 ID
            relation_type: 关系类型
            
        Returns:
            bool: 是否存在该关系
        """
        if not self.graph.has_edge(source_id, target_id):
            return False
        
        edge_data = self.graph.get_edge_data(source_id, target_id)
        return edge_data.get('type') == relation_type
    
    def retrieve_relation_path(self, source_name: str, target_name: str) -> Optional[Dict[str, Any]]:
        """
        检索两个实体之间的关系路径
        
        Args:
            source_name: 源实体名称
            target_name: 目标实体名称
            
        Returns:
            路径信息 {"path": [...], "relations": [...]} 或 None
        """
        # 查找实体 ID
        source_id = self._find_entity_by_name(source_name)
        target_id = self._find_entity_by_name(target_name)
        
        if not source_id or not target_id:
            logger.warning(f"Entity not found: {source_name} or {target_name}")
            return None
        
        # 获取最短路径
        path = self.graph_builder.get_relation_path(source_id, target_id)
        
        if not path:
            return None
        
        # 构建路径信息
        path_info = {
            "source": source_name,
            "target": target_name,
            "nodes": [],
            "relations": [],
            "length": len(path) - 1
        }
        
        # 添加节点信息
        for node_id in path:
            node_data = self.graph.nodes[node_id]
            path_info["nodes"].append({
                "id": node_id,
                "name": node_data.get('name'),
                "type": node_data.get('type')
            })
        
        # 添加关系信息
        for i in range(len(path) - 1):
            edge_data = self.graph.get_edge_data(path[i], path[i+1])
            path_info["relations"].append({
                "from": self.graph.nodes[path[i]].get('name'),
                "to": self.graph.nodes[path[i+1]].get('name'),
                "type": edge_data.get('type')
            })
        
        logger.debug(f"Found relation path: {source_name} -> {target_name}, length={len(path)-1}")
        return path_info
    
    def retrieve_all_paths(self, source_name: str, target_name: str, 
                          max_length: int = 3) -> List[Dict[str, Any]]:
        """
        检索两个实体之间的所有路径
        
        Args:
            source_name: 源实体名称
            target_name: 目标实体名称
            max_length: 最大路径长度
            
        Returns:
            所有路径列表
        """
        source_id = self._find_entity_by_name(source_name)
        target_id = self._find_entity_by_name(target_name)
        
        if not source_id or not target_id:
            return []
        
        paths = self.graph_builder.get_all_paths(source_id, target_id, cutoff=max_length)
        
        result = []
        for path in paths:
            path_info = {
                "nodes": [],
                "relations": [],
                "length": len(path) - 1
            }
            
            for node_id in path:
                node_data = self.graph.nodes[node_id]
                path_info["nodes"].append({
                    "id": node_id,
                    "name": node_data.get('name'),
                    "type": node_data.get('type')
                })
            
            for i in range(len(path) - 1):
                edge_data = self.graph.get_edge_data(path[i], path[i+1])
                path_info["relations"].append({
                    "from": self.graph.nodes[path[i]].get('name'),
                    "to": self.graph.nodes[path[i+1]].get('name'),
                    "type": edge_data.get('type')
                })
            
            result.append(path_info)
        
        logger.debug(f"Found {len(result)} paths between {source_name} and {target_name}")
        return result
    
    def hybrid_retrieve(self, query: str, vector_results: List = None, 
                       k: int = 10) -> List[Dict[str, Any]]:
        """
        混合检索：结合向量检索和图检索
        
        Args:
            query: 用户查询
            vector_results: 向量检索结果
            k: 返回数量
            
        Returns:
            混合检索结果
        """
        # 1. 图检索
        graph_results = self.retrieve_related_entities(query, k=k)
        
        # 2. 如果没有向量结果，只返回图检索结果
        if not vector_results:
            return graph_results
        
        # 3. 合并结果
        merged = {}
        
        # 添加图检索结果
        for result in graph_results:
            key = result.get('name', result.get('id'))
            merged[key] = {
                **result,
                "source": "graph",
                "graph_score": result.get('relevance_score', 0.5)
            }
        
        # 添加向量检索结果（如果不在图中）
        for doc in vector_results:
            # 尝试从文档中提取实体名称
            # 这里简化处理，实际应该解析文档内容
            doc_key = doc.page_content[:50] if hasattr(doc, 'page_content') else str(doc)
            
            if doc_key not in merged:
                merged[doc_key] = {
                    "content": doc.page_content if hasattr(doc, 'page_content') else str(doc),
                    "source": "vector",
                    "vector_score": 1.0,  # 假设向量检索分数
                    "type": "document"
                }
        
        # 4. 转换为列表并排序
        results = list(merged.values())
        results.sort(
            key=lambda x: x.get('graph_score', x.get('vector_score', 0)),
            reverse=True
        )
        
        logger.debug(f"Hybrid retrieval: {len(results)} results (graph: {len(graph_results)}, vector: {len(vector_results) if vector_results else 0})")
        return results[:k]
    
    def get_entity_info(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        获取实体详细信息
        
        Args:
            entity_name: 实体名称
            
        Returns:
            实体信息字典
        """
        entity_id = self._find_entity_by_name(entity_name)
        
        if not entity_id:
            return None
        
        node_data = self.graph.nodes[entity_id]
        
        # 获取邻居
        neighbors = self.graph_builder.get_neighbors(entity_id, k=1)
        
        # 构建关系列表
        relations = []
        for neighbor_id, neighbor_data in neighbors:
            edge_data = self.graph.get_edge_data(entity_id, neighbor_id)
            relations.append({
                "type": edge_data.get('type', 'related_to'),
                "target": neighbor_data.get('name'),
                "target_type": neighbor_data.get('type')
            })
        
        return {
            "id": entity_id,
            "name": node_data.get('name'),
            "type": node_data.get('type'),
            "attributes": node_data.get('attributes', {}),
            "relations": relations
        }


# 测试函数
def test_retriever():
    """测试图检索器"""
    from graph_builder import KnowledgeGraphBuilder
    from entity_extractor import Entity
    
    # 创建图和检索器
    builder = KnowledgeGraphBuilder()
    
    # 创建测试实体
    entities = [
        Entity(
            id="char_阿比盖尔",
            name="阿比盖尔",
            type="character",
            attributes={"生日": "秋季第 14 天"},
            relations=[
                {"type": "father", "target": "皮埃尔"},
                {"type": "mother", "target": "卡洛琳"},
                {"type": "friend", "target": "山姆"},
                {"type": "friend", "target": "塞巴斯蒂安"}
            ]
        ),
        Entity(
            id="char_皮埃尔",
            name="皮埃尔",
            type="character",
            attributes={"职业": "杂货店老板"},
            relations=[
                {"type": "daughter", "target": "阿比盖尔"},
                {"type": "wife", "target": "卡洛琳"}
            ]
        ),
        Entity(
            id="char_山姆",
            name="山姆",
            type="character",
            attributes={"职业": "无"},
            relations=[
                {"type": "friend", "target": "阿比盖尔"}
            ]
        )
    ]
    
    builder.build_from_entities(entities)
    retriever = GraphRetriever(builder)
    
    # 测试 1: 实体识别
    print("\n=== 测试实体识别 ===")
    query = "阿比盖尔的朋友有哪些"
    entities = retriever.identify_entities(query)
    print(f"查询：{query}")
    print(f"识别到的实体：{entities}")
    
    # 测试 2: 相关实体检索
    print("\n=== 测试相关实体检索 ===")
    related = retriever.retrieve_related_entities(query, k=5)
    print(f"相关实体:")
    for entity in related:
        print(f"  - {entity['name']} ({entity['type']}), score={entity['relevance_score']:.2f}")
    
    # 测试 3: 关系路径检索
    print("\n=== 测试关系路径检索 ===")
    path = retriever.retrieve_relation_path("阿比盖尔", "皮埃尔")
    if path:
        print(f"路径：{path['source']} -> {path['target']}")
        print(f"长度：{path['length']}")
        print("节点:")
        for node in path['nodes']:
            print(f"  - {node['name']} ({node['type']})")
        print("关系:")
        for rel in path['relations']:
            print(f"  - {rel['from']} --[{rel['type']}]--> {rel['to']}")
    
    # 测试 4: 获取实体信息
    print("\n=== 测试获取实体信息 ===")
    info = retriever.get_entity_info("阿比盖尔")
    if info:
        print(f"实体：{info['name']}")
        print(f"类型：{info['type']}")
        print(f"属性：{info['attributes']}")
        print(f"关系:")
        for rel in info['relations']:
            print(f"  - {rel['type']}: {rel['target']}")
    
    return retriever


if __name__ == "__main__":
    import networkx as nx
    test_retriever()
