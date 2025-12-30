from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

# 컬렉션 이름 지정
COLLECTION_NAME = 'my_collection'
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

client = MilvusClient(
    uri = "http://localhost:19530"
)
def milvus_search(intent: str, top_k: int = 1) -> ToolResult: 
    """
    Milvus에서 쿼리와 유사한 SQL 템플릿을 검색합니다.
    Args:
        client (MilvusClient): MilvusClient 객체.
        intent (str): 검색할 쿼리 문자열.
        top_k (int): 검색할 상위 K개 결과 수.
    Returns:
        List[Dict]: 유사한 SQL 템플릿 목록.
    """

    print(f"[Tool] [milvus_search] intent: {intent}")

    vector = model.encode(intent).tolist()

    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[vector],
        anns_field="vector",
        limit=top_k,
        search_params={
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        },
        output_fields=['intent_description', 'sql_template']
    )

    print(f"results: {results}")

    if not results or not results[0]:
        return ToolResult(
            content=[TextContent(type="text", text="No SQL template found")],
            structured_content=None
        )

    hit = results[0][0]

    intent_description = hit["entity"]["intent_description"]
    sql_template = hit["entity"]["sql_template"]
    score = hit["distance"]

    print(f"[Tool] [milvus_search] 검색 결과 - 의도: '{intent_description}', 유사도: {score}")

    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=sql_template
            )
        ],
        structured_content={
            "intent_description": intent_description,
            "sql_template": sql_template,
            "similarity_score": score
        }
    )