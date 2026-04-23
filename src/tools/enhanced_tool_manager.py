import time
import re
import math
import json
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from langchain_core.tools import Tool

from utils.logger import get_logger
from utils.monitor import get_metrics_collector

logger = get_logger()
metrics = get_metrics_collector()


class IntentRecognizer:
    """意图识别器"""
    
    def __init__(self):
        # 意图模式定义
        self.intent_patterns = {
            "search": [
                r"(搜索|查找|查询|搜一下|找一下|查一下)(.*)",
                r"(什么是|什么是|什么是)(.*)",
                r"(.*)的(信息|资料|详情)",
            ],
            "calculate": [
                r"(\d+)(加上|加|\+)(\d+)",
                r"(\d+)(减去|减|\-)(\d+)",
                r"(\d+)(乘以|乘|\*)(\d+)",
                r"(\d+)(除以|除|/)(\d+)",
                r"(.*)[\+\-\*/](.*)",  # 匹配包含数学运算符的表达式
                r"(计算|算一下|计算一下)(.*)",
                r"(.*)等于多少",
                r"(.*)的(结果|答案)"
            ],
            "time": [
                r"(现在几点|当前时间|时间)",
                r"(今天几号|日期)",
                r"(星期几)",
            ],
            "weather": [
                r"(天气|气温|温度|天气预报)(.*)",
                r"(.*)的天气",
            ],
            "wiki": [
                r"(维基百科|wiki)(.*)",
                r"(.*)的维基百科",
            ],
            "translate": [
                r"(翻译|translate)(.*)",
                r"(.*)的(中文|英文)翻译",
            ],
        }
        
        # 工具映射
        self.tool_mapping = {
            "search": "web_search",
            "calculate": "calculator",
            "time": "get_current_time",
            "weather": "get_weather",
            "wiki": "wikipedia_search",
            "translate": "translate_text",
        }
    
    def recognize(self, query: str) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        """识别查询意图"""
        query = query.strip().lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.match(pattern, query)
                if match:
                    # 提取参数
                    params = self._extract_params(intent, query, match)
                    tool_name = self.tool_mapping.get(intent)
                    
                    logger.info(f"Intent recognized: {intent} -> {tool_name}", 
                               query=query, intent=intent, tool_name=tool_name)
                    
                    return intent, tool_name, params
        
        # 默认返回None，表示不需要工具
        return None, None, {}
    
    def _extract_params(self, intent: str, query: str, match: re.Match) -> Dict[str, Any]:
        """提取意图参数"""
        params = {}
        
        if intent == "search":
            # 提取搜索关键词
            groups = match.groups()
            if len(groups) >= 2:
                params["query"] = groups[1].strip()
            else:
                params["query"] = query
        
        elif intent == "calculate":
            # 提取计算表达式
            groups = match.groups()
            
            # 处理不同的模式
            if len(groups) >= 1:
                # 模式1: "计算一下25乘以4" -> groups[0] = "计算", groups[1] = "一下25乘以4"
                # 模式2: "25乘以4等于多少" -> groups[0] = "25乘以4"
                # 模式3: "12加8" -> groups[0] = "12", groups[1] = "加", groups[2] = "8"
                # 模式4: "15-7" -> groups[0] = "15", groups[1] = "7"
                
                if len(groups) == 3 and groups[1] and groups[2]:
                    # 模式3: "12加8" 或 "12+8" 或 "100除以5"
                    num1 = groups[0].strip()
                    operator = groups[1].strip()
                    num2 = groups[2].strip()
                    
                    # 转换中文运算符
                    operator_map = {
                        "加": "+", "加上": "+",
                        "减": "-", "减去": "-",
                        "乘": "*", "乘以": "*",
                        "除": "/", "除以": "/"
                    }
                    
                    math_operator = operator_map.get(operator, operator)
                    expression = f"{num1}{math_operator}{num2}"
                elif len(groups) == 2 and match.re.pattern == r"(.*)[\+\-\*/](.*)":
                    # 模式4: "15-7" 或 "15*3"
                    # 需要从原始查询中提取完整表达式
                    expression = query
                elif len(groups) == 2 and groups[0] in ["计算", "算一下", "计算一下"]:
                    # 模式1: "计算一下25乘以4"
                    expression = groups[1].strip()
                else:
                    # 模式2: "25乘以4等于多少" 或其他模式
                    expression = groups[0].strip()
                
                # 将中文运算符转换为数学运算符
                expression = expression.replace("乘以", "*")
                expression = expression.replace("乘", "*")
                expression = expression.replace("除以", "/")
                expression = expression.replace("除", "/")
                expression = expression.replace("加上", "+")
                expression = expression.replace("加", "+")
                expression = expression.replace("减去", "-")
                expression = expression.replace("减", "-")
                expression = expression.replace("等于", "=")
                
                # 清理表达式
                expression = re.sub(r"[^\d\+\-\*\/\(\)\.\s=]", "", expression)
                params["expression"] = expression
        
        elif intent == "weather":
            # 提取地点
            groups = match.groups()
            if len(groups) >= 2 and groups[1].strip():
                params["location"] = groups[1].strip()
            else:
                params["location"] = "北京"  # 默认地点
        
        elif intent == "wiki":
            # 提取搜索词
            groups = match.groups()
            if len(groups) >= 2:
                params["query"] = groups[1].strip()
            else:
                params["query"] = query
        
        elif intent == "translate":
            # 提取翻译文本和目标语言
            groups = match.groups()
            if len(groups) >= 2:
                text = groups[1].strip()
                params["text"] = text
                
                # 检测目标语言
                if "中文" in query:
                    params["target_lang"] = "zh"
                elif "英文" in query or "english" in query.lower():
                    params["target_lang"] = "en"
                else:
                    params["target_lang"] = "en"  # 默认翻译成英文
        
        return params


class EnhancedToolManager:
    """增强的工具管理器"""
    
    def __init__(self):
        self.tools = {}
        self.intent_recognizer = IntentRecognizer()
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 网页搜索工具
        self.register_tool(
            name="web_search",
            func=self.web_search,
            description="搜索网络信息，支持中文和英文搜索"
        )
        
        # 计算器工具
        self.register_tool(
            name="calculator",
            func=self.calculator,
            description="执行数学计算，支持加减乘除和常用函数"
        )
        
        # 时间工具
        self.register_tool(
            name="get_current_time",
            func=self.get_current_time,
            description="获取当前时间和日期"
        )
        
        # 天气工具
        self.register_tool(
            name="get_weather",
            func=self.get_weather,
            description="获取指定城市的天气信息"
        )
        
        # 维基百科工具
        self.register_tool(
            name="wikipedia_search",
            func=self.wikipedia_search,
            description="搜索维基百科内容"
        )
        
        # 翻译工具
        self.register_tool(
            name="translate_text",
            func=self.translate_text,
            description="翻译文本，支持中英文互译"
        )
        
        # 单位转换工具
        self.register_tool(
            name="unit_converter",
            func=self.unit_converter,
            description="单位转换，支持长度、重量、温度等"
        )
        
        # 货币转换工具
        self.register_tool(
            name="currency_converter",
            func=self.currency_converter,
            description="货币转换，支持主流货币"
        )
        
        logger.info(f"Registered {len(self.tools)} tools")
    
    def register_tool(self, name: str, func: callable, description: str):
        """注册工具"""
        tool = Tool(
            name=name,
            func=func,
            description=description
        )
        self.tools[name] = tool
    
    def get_tools(self) -> List[Tool]:
        """获取所有工具"""
        return list(self.tools.values())
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取指定工具"""
        return self.tools.get(name)
    
    def get_tool_descriptions(self) -> str:
        """获取工具描述"""
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- {name}: {tool.description}")
        return "\n".join(descriptions)
    
    def should_use_tool(self, query: str) -> bool:
        """判断是否需要使用工具"""
        intent, tool_name, params = self.intent_recognizer.recognize(query)
        return intent is not None
    
    def parse_tool_call(self, query: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """解析工具调用"""
        intent, tool_name, params = self.intent_recognizer.recognize(query)
        return tool_name, params
    
    def run_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """运行指定工具"""
        start_time = time.time()
        
        try:
            tool = self.get_tool(tool_name)
            if not tool:
                error_msg = f"工具 {tool_name} 不存在"
                logger.error(error_msg)
                metrics.record_error("tool_not_found")
                return error_msg
            
            # 执行工具
            result = tool.func(**params)
            
            # 记录指标
            execution_time = time.time() - start_time
            metrics.record_tool_usage(tool_name, success=True)
            logger.log_tool_usage(tool_name, str(params), result, True, 
                                 execution_time=execution_time)
            
            return result
            
        except Exception as e:
            error_msg = f"工具执行失败: {str(e)}"
            execution_time = time.time() - start_time
            logger.error(error_msg, tool_name=tool_name, params=params, error=str(e))
            metrics.record_tool_usage(tool_name, success=False)
            metrics.record_error("tool_execution_failed")
            return error_msg
    
    # ========== 工具实现 ==========
    
    def web_search(self, query: str) -> str:
        """网页搜索"""
        try:
            # 这里可以使用真实的搜索API，如Tavily、Serper等
            # 暂时返回模拟结果
            return f"关于 '{query}' 的搜索结果：\n" \
                   f"1. 相关文章1: {query}的详细介绍\n" \
                   f"2. 相关文章2: {query}的最新信息\n" \
                   f"3. 相关文章3: {query}的实用指南\n" \
                   f"（注：实际项目中请集成真实的搜索API）"
        except Exception as e:
            return f"搜索失败: {str(e)}"
    
    def calculator(self, expression: str) -> str:
        """计算器"""
        try:
            # 安全地执行计算
            allowed_chars = set("0123456789+-*/(). =")
            if not all(c in allowed_chars for c in expression):
                return "表达式包含非法字符"
            
            # 移除等号（如果有）
            if "=" in expression:
                expression = expression.split("=")[0].strip()
            
            # 使用eval计算（注意：生产环境应使用更安全的方法）
            result = eval(expression, {"__builtins__": {}}, 
                         {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, 
                          "tan": math.tan, "log": math.log, "exp": math.exp})
            
            # 返回纯数字结果，同时保留原始表达式用于显示
            try:
                # 尝试转换为整数（如果是整数）
                if isinstance(result, float) and result.is_integer():
                    return str(int(result))
                return str(result)
            except:
                return str(result)
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    def get_current_time(self) -> str:
        """获取当前时间"""
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}\n" \
               f"星期: {['一', '二', '三', '四', '五', '六', '日'][now.weekday()]}"
    
    def get_weather(self, location: str = "北京") -> str:
        """获取天气"""
        try:
            # 这里可以集成真实的天气API
            # 暂时返回模拟数据
            weather_data = {
                "北京": {"temp": "25°C", "condition": "晴", "humidity": "45%"},
                "上海": {"temp": "28°C", "condition": "多云", "humidity": "65%"},
                "广州": {"temp": "30°C", "condition": "阵雨", "humidity": "75%"},
                "深圳": {"temp": "29°C", "condition": "多云", "humidity": "70%"},
            }
            
            if location in weather_data:
                data = weather_data[location]
                return f"{location}天气:\n" \
                       f"温度: {data['temp']}\n" \
                       f"天气: {data['condition']}\n" \
                       f"湿度: {data['humidity']}"
            else:
                return f"未找到 {location} 的天气信息，支持的城市: {', '.join(weather_data.keys())}"
        except Exception as e:
            return f"获取天气失败: {str(e)}"
    
    def wikipedia_search(self, query: str) -> str:
        """维基百科搜索"""
        try:
            # 这里可以集成Wikipedia API
            return f"维基百科搜索结果 - '{query}':\n" \
                   f"{query}是一个重要的话题，在维基百科上有详细记载。\n" \
                   f"（注：实际项目中请集成Wikipedia API）"
        except Exception as e:
            return f"维基百科搜索失败: {str(e)}"
    
    def translate_text(self, text: str, target_lang: str = "en") -> str:
        """翻译文本"""
        try:
            # 这里可以集成翻译API（如Google Translate、百度翻译等）
            translations = {
                "en": {"你好": "Hello", "世界": "World", "星露谷": "Stardew Valley"},
                "zh": {"Hello": "你好", "World": "世界", "Stardew Valley": "星露谷"},
            }
            
            if target_lang == "en":
                # 简单的中译英
                if text in translations["en"]:
                    return f"翻译结果: {translations['en'][text]}"
                else:
                    return f"'{text}' 的英文翻译"
            elif target_lang == "zh":
                # 简单的英译中
                if text in translations["zh"]:
                    return f"翻译结果: {translations['zh'][text]}"
                else:
                    return f"'{text}' 的中文翻译"
            else:
                return f"暂不支持翻译到 {target_lang} 语言"
        except Exception as e:
            return f"翻译失败: {str(e)}"
    
    def unit_converter(self, value: float, from_unit: str, to_unit: str) -> str:
        """单位转换"""
        try:
            # 定义转换因子
            conversions = {
                "length": {
                    "m": 1, "km": 1000, "cm": 0.01, "mm": 0.001,
                    "mile": 1609.34, "yard": 0.9144, "foot": 0.3048, "inch": 0.0254
                },
                "weight": {
                    "kg": 1, "g": 0.001, "mg": 0.000001,
                    "lb": 0.453592, "oz": 0.0283495
                },
                "temperature": {
                    "c": lambda x: x,  # 摄氏度
                    "f": lambda x: (x * 9/5) + 32,  # 华氏度
                    "k": lambda x: x + 273.15,  # 开尔文
                }
            }
            
            # 确定转换类型
            for conv_type, units in conversions.items():
                if from_unit in units and to_unit in units:
                    if conv_type == "temperature":
                        # 温度转换
                        result = conversions[conv_type][to_unit](value)
                        return f"{value}°{from_unit.upper()} = {result:.2f}°{to_unit.upper()}"
                    else:
                        # 其他单位转换
                        result = value * units[from_unit] / units[to_unit]
                        return f"{value} {from_unit} = {result:.4f} {to_unit}"
            
            return f"不支持从 {from_unit} 到 {to_unit} 的转换"
        except Exception as e:
            return f"单位转换失败: {str(e)}"
    
    def currency_converter(self, amount: float, from_currency: str, to_currency: str) -> str:
        """货币转换"""
        try:
            # 这里可以集成真实的汇率API
            # 暂时使用模拟汇率
            exchange_rates = {
                "USD": {"CNY": 7.2, "EUR": 0.92, "JPY": 150},
                "CNY": {"USD": 0.14, "EUR": 0.13, "JPY": 21},
                "EUR": {"USD": 1.09, "CNY": 7.8, "JPY": 163},
            }
            
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            if from_currency in exchange_rates and to_currency in exchange_rates[from_currency]:
                rate = exchange_rates[from_currency][to_currency]
                result = amount * rate
                return f"{amount} {from_currency} = {result:.2f} {to_currency} (汇率: 1 {from_currency} = {rate} {to_currency})"
            else:
                return f"不支持 {from_currency} 到 {to_currency} 的转换"
        except Exception as e:
            return f"货币转换失败: {str(e)}"


# 全局工具管理器实例
_tool_manager = None


def get_tool_manager() -> EnhancedToolManager:
    """获取全局工具管理器实例"""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = EnhancedToolManager()
    return _tool_manager


# 便捷函数
def should_use_tool(query: str) -> bool:
    """判断是否需要使用工具"""
    return get_tool_manager().should_use_tool(query)

def parse_tool_call(query: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """解析工具调用"""
    return get_tool_manager().parse_tool_call(query)

def run_tool(tool_name: str, params: Dict[str, Any]) -> str:
    """运行指定工具"""
    return get_tool_manager().run_tool(tool_name, params)

def get_tool_descriptions() -> str:
    """获取工具描述"""
    return get_tool_manager().get_tool_descriptions()