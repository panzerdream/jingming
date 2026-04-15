import requests
import json

class BailianAPI:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        # 确保API URL正确
        if api_url.endswith('/'):
            self.api_url = api_url.rstrip('/')
        else:
            self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def generate(self, prompt, model_name, temperature=0.7, max_tokens=1000):
        """调用阿里云百炼API生成文本"""
        # 构建完整的API URL
        api_url = f"{self.api_url}/chat/completions"
        
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
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
        prompt = f"基于以下上下文回答问题：\n\n{context}\n\n问题：{query}\n\n回答："
        return self.generate(prompt, model_name, temperature, max_tokens)