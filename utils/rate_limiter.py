from datetime import datetime, timedelta
from typing import List
import asyncio

"""
==================================================
유틸리티 모듈: 비동기 속도 제한기 (RateLimiter)
==================================================
이 파일은 지정된 시간 단위(1분) 동안의 요청 횟수를 제한하여 API 호출이나 
스크레이핑 시의 과부하 및 봇 감지를 방지하는 클래스를 정의합니다.

주요 역할:
1. 1분 윈도우 내의 요청 기록을 관리합니다.
2. 요청 횟수가 임계값을 초과하면, 가장 오래된 요청이 만료될 때까지 비동기적으로 대기합니다.
"""

class RateLimiter:
    """
    고정 윈도우(Fixed Window) 방식과 유사하게 요청 기록을 관리하여 
    API 호출 속도를 제한하는 클래스입니다.
    """

    def __init__(self, requests_per_minute: int = 30):
        """
        RateLimiter를 초기화합니다.
        
        Args:
            requests_per_minute (int): 1분 동안 허용되는 최대 요청 횟수. (기본값 30)
        """

        self.requests_per_minute = requests_per_minute
        # 요청 발생 시간을 저장하는 리스트 (list[datetime]). 이 리스트의 길이가 요청 횟수가 됩니다.
        self.requests: List[datetime] = [] 

    async def acquire(self):
        """
        요청 횟수 제한을 획득(Acquire)합니다. 
        제한을 초과하면 1분 윈도우가 재설정될 때까지 비동기적으로 대기합니다.
        """

        now = datetime.now()
        
        # 1. 윈도우 정리 (Clear Expired Requests)
        # - 현재 시점에서 1분(60초)보다 오래된 요청 기록은 제거합니다.
        one_minute_ago = now - timedelta(minutes=1)
        self.requests = [
            req for req in self.requests if req > one_minute_ago
        ]

        # 2. 요청 횟수 확인 및 대기 로직 (Check Limit and Wait)
        # - 현재 윈도우 내의 요청 횟수가 허용된 최대치와 같거나 초과했는지 확인합니다.
        if len(self.requests) >= self.requests_per_minute:
            # 첫 번째(가장 오래된) 요청이 발생한 시점부터 60초가 될 때까지 남은 시간을 계산합니다.
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            
            # 대기 시간이 양수일 경우만 대기합니다.
            if wait_time > 0:
                # 비동기적으로 대기하여 요청 윈도우가 재설정되기를 기다립니다.
                await asyncio.sleep(wait_time)

        # 3. 새로운 요청 기록 (Record New Request)
        # - 제한을 통과하거나 대기 후, 현재 요청 시간을 기록하여 요청 횟수를 1 증가시킵니다.
        self.requests.append(datetime.now())