from mcp_servers.config.settings import ORACLE_DSN, ORACLE_PASSWORD, ORACLE_USER
import oracledb

# 파일 최상단에 선언된 변수는 해당 파일(모듈) 전체를 범위로 하는 전역 변수로 간주
db_pool = None

def initialize_db_pool():
  """
  FastMCP 서버 시작 시 Oracle DB 연결 풀을 초기화합니다.
  """

  global db_pool # 기존의 전역 변수 이용
  
  if db_pool is not None:
    return db_pool
  
  try:
    # DB 연결 풀 생성
    db_pool = oracledb.create_pool(
      user=ORACLE_USER,
      password=ORACLE_PASSWORD,
      dsn=ORACLE_DSN,
      min=2,
      max=4,
      increment=1
    )
    print("🎉 database >> DB connection pool 초기화 성공.")
    return db_pool
  except oracledb.Error as e:
    print(f"❌ database >> DB pool 초기화 에러. >> {e}")
    return None

def get_db_connection():
  """
  DB 연결 풀에서 Connection 객체를 획득합니다.
  """

  global db_pool # 기존의 전역 변수 이용

  if db_pool is None:
    print('db_pool이 null 입니다.')
    db_pool = initialize_db_pool()
    print('db_pool이 초기화되었습니다. db_pool >> ', db_pool)

    if db_pool is None:
      raise Exception("❌ database >> DB pool 사용 불가.")
    
  # DB pool에서 연결 획득 (반납 필수)
  return db_pool.acquire()
  
# 서버 시작 시 DB pool 초기화
initialize_db_pool()