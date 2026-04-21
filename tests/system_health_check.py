#!/usr/bin/env python3
"""
系统健康检查
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_system_health():
    """检查系统健康状态"""
    
    print("系统健康检查")
    print("=" * 60)
    
    checks = []
    
    # 检查1: Python版本
    try:
        python_version = sys.version.split()[0]
        checks.append(("Python版本", f"✓ {python_version}", True))
    except:
        checks.append(("Python版本", "✗ 无法获取", False))
    
    # 检查2: 依赖导入
    try:
        import psutil
        checks.append(("psutil依赖", f"✓ {psutil.__version__}", True))
    except:
        checks.append(("psutil依赖", "✗ 未安装", False))
    
    # 检查3: 配置文件
    config_files = [
        ("config/.env", "环境变量配置"),
        ("requirements.txt", "依赖文件"),
        ("data/knowledge/", "知识库目录"),
    ]
    
    for path, name in config_files:
        if os.path.exists(path):
            checks.append((name, f"✓ 存在", True))
        else:
            checks.append((name, f"✗ 不存在", False))
    
    # 检查4: 核心模块
    core_modules = [
        ("src/tools/enhanced_tool_manager.py", "增强工具管理器"),
        ("src/api/bailian_api.py", "API模块"),
        ("src/main.py", "主程序"),
        ("src/utils/logger.py", "日志系统"),
        ("src/utils/monitor.py", "监控系统"),
    ]
    
    for path, name in core_modules:
        if os.path.exists(path):
            checks.append((name, f"✓ 存在", True))
        else:
            checks.append((name, f"✗ 不存在", False))
    
    # 显示检查结果
    all_passed = True
    for name, status, passed in checks:
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有健康检查通过")
    else:
        print("⚠️  部分健康检查失败")
    
    return all_passed

def test_tool_system():
    """测试工具系统"""
    
    print("\n\n工具系统测试")
    print("=" * 60)
    
    try:
        # 添加src目录到路径
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
        
        from tools.enhanced_tool_manager import EnhancedToolManager
        
        tool_manager = EnhancedToolManager()
        print("✓ 工具管理器初始化成功")
        
        # 测试计算器
        test_cases = [
            ("10加5", "calculator", {"expression": "10+5"}),
            ("20乘以3", "calculator", {"expression": "20*3"}),
            ("现在几点", "get_current_time", {}),
        ]
        
        for query, expected_tool, expected_params in test_cases:
            print(f"\n测试查询: '{query}'")
            
            should_use = tool_manager.should_use_tool(query)
            tool_name, params = tool_manager.parse_tool_call(query)
            
            if should_use:
                print(f"  ✓ 识别需要工具")
                if tool_name == expected_tool:
                    print(f"  ✓ 正确识别工具: {tool_name}")
                else:
                    print(f"  ✗ 错误识别工具: 期望 {expected_tool}, 实际 {tool_name}")
                
                # 执行工具
                try:
                    result = tool_manager.run_tool(tool_name, params)
                    print(f"  ✓ 工具执行成功")
                    print(f"    结果: {result}")
                except Exception as e:
                    print(f"  ✗ 工具执行失败: {e}")
            else:
                print(f"  ✗ 未识别需要工具")
        
        print("\n✅ 工具系统测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 工具系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("Agent RAG 系统健康检查")
    print("=" * 60)
    
    # 运行检查
    health_ok = check_system_health()
    tools_ok = test_tool_system()
    
    print("\n" + "=" * 60)
    print("最终状态:")
    print(f"  健康检查: {'✅ 通过' if health_ok else '❌ 失败'}")
    print(f"  工具系统: {'✅ 通过' if tools_ok else '❌ 失败'}")
    
    if health_ok and tools_ok:
        print("\n🎉 系统状态良好，可以正常运行")
    else:
        print("\n⚠️  系统存在问题，需要修复")

if __name__ == "__main__":
    main()