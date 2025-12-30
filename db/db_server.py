from contextlib import asynccontextmanager
from fastapi import FastAPI

from db.milvus_init import create_milvus_client, initialize_milvus_collection, insert_data
from db.oracle_init import initialize_oracle_pool
from db.oracle_schema import create_oracle_tables, insert_deposit, insert_loan

# Lifespan 함수 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ------------------ Startup 로직 (서버 시작 시) ------------------
    print("----- [STARTUP] Oracle Pool 초기화 시작 -----")
    try:
        initialize_oracle_pool()
    except Exception as e:
        print(f"❌ [STARTUP] Oracle DB 초기화 실패: {e}")
        raise
    print("----- [STARTUP] Oracle Pool 초기화 완료 -----")

    print("----- [STARTUP] Milvus 리소스 초기화 시작 -----")
    try:
        # 1. 클라이언트 객체 생성
        client = create_milvus_client()
    
        # 2. 클라이언트 객체를 앱의 상태(state)에 저장 (전역 변수 역할)
        # 각 워커 프로세스가 독립적으로 이 객체를 저장하고 사용합니다.
        app.state.milvus_client = client

        # 3. 컬렉션 초기화 실행
        initialize_milvus_collection(client)

        print("----- [STARTUP] Milvus 준비 완료 -----")

        # 4. Oracle 예시 데이터 입력
        print("----- [STARTUP] Oracle 데이터 입력 시작 -----")
        create_oracle_tables()
        insert_deposit("Alice", 1000)
        insert_deposit("Bob", 1500)
        insert_deposit("Charlie", 2000)
        insert_loan("Kim", 100000)
        insert_loan("Lee", 150000)
        insert_loan("Park", 300000)
        print("----- [STARTUP] Oracle 데이터 입력 완료 -----")
        
        # 5. Milvus 예시 데이터 입력
        print("----- [STARTUP] Milvus 데이터 입력 시작 -----")

        # 의도 설명과 SQL 템플릿을 명확히 구분하여 저장
        insert_data(
            client,
            intent_description="계좌 잔액 조회: 특정 계좌 소유자의 예금 잔액을 확인합니다",
            sql_template="SELECT balance FROM deposit WHERE account_holder = :account_holder"
        )
        insert_data(
            client,
            intent_description="대출 금액 조회: 특정 채무자가 빌린 대출 금액을 확인합니다",
            sql_template="SELECT money FROM loan WHERE borrower = :borrower"
        )

        print("----- [STARTUP] Milvus 데이터 입력 완료 -----")

    except Exception as e:
        print(f'----- [STARTUP] Milvus 초기화 실패: {e} -----')
        raise # raise는 무엇인가

    # 서버 동작
    yield

    # 서버 종료 시 정리 로직
    print("----- [SHUTDOWN] Milvus 리소스 정리 시작 -----")
    client_to_close = app.state.milvus_client
    if client_to_close:
        client_to_close.close()
        print("MilvusClient 연결이 명시적으로 정리되었습니다.")
    
    # state에서 객체 제거
    del app.state.milvus_client
    print("----- [SHUTDOWN] Milvus 정리 완료 -----")

app = FastAPI(lifespan=lifespan)