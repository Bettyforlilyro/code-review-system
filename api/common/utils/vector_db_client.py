import chromadb
import uuid
from api.common.config.system_config import vector_db_config


class VectorDBClient:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=vector_db_config['db_path'])
        self.test_collection_name = "test_collection"

    def health_check(self):
        """测试向量数据库连接和基本操作"""
        try:
            # 创建测试集合
            collection = self.client.get_or_create_collection(self.test_collection_name)

            # 测试数据
            test_documents = [
                "这是一个测试文档，用于验证向量数据库功能。",
                "机器学习是人工智能的重要分支。",
                "Python是一种流行的编程语言。"
            ]
            test_metadatas = [{"type": "test", "source": "health_check"} for _ in test_documents]
            test_ids = [str(uuid.uuid4()) for _ in test_documents]

            # 添加文档
            collection.add(
                documents=test_documents,
                metadatas=test_metadatas,
                ids=test_ids
            )

            # 查询测试
            results = collection.query(
                query_texts=["编程语言"],
                n_results=2
            )

            # 清理测试数据
            collection.delete(ids=test_ids)

            return {
                'status': 'healthy',
                'operation': 'read_write_query',
                'query_results_count': len(results['documents'][0]) if results['documents'] else 0
            }

        except Exception as e:
            raise Exception(f"向量数据库错误: {str(e)}")

    def test_rag_functionality(self):
        """测试RAG相关功能"""
        try:
            collection = self.client.get_or_create_collection("knowledge_base_test")

            # 添加一些技术文档用于测试
            tech_docs = [
                "Flask是一个轻量级的Python Web框架。",
                "Celery用于处理异步任务和定时任务。",
                "PostgreSQL是一个功能强大的开源关系数据库。",
                "Redis是一个内存中的数据结构存储，用作数据库、缓存和消息代理。"
            ]

            doc_ids = [f"tech_doc_{i}" for i in range(len(tech_docs))]
            collection.add(
                documents=tech_docs,
                ids=doc_ids,
                metadatas=[{"category": "technology"} for _ in tech_docs]
            )

            # 测试语义搜索
            results = collection.query(
                query_texts=["Web框架"],
                n_results=3
            )

            return {
                'status': 'success',
                'documents_added': len(tech_docs),
                'search_results': {
                    'query': 'Web框架',
                    'found_documents': results['documents'][0] if results['documents'] else [],
                    'distances': results['distances'][0] if results['distances'] else []
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            # 清理测试数据
            try:
                collection.delete(ids=doc_ids)
            except:
                pass