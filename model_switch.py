#!/usr/bin/env python3
"""
快速模型切换工具
"""

import os
import sys
import subprocess
import time

CONFIG_FILE = "config/.env"

def print_color(text, color="white"):
    """打印带颜色的文本"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def show_current():
    """显示当前配置"""
    print_color("=== 当前配置 ===", "blue")
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()
            print(content)
    else:
        print_color("配置文件不存在", "yellow")
    
    # 检查Ollama
    print_color("\n=== 系统状态 ===", "blue")
    try:
        result = subprocess.run(["which", "ollama"], capture_output=True, text=True)
        if result.returncode == 0:
            print_color("✅ Ollama已安装", "green")
            
            # 检查服务状态
            try:
                subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"], 
                             capture_output=True, timeout=2)
                print_color("✅ Ollama服务正在运行", "green")
                
                # 显示可用模型
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
                if result.stdout:
                    print_color("可用模型:", "blue")
                    print(result.stdout)
            except:
                print_color("⚠️  Ollama服务未运行", "yellow")
        else:
            print_color("❌ Ollama未安装", "red")
    except:
        print_color("❌ 无法检查Ollama状态", "red")

def switch_to_local(model="qwen3.5:9b"):
    """切换到本地模型"""
    print_color(f"切换到本地模型: {model}", "blue")
    
    # 检查Ollama
    try:
        subprocess.run(["which", "ollama"], check=True, capture_output=True)
    except:
        print_color("错误: Ollama未安装，请先安装: https://ollama.com", "red")
        return
    
    # 检查服务
    try:
        subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"], 
                      timeout=2, check=True, capture_output=True)
    except:
        print_color("启动Ollama服务...", "yellow")
        subprocess.Popen(["ollama", "serve"])
        time.sleep(3)
    
    # 检查模型
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model not in result.stdout:
            print_color(f"下载模型 {model}...", "yellow")
            subprocess.run(["ollama", "pull", model])
    except:
        print_color("警告: 无法检查模型列表", "yellow")
    
    # 更新配置
    config = f"""# 本地模型配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL={model}

# 向量存储配置
VECTOR_STORE_PATH=data/vector_db
KNOWLEDGE_BASE_PATH=data/knowledge

# 模型配置
MODEL_NAME={model}
MODEL_TYPE=local

# 检索配置
TOP_K=5
CHUNK_SIZE=500
CHUNK_OVERLAP=150

# 性能优化
API_TIMEOUT=30
MAX_TOKENS=1000
"""
    
    with open(CONFIG_FILE, 'w') as f:
        f.write(config)
    
    print_color(f"✅ 已切换到本地模型: {model}", "green")
    print_color("本地模型响应速度更快（通常1-3秒）", "green")

def switch_to_cloud(model="qwen3.6-plus"):
    """切换到云端模型"""
    print_color(f"切换到云端模型: {model}", "blue")
    
    config = f"""# 阿里云百炼 API 配置
BAILIAN_API_KEY=your_api_key_here
BAILIAN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 向量存储配置
VECTOR_STORE_PATH=data/vector_db
KNOWLEDGE_BASE_PATH=data/knowledge

# 模型配置
MODEL_NAME={model}
MODEL_TYPE=cloud

# 检索配置
TOP_K=5
CHUNK_SIZE=500
CHUNK_OVERLAP=150

# 性能优化
API_TIMEOUT=15
MAX_TOKENS=500
"""
    
    with open(CONFIG_FILE, 'w') as f:
        f.write(config)
    
    print_color(f"✅ 已切换到云端模型: {model}", "green")
    print_color("⚠️  请确保BAILIAN_API_KEY已正确设置", "yellow")

def quick_test():
    """快速性能测试"""
    print_color("=== 快速性能测试 ===", "blue")
    
    # 测试查询
    test_queries = [
        "你好",
        "现在几点",
        "计算2+3"
    ]
    
    for query in test_queries:
        print_color(f"\n测试: {query}", "blue")
        
        # 使用curl测试后端API
        try:
            import time
            start = time.time()
            result = subprocess.run([
                "curl", "-s", "-X", "POST", 
                "http://localhost:8000/api/query",
                "-H", "Content-Type: application/json",
                "-d", f'{{"query":"{query}"}}'
            ], capture_output=True, text=True, timeout=10)
            elapsed = time.time() - start
            
            if result.returncode == 0:
                response = result.stdout[:100] + "..." if len(result.stdout) > 100 else result.stdout
                print_color(f"响应时间: {elapsed:.2f}秒", "green")
                print_color(f"响应: {response}", "white")
            else:
                print_color(f"请求失败 ({elapsed:.2f}秒)", "red")
                
        except subprocess.TimeoutExpired:
            print_color("请求超时（10秒）", "red")
        except Exception as e:
            print_color(f"错误: {e}", "red")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_color("使用方法:", "blue")
        print_color("  python3 model_switch.py current    # 显示当前配置")
        print_color("  python3 model_switch.py local      # 切换到本地模型")
        print_color("  python3 model_switch.py cloud      # 切换到云端模型")
        print_color("  python3 model_switch.py test       # 快速性能测试")
        return
    
    command = sys.argv[1]
    
    if command == "current":
        show_current()
    elif command == "local":
        model = sys.argv[2] if len(sys.argv) > 2 else "qwen3.5:9b"
        switch_to_local(model)
    elif command == "cloud":
        model = sys.argv[2] if len(sys.argv) > 2 else "qwen3.6-plus"
        switch_to_cloud(model)
    elif command == "test":
        quick_test()
    else:
        print_color(f"未知命令: {command}", "red")

if __name__ == "__main__":
    main()