from pymilvus import DataType, MilvusClient
from sentence_transformers import SentenceTransformer
from db.config.settings import MILVUS_URI

# 컬렉션 이름 지정
COLLECTION_NAME = 'my_collection'
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def create_milvus_client() -> MilvusClient:
    """
    MilvusClient 객체를 생성합니다.
    """

    # 1. Milvus DB 연결
    return MilvusClient(
        uri=MILVUS_URI,
        timeout=1000
    )

def initialize_milvus_collection(client: MilvusClient):
    """
    Milvus 컬렉션이 없으면 생성하고 로드합니다.
    컬렉션이 존재하는 경우 기존 컬렉션을 삭제하고 재생성합니다.
    Args:
        client (MilvusClient): MilvusClient 객체.
    """
    if client.has_collection(COLLECTION_NAME):
        print(f'[DB - Milvus] {COLLECTION_NAME} 컬렉션이 이미 존재합니다. 기존 컬렉션 삭제 후 재생성합니다.')
        client.drop_collection(COLLECTION_NAME)

    # 2. 스키마 생성
    schema = MilvusClient.create_schema(
        auto_id=True,
        enable_dynamic_field=True   
    )

    # 3. 필드 추가
    schema.add_field('id', DataType.INT64, is_primary=True, auto_id=True)
    schema.add_field('vector', DataType.FLOAT_VECTOR, dim=384)
    schema.add_field('intent_description', DataType.VARCHAR, max_length=512)  # 검색용 의도 설명
    schema.add_field('sql_template', DataType.VARCHAR, max_length=512)  # 실제 SQL 템플릿

    # 4. 인덱스 설정
    # - AUTOINDEX: 자동 인덱스 설정, Milvus가 데이터 기반으로 최적 타입 자동 선택
    # - HNSW, IVF_FLAT: 수동 인덱스 설정 (HNSW: 그래프 기반, IVF_FLAT: 클러스터링 기반)
    # 스칼라 필드는 인덱스 유형만 설정하면 된다.
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name='id',
        index_type='AUTOINDEX'
    )
    # 벡터 필드는 인덱스 유형과 메트릭 유형을 모두 설정해야 한다.
    index_params.add_index(
        field_name='vector',
        index_type='AUTOINDEX',
        metric_type='COSINE' # 벡터 유사성 측정 방식 (코사인 유사도 사용)
    )

    # 5. 컬렉션 생성
    # - 인덱스 매개변수를 사용하여 컬렉션을 생성한 경우, Milvus는 컬렉션 생성 시 자동으로 해당 컬렉션을 로드한다.
    # - 인덱스 매개변수 없이 컬렉션을 생성한 경우, Milvus는 컬렉션 생성 시 해당 컬렉션을 로드하지 않습니다.
    # - shard: 컬렉션을 수평으로 분할한 것, 각 샤드는 데이터 입력 채널에 해당한다.
    ## - 기본적으로 모든 컬렉션에는 하나의 샤드가 있다. 샤드 수를 늘리면 데이터 삽입 속도와 처리량이 좋아진다.
    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
        # num_shards=1 # 기본값 1개
        # enable_mmap=True # 기본값 true, mmap 활성화시 필요한 부분만 메모리에 로드, 비활성화시 전체 파일 메모리에 로드
        properties={
            'collection.ttl.seconds': 86400 # 데이터 삽입 후 삭제되기까지 시간(초)
        }
        # consistency_level='Bounded' # 일관성 수준: 최신 데이터 보장 옵션
        # - Strong: 최신 데이터가 반드시 모든 노드에 반영된 후 검색
        # - Session: 동일한 세션에서 삽입한 데이터는 반드시 반영 (특정 사용자 기준으로 일관성 유지)
        # - Bounded: 기본값, 일정 시간 이내의 최신성만 보장
        # - Eventually: 최신 데이터는 일정 시간이 지나면 반영
    )

    # 6. 로드 상태 확인 (데이터 검색 전 메모리에 로드되었는 지 확인)
    res = client.get_load_state(
        collection_name=COLLECTION_NAME
    )

    print(f'[DB] Milvus load state: {res}')


def insert_data(client: MilvusClient, intent_description: str, sql_template: str):
    """
    Milvus 컬렉션에 벡터 데이터를 삽입합니다.
    이미 존재하는 데이터의 경우는 삽입하지 않습니다.
    Args:
        client (MilvusClient): MilvusClient 객체.
        intent_description (str): 사용자 의도 설명 (예: "계좌 잔액 조회", "대출 금액 조회")
        sql_template (str): 실행할 SQL 템플릿.
    """

    existing = client.query(
        collection_name=COLLECTION_NAME,
        filter=f'sql_template == "{sql_template}"',
        output_fields=['id']
    )

    if len(existing) > 0:
        print(f'[DB - Milvus] 이미 존재하는 쿼리입니다: {existing[0]["id"]} {sql_template}')
        return

    # 의도 설명으로 벡터 임베딩 생성 (이게 핵심!)
    vector = model.encode(intent_description).tolist()

    data = [{
        'vector': vector,
        'intent_description': intent_description,
        'sql_template': sql_template
    }]

    insert_result = client.insert(
        collection_name=COLLECTION_NAME,
        data=data
    )

    print(f'[DB - Milvus] 삽입 완료 - 의도: "{intent_description}" | SQL: "{sql_template}"')