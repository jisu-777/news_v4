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
            trusted_press (Optional[Dict]): 신뢰할 수 있는 언론사 목록

        Returns:
            List[Dict[str, str]]: URL, 제목, 언론사, 발행일을 포함한 딕셔너리 리스트
        """
        # 신뢰할 수 있는 언론사가 지정된 경우 해당 언론사에서만 검색
        if trusted_press:
            return self._search_trusted_press(keyword, k, trusted_press)
        else:
            # 기존 로직: 전체 언론사에서 검색
            return self._search_all_press(keyword, k)

    def _search_trusted_press(self, keyword: str, k: int, 
                             trusted_press: Dict) -> List[Dict[str, str]]:
        """
        신뢰할 수 있는 언론사에서만 키워드로 뉴스 검색
        
        Args:
            keyword: 검색할 키워드
            k: 최대 결과 수
            trusted_press: 신뢰할 수 있는 언론사 목록
            
        Returns:
            신뢰할 수 있는 언론사에서 수집된 뉴스 리스트
        """
        all_results = []
        
        # 각 신뢰할 수 있는 언론사별로 검색
        for press_name, aliases in trusted_press.items():
            print(f"언론사 '{press_name}'에서 '{keyword}' 검색 중...")
            
            for alias in aliases:
                try:
                    # 언론사별 검색 URL 생성 (site: 제한자 사용)
                    search_query = f"{keyword} site:{alias}"
                    encoded_query = quote(search_query)
                    url = f"{self.base_url}/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
                    
                    # 해당 언론사에서 뉴스 검색
                    try:
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        
                        # XML 파싱
                        soup = BeautifulSoup(response.content, 'xml')
                        entries = soup.find_all('item')
                        
                        if entries:
                            # 각 언론사당 균등하게 분배
                            max_per_press = max(1, k // len(trusted_press))
                            
                            for entry in entries[:max_per_press]:
                                title_elem = entry.find('title')
                                link_elem = entry.find('link')
                                pub_date_elem = entry.find('pubDate')
                                
                                if title_elem and link_elem:
                                    all_results.append({
                                        "url": link_elem.text.strip(),
                                        "content": title_elem.text.strip(),
                                        "press": press_name,  # 메인 언론사명 사용
                                        "date": pub_date_elem.text.strip() if pub_date_elem else '날짜 정보 없음',
                                        "source_alias": alias  # 실제 검색에 사용된 별칭
                                    })
                            
                            print(f"  - '{alias}'에서 {len(entries[:max_per_press])}개 수집")
                            break  # 첫 번째 성공한 별칭에서 수집 완료
                    except Exception as e:
                        print(f"  - '{alias}' 검색 중 오류: {str(e)}")
                        continue
                        
                except Exception as e:
                    print(f"  - '{alias}' 검색 중 오류: {str(e)}")
                    continue
        
        # 최대 개수 제한
        final_results = all_results[:k]
        print(f"신뢰할 수 있는 언론사에서 총 {len(final_results)}개 뉴스 수집 완료")
        
        return final_results

    def _search_all_press(self, keyword: Optional[str], k: int) -> List[Dict[str, str]]:
        """
        기존 로직: 전체 언론사에서 뉴스 검색
        """
        # URL 생성
        if keyword:
            encoded_keyword = quote(keyword)
            url = f"{self.base_url}/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
        else:
            url = f"{self.base_url}?hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            # 뉴스 데이터 파싱
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('item')
            
            # 수집된 뉴스가 없는 경우
            if not entries:
                print(f"'{keyword}' 관련 뉴스를 찾을 수 없습니다.")
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
                        "content": title_elem.text.strip(),  # 제목은 그대로 사용
                        "press": press,
                        "date": pub_date_elem.text.strip() if pub_date_elem else '날짜 정보 없음'
                    })

            return result
            
        except Exception as e:
            print(f"뉴스 검색 중 오류 발생: {str(e)}")
            return []