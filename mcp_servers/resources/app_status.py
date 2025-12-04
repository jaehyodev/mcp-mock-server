"""
======================================
앱 상태 리소스 (resources/app_status.py) -> 미구현!
======================================
"""

def register_system_status_resource(mcp):
    """
    주어진 FastMCP 인스턴스에 시스템 설정 및 상태 리소스를 등록합니다.
    
    주의: 현재 이 리소스는 등록만 되어 있으며, LLM이 이 리소스를 인식하고 
    사용자 요청에 응답하는 기능은 아직 구현 또는 활성화되지 않았습니다.
    """
    
    @mcp.resource(
        uri="data://config/settings",
        name="AppConfiguration",
        description="시스템의 현재 배포 버전, 로그 레벨 등 FastMCP 설정(Settings) 전체를 반환합니다. 이는 디버깅이나 상태 확인에 사용됩니다.",
        mime_type="application/json",
        tags={"config", "status"},
    )
    def get_app_config_status() -> dict:
        # mcp.settings는 애플리케이션의 설정값을 담고 있습니다.
        config_data = mcp.settings.to_dict()

        return config_data