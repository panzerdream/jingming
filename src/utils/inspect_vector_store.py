import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from vector_store.vector_store import VectorStoreManager

def inspect_vector_store():
    """查看向量存储的内容"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    vector_store_path = os.path.join(base_dir, 'data', 'vector_db')

    if not os.path.exists(vector_store_path):
        print("向量存储目录不存在")
        return

    vector_store_manager = VectorStoreManager(vector_store_path)
    vector_store = vector_store_manager.load_vector_store()

    if vector_store:
        print("=== 向量存储信息 ===")
        print(f"向量存储路径: {vector_store_path}")

        index_path = os.path.join(vector_store_path, "index.faiss")
        if os.path.exists(index_path):
            print(f"向量索引文件大小: {os.path.getsize(index_path)} bytes")

        docstore_path = os.path.join(vector_store_path, "docstore.json")
        if os.path.exists(docstore_path):
            print(f"文档存储文件大小: {os.path.getsize(docstore_path)} bytes")

        try:
            docs = vector_store.docstore._dict
            print(f"文档数量: {len(docs)}")
            print("\n文档列表:")
            for i, (doc_id, doc) in enumerate(list(docs.items())[:10]):
                content_preview = doc.page_content[:100].replace('\n', ' ')
                print(f"  {i+1}. [{doc_id}] {content_preview}...")
        except Exception as e:
            print(f"读取文档列表失败: {e}")

        print("\n可用搜索方法:")
        print("  - search_dense(query, k=5): 纯向量搜索")
        print("  - search(query, k=5, use_hybrid=True): 混合搜索")
    else:
        print("向量存储未找到或为空")

if __name__ == "__main__":
    inspect_vector_store()