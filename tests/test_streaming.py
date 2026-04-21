#!/usr/bin/env python3
"""
测试流式响应
"""

import asyncio
import aiohttp

async def test_streaming_response():
    """测试流式响应"""
    
    url = "http://localhost:8000/api/query"
    data = {"query": "测试流式响应"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            print(f"状态码: {response.status}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            # 读取流式响应
            async for chunk in response.content.iter_chunked(1024):
                print(f"收到块: {chunk.decode('utf-8')}")

if __name__ == "__main__":
    asyncio.run(test_streaming_response())