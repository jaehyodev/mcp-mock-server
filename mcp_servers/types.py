from dataclasses import dataclass
from mcp_servers.db.oracle import OracleManager

@dataclass
class AppContext:
    oracle: OracleManager
