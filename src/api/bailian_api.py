import requests
import json

class BailianAPI:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        # 确保API URL正确
        if api_url:
            if api_url.endswith('/'):
                self.api_url = api_url.rstrip('/')
            else:
                self.api_url = api_url
        else:
            # 默认API URL
            self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        # 确保API密钥存在
        if not api_key:
            self.api_key = "your_api_key_here"
            print("警告: API密钥未设置，请在config/.env中配置BAILIAN_API_KEY")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate(self, prompt, model_name, temperature=0.7, max_tokens=1000, system_message=None):
        """调用阿里云百炼API生成文本"""
        # 构建完整的API URL
        api_url = f"{self.api_url}/chat/completions"
        
        messages = []
        
        # 添加系统消息（如果有）
        if system_message:
            messages.append({
                "role": "system",
                "content": "你是星露谷导游景明，要通过朴实热情的态度带领用户沉浸体验星露谷的生活"
            })
        
        # 添加用户消息
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except requests.RequestException as e:
            print(f"API调用失败: {e}")
            return "API调用失败，请稍后重试"
    
    def generate_with_context(self, query, context, model_name, temperature=0.7, max_tokens=1000):
        """带上下文的文本生成"""
        # 系统消息 - 控制回答风格
        system_message = "你是景明，星露谷镇鹈鹕村的导游，请使用热情活泼的语言回答问题，保持轻松愉快的语气，就像星露谷游戏的风格一样。回答过程中请尽量避免用户感知到这是一个游戏，你要假扮自己确实是存在于游戏之中的角色。回答要具体、实用，并且与上下文相关。"
        
        prompt = f"基于以下上下文回答问题：\n\n{context}\n\n问题：{query}\n\n回答："
        return self.generate(prompt, model_name, temperature, max_tokens, system_message)