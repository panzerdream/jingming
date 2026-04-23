"""
实体抽取器
从 Markdown 文档中提取实体和关系
支持星露谷物语知识库的特定格式
"""
import re
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

# 导入日志模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger()


@dataclass
class Entity:
    """实体类"""
    id: str
    name: str
    type: str  # character, item, festival, location
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "attributes": self.attributes,
            "relations": self.relations
        }


@dataclass
class Relation:
    """关系类"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)


class EntityExtractor:
    """星露谷物语知识库实体抽取器"""
    
    def __init__(self):
        # 实体类型映射
        self.entity_type_map = {
            "人物": "character",
            "角色": "character",
            "居民": "character",
            "物品": "item",
            "道具": "item",
            "节日": "festival",
            "活动": "festival",
            "地点": "location",
            "区域": "location"
        }
        
        # 关系类型映射
        self.relation_type_map = {
            "家庭": "family",
            "家人": "family",
            "父母": "parent",
            "父亲": "father",
            "母亲": "mother",
            "女儿": "daughter",
            "儿子": "son",
            "朋友": "friend",
            "好友": "friend",
            "同事": "colleague",
            "工作": "work_at",
            "住在": "live_at",
            "喜欢": "like",
            "爱": "love",
            "讨厌": "hate",
            "位于": "located_at",
            "属于": "belong_to"
        }
        
        # 编译正则表达式
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """编译正则表达式模式"""
        patterns = {}
        
        # 人物属性提取
        patterns['character_attr'] = re.compile(
            r'\*\*(.*?)\*\*[:：]\s*(.*?)(?:\n|$)',
            re.MULTILINE
        )
        
        # 关系提取（列表格式）
        patterns['relation_list'] = re.compile(
            r'^[ \t]*[-*•]\s*(.*?)[:：]\s*(.*?)(?:\n|$)',
            re.MULTILINE
        )
        
        # 关系提取（文本格式）
        patterns['relation_text'] = re.compile(
            r'(?:和 | 与|的|是)([\u4e00-\u9fa5]+?)(?:的|朋友 | 家人 | 女儿 | 儿子 | 父亲 | 母亲)',
            re.MULTILINE
        )
        
        # 物品分类
        patterns['item_category'] = re.compile(
            r'##\s*(农作物 | 果树 | 动物产品 | 鱼类 | 矿物 | 手工艺品 | 工具 | 食物)',
            re.MULTILINE
        )
        
        # 节日信息
        patterns['festival_info'] = re.compile(
            r'\*\*(时间 | 日期 | 地点 | 活动)\*\*[:：]\s*(.*?)(?:\n|$)',
            re.MULTILINE
        )
        
        return patterns
    
    def extract_character(self, content: str, filename: str) -> Optional[Entity]:
        """从人物详细文档中提取实体"""
        try:
            # 从文件名获取人物名称
            name = os.path.splitext(filename)[0]
            entity_id = f"char_{name}"
            
            # 提取属性
            attributes = {}
            matches = self.patterns['character_attr'].finditer(content)
            for match in matches:
                key = match.group(1).strip()
                value = match.group(2).strip()
                attributes[key] = value
            
            # 提取关系
            relations = []
            
            # 查找家庭关系
            family_keywords = ['父亲', '母亲', '女儿', '儿子', '祖父', '祖母', '兄弟', '姐妹']
            for keyword in family_keywords:
                if keyword in content:
                    # 简单提取，实际应该更复杂
                    pattern = rf'{keyword}[:：]\s*([^\n,，]+)'
                    match = re.search(pattern, content)
                    if match:
                        relative_name = match.group(1).strip()
                        relations.append({
                            "type": "family",
                            "subtype": keyword,
                            "target": relative_name
                        })
            
            # 查找朋友关系
            if '朋友' in content or '好友' in content:
                friend_pattern = r'(?:朋友 | 好友)[:：\s]*([^\n,，]+)'
                match = re.search(friend_pattern, content)
                if match:
                    friend_names = match.group(1).strip()
                    for name in re.split(r'[、,，]', friend_names):
                        if name.strip():
                            relations.append({
                                "type": "friend",
                                "target": name.strip()
                            })
            
            # 查找工作地点
            work_keywords = ['工作', '职业', '上班']
            for keyword in work_keywords:
                if keyword in content:
                    pattern = rf'{keyword}[:：\s]*([^\n,，]+)'
                    match = re.search(pattern, content)
                    if match:
                        workplace = match.group(1).strip()
                        relations.append({
                            "type": "work_at",
                            "target": workplace
                        })
            
            # 查找住址
            if '住在' in content or '住址' in content:
                addr_pattern = r'(?:住在 | 住址)[:：\s]*([^\n,，]+)'
                match = re.search(addr_pattern, content)
                if match:
                    address = match.group(1).strip()
                    relations.append({
                        "type": "live_at",
                        "target": address
                    })
            
            # 创建实体
            entity = Entity(
                id=entity_id,
                name=name,
                type="character",
                attributes=attributes,
                relations=relations
            )
            
            logger.debug(f"Extracted character entity: {name}, relations: {len(relations)}")
            return entity
            
        except Exception as e:
            logger.error(f"Failed to extract character from {filename}: {e}")
            return None
    
    def extract_item(self, content: str, filename: str) -> List[Entity]:
        """从物品文档中提取实体"""
        entities = []
        
        try:
            # 提取物品分类
            categories = self.patterns['item_category'].findall(content)
            
            # 按分类提取物品
            current_category = None
            lines = content.split('\n')
            
            for line in lines:
                # 检查是否是分类标题
                for category in categories:
                    if category in line and '##' in line:
                        current_category = category
                        break
                
                # 提取物品名称（列表格式）
                if current_category and line.strip().startswith('-'):
                    item_match = re.search(r'-\s*\*\*(.+?)\*\*', line)
                    if item_match:
                        item_name = item_match.group(1).strip()
                        entity_id = f"item_{item_name}"
                        
                        entity = Entity(
                            id=entity_id,
                            name=item_name,
                            type="item",
                            attributes={
                                "category": current_category,
                                "source_file": filename
                            }
                        )
                        entities.append(entity)
            
            logger.debug(f"Extracted {len(entities)} item entities from {filename}")
            return entities
            
        except Exception as e:
            logger.error(f"Failed to extract items from {filename}: {e}")
            return []
    
    def extract_festival(self, content: str, filename: str) -> List[Entity]:
        """从节日文档中提取实体"""
        entities = []
        
        try:
            # 查找节日标题
            festival_pattern = r'###\s*(.+?)(?:\n|$)'
            festivals = re.finditer(festival_pattern, content)
            
            for match in festivals:
                festival_name = match.group(1).strip()
                if not festival_name or len(festival_name) > 20:
                    continue
                
                entity_id = f"fest_{festival_name}"
                
                # 提取节日属性
                attributes = {"source_file": filename}
                
                # 查找时间
                time_match = re.search(r'(?:时间 | 日期)[:：\s]*([^\n]+)', content)
                if time_match:
                    attributes['time'] = time_match.group(1).strip()
                
                # 查找地点
                loc_match = re.search(r'地点 [:：\s]*([^\n]+)', content)
                if loc_match:
                    attributes['location'] = loc_match.group(1).strip()
                
                # 查找活动
                act_match = re.search(r'活动 [:：\s]*([^\n]+)', content)
                if act_match:
                    attributes['activity'] = act_match.group(1).strip()
                
                entity = Entity(
                    id=entity_id,
                    name=festival_name,
                    type="festival",
                    attributes=attributes
                )
                entities.append(entity)
            
            logger.debug(f"Extracted {len(entities)} festival entities from {filename}")
            return entities
            
        except Exception as e:
            logger.error(f"Failed to extract festivals from {filename}: {e}")
            return []
    
    def extract_from_markdown(self, filepath: str) -> List[Entity]:
        """从 Markdown 文件提取实体"""
        entities = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = os.path.basename(filepath)
            
            # 判断文件类型并提取
            if '居民详细' in filepath:
                # 人物详细文档
                entity = self.extract_character(content, filename)
                if entity:
                    entities.append(entity)
            
            elif '人物' in filename:
                # 人物总览文档
                # 可以提取多个人物
                pass
            
            elif '物品' in filename:
                # 物品文档
                items = self.extract_item(content, filename)
                entities.extend(items)
            
            elif '节日' in filename:
                # 节日文档
                festivals = self.extract_festival(content, filename)
                entities.extend(festivals)
            
            logger.info(f"Extracted {len(entities)} entities from {filepath}")
            return entities
            
        except Exception as e:
            logger.error(f"Failed to extract from {filepath}: {e}")
            return []
    
    def extract_from_directory(self, directory: str) -> List[Entity]:
        """从目录中所有 Markdown 文件提取实体"""
        all_entities = []
        
        try:
            # 遍历目录
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.md'):
                        filepath = os.path.join(root, file)
                        entities = self.extract_from_markdown(filepath)
                        all_entities.extend(entities)
            
            logger.info(f"Total extracted {len(all_entities)} entities from {directory}")
            return all_entities
            
        except Exception as e:
            logger.error(f"Failed to extract from directory {directory}: {e}")
            return []


# 测试函数
def test_extractor():
    """测试实体抽取器"""
    extractor = EntityExtractor()
    
    # 测试人物抽取
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
        print(f"实体：{entity.name}")
        print(f"类型：{entity.type}")
        print(f"属性：{entity.attributes}")
        print(f"关系：{entity.relations}")
    
    return entity


if __name__ == "__main__":
    test_extractor()
