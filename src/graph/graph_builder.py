"""
知识图谱构建器
从实体列表构建 NetworkX 图，支持可视化和持久化
"""
import networkx as nx
import os
import json
import time
from typing import Dict, List, Tuple, Optional, Any, Set
from .entity_extractor import Entity, EntityExtractor

# 导入日志模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger()


class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.entity_map: Dict[str, Entity] = {}
        self.relation_count = 0
        
        # 实体类型颜色映射（用于可视化）
        self.type_colors = {
            "character": "#FF6B6B",  # 红色
            "item": "#4ECDC4",       # 青色
            "festival": "#45B7D1",   # 蓝色
            "location": "#96CEB4"    # 绿色
        }
    
    def add_entity(self, entity: Entity) -> None:
        """
        添加实体节点到图中
        
        Args:
            entity: 实体对象
        """
        node_id = entity.id
        
        # 添加节点
        self.graph.add_node(
            node_id,
            name=entity.name,
            type=entity.type,
            attributes=entity.attributes,
            label=f"{entity.name}\n({entity.type})"
        )
        
        # 保存到实体映射
        self.entity_map[node_id] = entity
        
        logger.debug(f"Added entity node: {node_id} ({entity.name})")
    
    def add_relation(self, source_id: str, target_id: str, 
                     relation_type: str, properties: Dict = None) -> bool:
        """
        添加关系到图中
        
        Args:
            source_id: 源实体 ID
            target_id: 目标实体 ID
            relation_type: 关系类型
            properties: 关系属性
            
        Returns:
            bool: 添加成功返回 True
        """
        # 检查节点是否存在
        if source_id not in self.graph.nodes:
            logger.warning(f"Source node not found: {source_id}")
            return False
        
        if target_id not in self.graph.nodes:
            logger.warning(f"Target node not found: {target_id}")
            return False
        
        # 添加边
        edge_properties = properties or {}
        edge_properties['type'] = relation_type
        
        self.graph.add_edge(
            source_id,
            target_id,
            **edge_properties
        )
        
        self.relation_count += 1
        logger.debug(f"Added relation: {source_id} --[{relation_type}]--> {target_id}")
        return True
    
    def build_from_entities(self, entities: List[Entity]) -> None:
        """
        从实体列表构建图
        
        Args:
            entities: 实体列表
        """
        logger.info(f"Building graph from {len(entities)} entities...")
        start_time = time.time()
        
        # 第一步：添加所有实体节点
        for entity in entities:
            self.add_entity(entity)
        
        # 第二步：添加关系
        for entity in entities:
            source_id = entity.id
            
            for relation in entity.relations:
                relation_type = relation.get('type', 'related_to')
                target_name = relation.get('target', '')
                
                # 尝试找到目标实体
                target_id = self._find_entity_id_by_name(target_name)
                
                if target_id:
                    # 添加关系边
                    self.add_relation(
                        source_id,
                        target_id,
                        relation_type,
                        relation
                    )
                else:
                    # 目标实体不存在，创建一个虚拟节点
                    target_type = self._infer_entity_type(target_name)
                    virtual_entity = Entity(
                        id=f"unknown_{target_name}",
                        name=target_name,
                        type=target_type,
                        attributes={"virtual": True}
                    )
                    self.add_entity(virtual_entity)
                    self.add_relation(source_id, virtual_entity.id, relation_type, relation)
        
        execution_time = time.time() - start_time
        logger.info(
            f"Graph built successfully: "
            f"{self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges, "
            f"in {execution_time:.2f}s"
        )
    
    def _find_entity_id_by_name(self, name: str) -> Optional[str]:
        """
        根据名称查找实体 ID
        
        Args:
            name: 实体名称
            
        Returns:
            实体 ID，未找到返回 None
        """
        # 直接匹配
        for node_id, data in self.graph.nodes(data=True):
            if data.get('name') == name:
                return node_id
        
        # 模糊匹配（去除空格等）
        name_clean = name.strip()
        for node_id, data in self.graph.nodes(data=True):
            if data.get('name', '').strip() == name_clean:
                return node_id
        
        return None
    
    def _infer_entity_type(self, name: str) -> str:
        """
        根据名称推断实体类型
        
        Args:
            name: 实体名称
            
        Returns:
            推断的类型
        """
        # 简单启发式规则
        location_keywords = ['镇', '森林', '矿洞', '海滩', '农场', '屋', '店', '酒吧']
        item_keywords = ['剑', '矿石', '作物', '鱼', '工具', '礼物']
        
        for keyword in location_keywords:
            if keyword in name:
                return "location"
        
        for keyword in item_keywords:
            if keyword in name:
                return "item"
        
        # 默认是人物
        return "character"
    
    def build_from_directory(self, knowledge_base_path: str) -> None:
        """
        从知识库目录构建图
        
        Args:
            knowledge_base_path: 知识库目录路径
        """
        logger.info(f"Building graph from knowledge base: {knowledge_base_path}")
        
        # 使用实体抽取器提取实体
        extractor = EntityExtractor()
        entities = extractor.extract_from_directory(knowledge_base_path)
        
        # 构建图
        self.build_from_entities(entities)
    
    def get_neighbors(self, entity_id: str, k: int = 2) -> List[Tuple[str, Dict]]:
        """
        获取实体的 k 跳邻居
        
        Args:
            entity_id: 实体 ID
            k: 跳数
            
        Returns:
            邻居节点列表 [(node_id, data), ...]
        """
        if entity_id not in self.graph:
            logger.warning(f"Entity not found: {entity_id}")
            return []
        
        # 获取 k 跳邻居
        neighbors = list(nx.single_source_shortest_path_length(
            self.graph, 
            entity_id, 
            cutoff=k
        ).keys())
        
        # 移除自身
        neighbors.remove(entity_id)
        
        # 返回节点及其数据
        result = [(nid, dict(self.graph.nodes[nid])) for nid in neighbors]
        return result
    
    def get_relation_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """
        获取两个实体之间的关系路径
        
        Args:
            source_id: 源实体 ID
            target_id: 目标实体 ID
            
        Returns:
            路径节点列表，无路径返回 None
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None
        
        try:
            path = nx.shortest_path(self.graph, source=source_id, target=target_id)
            return path
        except nx.NetworkXNoPath:
            logger.debug(f"No path found between {source_id} and {target_id}")
            return None
    
    def get_all_paths(self, source_id: str, target_id: str, 
                      cutoff: int = 3) -> List[List[str]]:
        """
        获取两个实体之间的所有路径
        
        Args:
            source_id: 源实体 ID
            target_id: 目标实体 ID
            cutoff: 最大路径长度
            
        Returns:
            所有路径列表
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []
        
        try:
            paths = list(nx.all_simple_paths(
                self.graph, 
                source=source_id, 
                target=target_id,
                cutoff=cutoff
            ))
            return paths
        except Exception as e:
            logger.error(f"Failed to find paths: {e}")
            return []
    
    def visualize(self, output_path: str = "knowledge_graph.png") -> bool:
        """
        可视化知识图谱
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 成功返回 True
        """
        try:
            import graphviz
            
            # 创建 graphviz 图
            dot = graphviz.Digraph(comment='Knowledge Graph')
            dot.attr(rankdir='LR', size='12,8')
            
            # 添加节点
            for node_id, data in self.graph.nodes(data=True):
                node_type = data.get('type', 'unknown')
                node_name = data.get('name', node_id)
                color = self.type_colors.get(node_type, '#999999')
                
                # 节点标签
                label = f"{node_name}\\n({node_type})"
                
                dot.node(
                    node_id,
                    label=label,
                    style='filled',
                    fillcolor=color,
                    fontcolor='white'
                )
            
            # 添加边
            for source, target, data in self.graph.edges(data=True):
                relation_type = data.get('type', 'related_to')
                dot.edge(source, target, label=relation_type, fontsize='10')
            
            # 渲染并保存
            dot.render(output_path, format='png', cleanup=True)
            
            logger.info(f"Graph visualized and saved to {output_path}.png")
            return True
            
        except ImportError:
            logger.error("graphviz not installed, cannot visualize graph")
            return False
        except Exception as e:
            logger.error(f"Failed to visualize graph: {e}")
            return False
    
    def save(self, filepath: str) -> bool:
        """
        保存图到文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 成功返回 True
        """
        try:
            # 保存图数据为 JSON
            graph_data = {
                "nodes": [],
                "edges": [],
                "stats": {
                    "node_count": self.graph.number_of_nodes(),
                    "edge_count": self.graph.number_of_edges(),
                    "build_time": time.time()
                }
            }
            
            # 序列化节点
            for node_id, data in self.graph.nodes(data=True):
                node_data = {
                    "id": node_id,
                    "name": data.get('name'),
                    "type": data.get('type'),
                    "attributes": data.get('attributes', {})
                }
                graph_data["nodes"].append(node_data)
            
            # 序列化边
            for source, target, data in self.graph.edges(data=True):
                edge_data = {
                    "source": source,
                    "target": target,
                    "type": data.get('type'),
                    "properties": {k: v for k, v in data.items() if k != 'type'}
                }
                graph_data["edges"].append(edge_data)
            
            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Graph saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
            return False
    
    def load(self, filepath: str) -> bool:
        """
        从文件加载图
        
        Args:
            filepath: 文件路径
            
        Returns:
            bool: 成功返回 True
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # 清空当前图
            self.graph.clear()
            self.entity_map.clear()
            self.relation_count = 0
            
            # 加载节点
            for node_data in graph_data["nodes"]:
                node_id = node_data["id"]
                entity = Entity(
                    id=node_id,
                    name=node_data.get("name", node_id),
                    type=node_data.get("type", "unknown"),
                    attributes=node_data.get("attributes", {})
                )
                self.add_entity(entity)
            
            # 加载边
            for edge_data in graph_data["edges"]:
                self.add_relation(
                    edge_data["source"],
                    edge_data["target"],
                    edge_data.get("type", "related_to"),
                    edge_data.get("properties", {})
                )
            
            logger.info(f"Graph loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取图统计信息
        
        Returns:
            dict: 统计信息
        """
        # 计算连通分量
        connected_components = list(nx.connected_components(self.graph))
        
        # 计算度分布
        degrees = [d for n, d in self.graph.degree()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        
        # 实体类型分布
        type_distribution = {}
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            type_distribution[node_type] = type_distribution.get(node_type, 0) + 1
        
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "connected_components": len(connected_components),
            "avg_degree": round(avg_degree, 2),
            "type_distribution": type_distribution,
            "relation_count": self.relation_count
        }


# 测试函数
def test_graph_builder():
    """测试图构建器"""
    from entity_extractor import Entity
    
    # 创建构建器
    builder = KnowledgeGraphBuilder()
    
    # 创建测试实体
    entity1 = Entity(
        id="char_阿比盖尔",
        name="阿比盖尔",
        type="character",
        attributes={"生日": "秋季第 14 天"},
        relations=[
            {"type": "father", "target": "皮埃尔"},
            {"type": "friend", "target": "山姆"}
        ]
    )
    
    entity2 = Entity(
        id="char_皮埃尔",
        name="皮埃尔",
        type="character",
        attributes={"职业": "杂货店老板"},
        relations=[]
    )
    
    entity3 = Entity(
        id="char_山姆",
        name="山姆",
        type="character",
        attributes={"职业": "无"},
        relations=[]
    )
    
    # 构建图
    builder.build_from_entities([entity1, entity2, entity3])
    
    # 打印统计信息
    stats = builder.get_stats()
    print(f"\n图统计信息:")
    print(f"  节点数：{stats['node_count']}")
    print(f"  边数：{stats['edge_count']}")
    print(f"  连通分量：{stats['connected_components']}")
    print(f"  平均度：{stats['avg_degree']}")
    print(f"  类型分布：{stats['type_distribution']}")
    
    # 测试邻居检索
    neighbors = builder.get_neighbors("char_阿比盖尔", k=1)
    print(f"\n阿比盖尔的邻居:")
    for nid, data in neighbors:
        print(f"  - {data['name']} ({data['type']})")
    
    # 测试路径检索
    path = builder.get_relation_path("char_阿比盖尔", "char_山姆")
    print(f"\n阿比盖尔到山姆的路径:")
    if path:
        for node_id in path:
            node_name = builder.graph.nodes[node_id].get('name')
            print(f"  {node_name}")
    
    # 保存图
    builder.save("test_graph.json")
    
    # 可视化（需要 graphviz）
    # builder.visualize("test_graph")
    
    return builder


if __name__ == "__main__":
    test_graph_builder()
