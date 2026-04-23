"""
Redis 集成测试脚本
测试 Redis 管理器和增强对话管理器的功能
"""
import sys
import os
import time

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.redis_manager import RedisManager, init_redis_manager, get_redis_manager
from conversation.enhanced_conversation_manager import EnhancedConversationManager
from utils.logger import get_logger

logger = get_logger()


def test_redis_connection():
    """测试 Redis 连接"""
    print("\n=== 测试 Redis 连接 ===")
    
    try:
        redis_mgr = init_redis_manager(
            host='localhost',
            port=6379,
            db=0,
            session_ttl=1800,
            memory_ttl=604800
        )
        
        if redis_mgr:
            stats = redis_mgr.get_stats()
            print(f"✓ Redis 连接成功")
            print(f"  - 主机：{stats['host']}:{stats['port']}")
            print(f"  - 内存使用：{stats['used_memory']}")
            print(f"  - 会话数量：{stats['session_count']}")
            return True
        else:
            print("✗ Redis 连接失败")
            return False
            
    except Exception as e:
        print(f"✗ Redis 连接错误：{e}")
        return False


def test_session_management():
    """测试会话管理"""
    print("\n=== 测试会话管理 ===")
    
    redis_mgr = get_redis_manager()
    if not redis_mgr:
        print("✗ Redis 管理器未初始化")
        return False
    
    try:
        # 创建会话
        session_id = f"test_session_{int(time.time())}"
        user_id = "test_user_123"
        
        success = redis_mgr.create_session(session_id, user_id)
        if success:
            print(f"✓ 会话创建成功：{session_id}")
        else:
            print(f"✗ 会话创建失败")
            return False
        
        # 获取会话
        session_data = redis_mgr.get_session(session_id)
        if session_data:
            print(f"✓ 会话获取成功")
            print(f"  - 用户 ID: {session_data['user_id']}")
            print(f"  - 创建时间：{session_data['created_at']}")
            print(f"  - 消息数量：{session_data['message_count']}")
        else:
            print(f"✗ 会话获取失败")
            return False
        
        # 添加消息
        redis_mgr.add_message(session_id, "user", "你好，我想问一下谢恩在哪里")
        redis_mgr.add_message(session_id, "assistant", "谢恩通常在鹈鹕镇的酒吧工作")
        redis_mgr.add_message(session_id, "user", "他喜欢什么？")
        
        print(f"✓ 添加了 3 条消息")
        
        # 获取消息
        messages = redis_mgr.get_messages(session_id, limit=10)
        print(f"✓ 获取到 {len(messages)} 条消息")
        for msg in messages:
            print(f"  - [{msg['role']}]: {msg['content'][:50]}...")
        
        # 获取消息字符串
        history_str = redis_mgr.get_messages_string(session_id)
        print(f"✓ 消息历史字符串长度：{len(history_str)}")
        
        # 删除会话
        redis_mgr.delete_session(session_id)
        print(f"✓ 会话已删除：{session_id}")
        
        # 验证删除
        session_data = redis_mgr.get_session(session_id)
        if not session_data:
            print(f"✓ 确认会话已删除")
        else:
            print(f"✗ 会话删除失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_conversation_manager():
    """测试增强对话管理器"""
    print("\n=== 测试增强对话管理器 ===")
    
    try:
        # 创建增强对话管理器（不需要 vector_store 也能测试基本功能）
        conv_mgr = EnhancedConversationManager(vector_store_manager=None)
        
        # 创建会话
        session_id = conv_mgr.create_session("test_user")
        print(f"✓ 会话创建成功：{session_id}")
        
        # 添加消息
        conv_mgr.add_message(session_id, "user", "星露谷是什么游戏？")
        conv_mgr.add_message(session_id, "assistant", "星露谷物语是一款农场模拟角色扮演游戏")
        conv_mgr.add_message(session_id, "user", "好玩吗？")
        conv_mgr.add_message(session_id, "assistant", "非常好玩，你可以种植、 mining、钓鱼、和村民交朋友")
        
        print(f"✓ 添加了 4 条消息")
        
        # 获取消息
        messages = conv_mgr.get_messages(session_id)
        print(f"✓ 获取到 {len(messages)} 条消息")
        
        # 获取上下文（没有检索文档）
        context = conv_mgr.get_context(session_id, "这个游戏有哪些 NPC", [])
        print(f"✓ 上下文构建成功，长度：{len(context)}")
        print(f"  上下文预览：{context[:200]}...")
        
        # 获取统计信息
        stats = conv_mgr.get_stats()
        print(f"✓ 统计信息:")
        print(f"  - Redis 可用：{stats['redis_available']}")
        print(f"  - 向量存储可用：{stats['vector_store_available']}")
        print(f"  - 短期记忆最大消息数：{stats['max_short_term_messages']}")
        
        # 删除会话
        conv_mgr.delete_session(session_id)
        print(f"✓ 会话已删除")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_importance_calculation():
    """测试重要性评分计算"""
    print("\n=== 测试重要性评分计算 ===")
    
    conv_mgr = EnhancedConversationManager()
    
    test_cases = [
        ("谢恩在哪里", "谢恩在鹈鹕镇的酒吧工作，每天下午 4 点上班", 0.8),
        ("你好", "你好！有什么可以帮助你的吗？", 0.5),
        ("那他会喜欢什么礼物", "他喜欢啤酒和披萨，这些都是他最喜欢的礼物", 0.7),
        ("然后呢", "然后你可以去煤矿森林继续探索", 0.6),
    ]
    
    for query, response, expected_min in test_cases:
        score = conv_mgr._calculate_importance(query, response)
        status = "✓" if score >= expected_min * 0.8 else "⚠"  # 80% 容差
        print(f"{status} 查询：'{query}' -> 评分：{score:.2f}")
    
    return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Redis 集成测试")
    print("=" * 60)
    
    results = []
    
    # 测试 1: Redis 连接
    results.append(("Redis 连接", test_redis_connection()))
    
    # 测试 2: 会话管理
    if results[0][1]:
        results.append(("会话管理", test_session_management()))
    
    # 测试 3: 增强对话管理器
    results.append(("增强对话管理器", test_enhanced_conversation_manager()))
    
    # 测试 4: 重要性评分
    results.append(("重要性评分", test_importance_calculation()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
