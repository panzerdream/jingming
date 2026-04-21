#!/bin/bash
# 模型切换脚本 - 快速切换Agent RAG系统使用的模型

set -e

CONFIG_FILE="config/.env"
BACKUP_FILE="config/.env.backup"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 备份当前配置
backup_config() {
    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        print_info "配置文件已备份到 $BACKUP_FILE"
    fi
}

# 恢复备份配置
restore_config() {
    if [ -f "$BACKUP_FILE" ]; then
        cp "$BACKUP_FILE" "$CONFIG_FILE"
        print_success "配置文件已从备份恢复"
    else
        print_error "备份文件不存在"
    fi
}

# 显示当前配置
show_current() {
    if [ -f "$CONFIG_FILE" ]; then
        print_info "当前配置:"
        echo "══════════════════════════════════════════════"
        grep -E "^(MODEL_NAME|BAILIAN_API_KEY|# Model)" "$CONFIG_FILE" || true
        echo "══════════════════════════════════════════════"
        
        # 检查Ollama服务状态
        if which ollama >/dev/null 2>&1; then
            if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
                print_success "✅ Ollama服务正在运行"
                echo "可用模型:"
                ollama list | tail -n +2 || true
            else
                print_warning "⚠️  Ollama服务未运行，运行: ollama serve"
            fi
        else
            print_warning "⚠️  Ollama未安装"
        fi
    else
        print_error "配置文件不存在: $CONFIG_FILE"
    fi
}

# 切换到云端模型
switch_to_cloud() {
    backup_config
    
    local model_name="${1:-qwen3.6-plus}"
    
    cat > "$CONFIG_FILE" << EOF
# 阿里云百炼 API 配置
BAILIAN_API_KEY=your_api_key_here
BAILIAN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 向量存储配置
VECTOR_STORE_PATH=data/vector_db
KNOWLEDGE_BASE_PATH=data/knowledge

# 模型配置 - 云端模型
MODEL_NAME=${model_name}
MODEL_TYPE=cloud

# 检索配置
TOP_K=5
CHUNK_SIZE=500
CHUNK_OVERLAP=150

# 性能优化
API_TIMEOUT=15
MAX_TOKENS=500
EOF
    
    print_success "已切换到云端模型: $model_name"
    print_warning "请确保 BAILIAN_API_KEY 已正确设置"
}

# 切换到本地模型
switch_to_local() {
    backup_config
    
    local model_name="${1:-qwen3.5:9b}"
    
    # 检查Ollama服务
    if ! which ollama >/dev/null 2>&1; then
        print_error "Ollama未安装，请先安装: https://ollama.com"
        return 1
    fi
    
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_warning "Ollama服务未运行，正在启动..."
        ollama serve > /dev/null 2>&1 &
        sleep 3
    fi
    
    # 检查模型是否存在
    if ! ollama list | grep -q "$model_name"; then
        print_warning "模型 $model_name 不存在，正在下载..."
        ollama pull "$model_name"
    fi
    
    cat > "$CONFIG_FILE" << EOF
# 本地模型配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=${model_name}

# 向量存储配置
VECTOR_STORE_PATH=data/vector_db
KNOWLEDGE_BASE_PATH=data/knowledge

# 模型配置 - 本地模型
MODEL_NAME=${model_name}
MODEL_TYPE=local

# 检索配置
TOP_K=5
CHUNK_SIZE=500
CHUNK_OVERLAP=150

# 性能优化
API_TIMEOUT=30
MAX_TOKENS=1000
EOF
    
    print_success "已切换到本地模型: $model_name"
    print_info "本地模型响应速度更快，无需网络请求"
}

# 切换到混合模式
switch_to_hybrid() {
    backup_config
    
    local cloud_model="${1:-qwen3.6-plus}"
    local local_model="${2:-qwen3.5:9b}"
    
    cat > "$CONFIG_FILE" << EOF
# 混合模式配置
BAILIAN_API_KEY=your_api_key_here
BAILIAN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=${local_model}

# 向量存储配置
VECTOR_STORE_PATH=data/vector_db
KNOWLEDGE_BASE_PATH=data/knowledge

# 模型配置 - 混合模式
CLOUD_MODEL=${cloud_model}
LOCAL_MODEL=${local_model}
MODEL_TYPE=hybrid

# 检索配置
TOP_K=5
CHUNK_SIZE=500
CHUNK_OVERLAP=150

# 性能优化
CLOUD_TIMEOUT=10
LOCAL_TIMEOUT=30
FALLBACK_ENABLED=true
EOF
    
    print_success "已切换到混合模式"
    print_info "云端模型: $cloud_model (主用)"
    print_info "本地模型: $local_model (备用)"
}

# 性能测试
run_performance_test() {
    print_info "运行性能测试..."
    
    if [ -f "performance_test.py" ]; then
        python3 performance_test.py
    else
        print_error "性能测试脚本不存在"
        print_info "正在创建性能测试脚本..."
        
        # 这里可以添加创建测试脚本的代码
        print_info "请先运行模型切换，然后手动测试响应速度"
    fi
}

# 启动服务
start_services() {
    print_info "启动服务..."
    
    # 检查后端是否运行
    if ! pgrep -f "python3.*main.py" >/dev/null; then
        print_info "启动后端服务..."
        cd backend && KMP_DUPLICATE_LIB_OK=TRUE python3 main.py > backend.log 2>&1 &
        sleep 3
    else
        print_info "后端服务已在运行"
    fi
    
    # 检查前端是否运行
    if ! lsof -i :5173 >/dev/null 2>&1; then
        print_info "启动前端服务..."
        cd frontend && npm run dev > frontend.log 2>&1 &
        sleep 5
    else
        print_info "前端服务已在运行"
    fi
    
    print_success "服务启动完成"
    print_info "前端: http://localhost:5173"
    print_info "后端: http://localhost:8000"
}

# 显示帮助
show_help() {
    cat << EOF
模型切换脚本 - Agent RAG 系统

使用方法: $0 [命令] [选项]

命令:
  current                   显示当前配置
  cloud [模型名]           切换到云端模型 (默认: qwen3.6-plus)
  local [模型名]           切换到本地模型 (默认: qwen3.5:9b)
  hybrid [云模型] [本地模型] 切换到混合模式
  restore                  恢复备份配置
  test                     运行性能测试
  start                    启动所有服务
  help                    显示此帮助信息

示例:
  $0 current               显示当前配置
  $0 cloud                 切换到云端模型
  $0 local qwen2.5:7b     切换到指定本地模型
  $0 hybrid qwen3.6-plus qwen3.5:9b 切换到混合模式
  $0 test                 运行性能测试
  $0 start                启动前后端服务

注意事项:
  1. 切换到本地模型前请确保已安装Ollama
  2. 云端模型需要有效的BAILIAN_API_KEY
  3. 混合模式优先使用本地模型，失败时回退到云端
EOF
}

# 主函数
main() {
    local command="$1"
    local arg1="$2"
    local arg2="$3"
    
    case "$command" in
        "current"|"status")
            show_current
            ;;
        "cloud")
            switch_to_cloud "$arg1"
            show_current
            ;;
        "local")
            switch_to_local "$arg1"
            show_current
            ;;
        "hybrid")
            switch_to_hybrid "$arg1" "$arg2"
            show_current
            ;;
        "restore")
            restore_config
            show_current
            ;;
        "test")
            run_performance_test
            ;;
        "start")
            start_services
            ;;
        "help"|"")
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"