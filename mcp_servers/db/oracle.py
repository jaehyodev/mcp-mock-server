from mcp_servers.config.settings import ORACLE_DSN, ORACLE_PASSWORD, ORACLE_USER
import oracledb


class OracleManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """
        Oracle Connection Pool 생성
        """
        print(f"Connecting to Oracle ({ORACLE_DSN})...")
        self.pool = oracledb.create_pool_async(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
            min=2,
            max=10,
            increment=1
        )
        return self
    
    async def disconnect(self):
        """
        Oracle Connection Pool 해제
        """
        if self.pool:
            print("[mcp_server] Closing Oracle Connection Pool...")
            await self.pool.close()
    
    async def get_pool(self):
        if not self.pool:
            await self.connect()
        return self.pool