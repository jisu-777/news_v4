import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from typing import List, Dict, Optional
import re
from datetime import datetime


class GoogleNews:
    """
    구글 뉴스를 검색하고 결과를 반환하는 클래스입니다.
    """

    def __init__(self):
        """GoogleNews 클래스를 초기화합니다."""
        self.base_url = "https://news.google.com/rss"

    def search_by_keyword(self, keyword: Optional[str] = None, k: int = 50, 
                         trusted_press: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        키워드로 뉴스를 검색합니다.

        Args:
            keyword (Optional[str]): 검색할 키워드 (기본값: None)
            k (int): 검색할 뉴스의 최대 개수 (기본값: 50)
            trusted_press (Optional[Dict]): 신뢰할 수 있는 언론사 목록 (사용하지 않음)

        Returns:
            List[Dict[str, str]]: URL, 제목, 언론사, 발행일을 포함한 딕셔너리 리스트
        """
        # 통합 검색만 사용 (순차 검색 제거)
        if keyword:
            return self.search_all_press_unified(keyword, k)
        else:
            return self.search_all_press_unified("", k)

    def search_by_keywords_or(self, keywords_query: str, k: int = 100, 
                             trusted_press: Optional[Dict] = None) -> List[Dict[str, str]]:
        """
        OR 조건으로 여러 키워드를 한번에 검색합니다.

        Args:
            keywords_query (str): "키워드1 OR 키워드2 OR 키워드3" 형태의 쿼리
            k (int): 검색할 뉴스의 최대 개수 (기본값: 100)
            trusted_press (Optional[Dict]): 신뢰할 수 있는 언론사 목록 (사용하지 않음)

        Returns:
            List[Dict[str, str]]: URL, 제목, 언론사, 발행일을 포함한 딕셔너리 리스트
        """
        # 통합 검색만 사용 (순차 검색 제거)
        return self.search_all_press_unified(keywords_query, k)

    def search_all_press_unified(self, keywords_query: str, k: int = 200) -> List[Dict[str, str]]:
        """
        전체 언론사에서 한번에 검색하여 빠른 수집 (GPT로 유효 언론사 필터링 예정)
        
        Args:
            keywords_query: "키워드1 OR 키워드2 OR 키워드3" 형태의 쿼리
            k: 검색할 뉴스의 최대 개수 (기본값: 200)
            
        Returns:
            URL, 제목, 언론사, 발행일을 포함한 딕셔너리 리스트
        """
        print(f"전체 언론사에서 통합 검색 시작: {keywords_query}")
        
        try:
            # 전체 언론사에서 OR 검색 URL 생성
            encoded_query = quote(keywords_query)
            url = f"{self.base_url}/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
            
            print(f"검색 URL: {url}")
            
            # 뉴스 데이터 파싱
            response = requests.get(url, timeout=15)  # 타임아웃 증가
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('item')
            
            print(f"전체 검색 결과: {len(entries)}개 발견")
            
            # 수집된 뉴스가 없는 경우
            if not entries:
                print(f"'{keywords_query}' 관련 뉴스를 찾을 수 없습니다.")
                return []
                
            # 결과 가공
            result = []
            for entry in entries[:k]:
                title_elem = entry.find('title')
                link_elem = entry.find('link')
                pub_date_elem = entry.find('pubDate')
                source_elem = entry.find('source')
                
                if title_elem and link_elem:
                    # source 태그에서 직접 언론사 정보 추출
                    press = source_elem.text.strip() if source_elem else '알 수 없음'
                    
                    result.append({
                        "url": link_elem.text.strip(), 
                        "content": title_elem.text.strip(),
                        "press": press,
                        "date": pub_date_elem.text.strip() if pub_date_elem else '날짜 정보 없음'
                    })

            print(f"통합 검색 완료: {len(result)}개 뉴스 수집")
            return result
            
        except Exception as e:
            print(f"통합 뉴스 검색 중 오류 발생: {str(e)}")
            return []