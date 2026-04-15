from langchain.tools import Tool
import requests

class ToolManager:
    def __init__(self):
        self.tools = []
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 搜索工具
        search_tool = Tool(
            name="Search",
            func=self.search_web,
            description="用于搜索网络信息，回答关于最新事件、事实性问题等"
        )
        self.tools.append(search_tool)
        
        # 计算器工具
        calculator_tool = Tool(
            name="Calculator",
            func=self.calculate,
            description="用于执行数学计算"
        )
        self.tools.append(calculator_tool)
    
    def add_tool(self, tool):
        """添加自定义工具"""
        self.tools.append(tool)
    
    def get_tools(self):
        """获取所有工具"""
        return self.tools
    
    def search_web(self, query):
        """搜索网络信息"""
        # 这里使用一个简单的模拟实现
        # 实际项目中可以集成Tavily API或其他搜索服务
        return f"关于'{query}'的搜索结果：这是一个模拟的搜索结果，实际项目中会调用真实的搜索API"
    
    def calculate(self, expression):
        """执行数学计算"""
        try:
            result = eval(expression)
            return f"计算结果：{result}"
        except Exception as e:
            return f"计算错误：{str(e)}"
    
    def run_tool(self, tool_name, input_text):
        """运行指定工具"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.func(input_text)
        return f"工具 {tool_name} 不存在"
    
    def get_tool_descriptions(self):
        """获取工具描述"""
        descriptions = []
        for tool in self.tools:
            descriptions.append(f"{tool.name}: {tool.description}")
        return "\n".join(descriptions)