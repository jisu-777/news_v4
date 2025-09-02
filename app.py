import streamlit as st
import requests
from datetime import datetime, timedelta, timezone, time
import json
import openai
import os
import re
from urllib.parse import urlparse
from config import KEYWORD_CATEGORIES, NAVER_API_SETTINGS

# 페이지 설정
st.set_page_config(
    page_title="PwC 뉴스 분석기",
    page_icon="logo_orange.png",
    layout="wide"
)

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

# 화이트리스트 필터링 제거 - GPT가 언론사 신뢰도를 판단하도록 함

# 커스텀 CSS
st.markdown("""
<style>
    .main-title {
        color: #d04a02;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 30px;
    }
    .category-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        border-left: 4px solid #d04a02;
    }
    .news-item {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .news-title {
        font-weight: 600;
        font-size: 1.1rem;
        color: #333;
        margin-bottom: 8px;
    }
    .news-meta {
        color: #666;
        font-size: 0.9rem;
        margin: 5px 0;
    }
    .news-url {
        color: #0077b6;
        font-size: 0.9rem;
        word-break: break-all;
    }
    .analysis-section {
        background-color: #f8f9fa;
        border-left: 4px solid #d04a02;
        padding: 20px;
        margin: 20px 0;
        border-radius: 5px;
    }
    .sidebar-section {
        background-color: #f0f0f0;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def collect_news_from_naver_api(category_keywords, start_dt, end_dt, category_name="", max_per_keyword=50):
    """네이버 뉴스 API에서 카테고리별 키워드로 뉴스 수집 - 2개 키워드씩 묶어서 검색"""
    all_news = []
    
    # 네이버 API 키 확인
    client_id = NAVER_API_SETTINGS["client_id"]
    client_secret = NAVER_API_SETTINGS["client_secret"]
    
    if not client_id or not client_secret:
        st.error("⚠️ 네이버 API 키가 설정되지 않았습니다. 환경변수 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요.")
        return []
    
    # API 헤더 설정
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    # 키워드 처리 방식 (카테고리별 다르게 적용)
    if category_name in ["삼일PwC", "경쟁사"]:
        # 삼일PwC, 경쟁사: 개별 키워드로 검색
        keyword_pairs = [(keyword, None) for keyword in category_keywords]
    else:
        # 다른 카테고리: 2개씩 묶어서 OR 조건으로 검색
        keyword_pairs = []
        for i in range(0, len(category_keywords), 2):
            if i + 1 < len(category_keywords):
                keyword_pairs.append((category_keywords[i], category_keywords[i + 1]))
            else:
                keyword_pairs.append((category_keywords[i], None))
    
    for keyword1, keyword2 in keyword_pairs:
        try:
            # 검색 쿼리 생성 (카테고리별 다르게 적용)
            if category_name in ["삼일PwC", "경쟁사"]:
                # 삼일PwC, 경쟁사: 개별 키워드
                query = keyword1
                keywords = [keyword1]
            else:
                # 다른 카테고리: 2개 키워드를 OR 조건으로 검색
                if keyword2:
                    query = f"{keyword1} OR {keyword2}"
                    keywords = [keyword1, keyword2]
                else:
                    query = keyword1
                    keywords = [keyword1]
            
            # 페이지네이션을 통한 네이버 뉴스 API 호출
            all_items = []
            target_count = max_per_keyword * 2  # 목표 수집 개수
            current_start = 1
            
            while len(all_items) < target_count:
                params = {
                    "query": query,
                    "display": min(100, target_count - len(all_items)),  # 남은 개수만큼 요청
                    "start": current_start,
                    "sort": NAVER_API_SETTINGS["sort"]
                }
                
                response = requests.get(
                    NAVER_API_SETTINGS["base_url"],
                    headers=headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code != 200:
                    st.warning(f"'{query}' 검색 중 API 오류: {response.status_code}")
                    break
                
                # JSON 응답 파싱
                data = response.json()
                items = data.get('items', [])
                
                if not items:  # 더 이상 결과가 없으면 중단
                    break
                
                all_items.extend(items)
                current_start += len(items)
                
                # API 호출 간격 조절
                import time
                time.sleep(0.1)
            
            items = all_items
            

            

            
            # 날짜 필터링 통계를 위한 카운터
            total_items = len(items)
            date_filtered_count = 0
            
            for item in items:
                
                # 날짜 파싱 (네이버 API는 RFC 822 형식)
                try:
                    date_str = item.get('pubDate', '')
                    if date_str:
                        # RFC 822 형식 파싱: "Wed, 15 Jan 2025 10:30:00 +0900"
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(date_str)
                        
                        # ✅ tz-aware면 그대로 KST로 변환, naive면 UTC로 가정 후 KST로
                        if pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc).astimezone(KST)
                        else:
                            pub_date = pub_date.astimezone(KST)
                    else:
                        pub_date = datetime.now(KST)
                except Exception as date_error:
                    # 날짜 파싱 실패 시 현재 시간 사용
                    pub_date = datetime.now(KST)
                

                
                # 날짜 및 시간 범위 확인 (카테고리별 다르게 적용)
                if category_name in ["삼일PwC", "경쟁사"]:
                    # 삼일PwC, 경쟁사: 날짜만 비교 (시간 무시)
                    pub_date_only = pub_date.date()
                    start_date_only = start_dt.date()
                    end_date_only = end_dt.date()
                    date_in_range = start_date_only <= pub_date_only <= end_date_only
                else:
                    # 다른 카테고리: 시간까지 비교
                    date_in_range = start_dt <= pub_date <= end_dt
                
                if date_in_range:
                    date_filtered_count += 1
                    # 제목과 요약 정리
                    title = clean_html_entities(item.get('title', ''))
                    summary = clean_html_entities(item.get('description', ''))
                    
                    # 검색 쿼리를 키워드로 사용
                    search_keyword = query  # "삼일PWC OR 삼일회계법인" 형태
                    
                    # 언론사 정보 추출 (originallink 우선 사용)
                    press_name = extract_press_from_url(
                        url=item.get('link', ''),
                        originallink=item.get('originallink')
                    )
                    
                    news_item = {
                        'title': title,
                        'url': item.get('link', ''),
                        'date': pub_date.strftime('%Y-%m-%d'),
                        'summary': summary,
                        'keyword': search_keyword,
                        'press': press_name
                    }
                    all_news.append(news_item)
                    

                    
        except Exception as e:
            st.warning(f"'{query if 'query' in locals() else keyword1}' 검색 중 오류: {str(e)}")
            continue
    

    
    return all_news

def clean_html_entities(text):
    """HTML 엔티티를 정리하는 함수"""
    if not text:
        return ""
    
    # HTML 태그 제거
    import re
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # HTML 엔티티 디코딩
    clean_text = clean_text.replace('&quot;', '"')
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    clean_text = clean_text.replace('&apos;', "'")
    
    # 연속된 공백 정리
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

def extract_press_from_url(url: str, originallink: str | None = None) -> str:
    """
    URL에서 언론사 정보를 추출.
    - originallink가 있으면 우선 사용 (네이버 뉴스 원문 복원)
    - 네이버 뉴스 링크는 별도 처리
    - 하드코딩 매핑 + 베이스도메인 매핑
    - 안전한 fallback
    """
    if not url and not originallink:
        return "언론사 정보 없음"

    from urllib.parse import urlparse, parse_qs

    # 1) originallink가 있으면 그걸로 교체 (정확도 ↑)
    target_url = originallink or url
    try:
        parsed = urlparse(target_url)
        domain = parsed.netloc.lower()

        # www.만 제거한 베이스 도메인 (서브도메인 과대일치 방지)
        base = domain[4:] if domain.startswith("www.") else domain

        # 네이버 뉴스 특수 처리: news.naver.com / n.news.naver.com / mnews.naver.com
        if base in {"news.naver.com", "n.news.naver.com", "m.news.naver.com", "mnews.naver.com"}:
            # 네이버 기사 URL엔 보통 oid(언론사 id) / aid가 포함됨
            # 예: https://n.news.naver.com/mnews/article/001/0012345678
            # path 분해해서 article/<oid>/<aid> 패턴 탐색
            path_parts = [p for p in parsed.path.split("/") if p]
            press_from_oid = None
            if "article" in path_parts:
                try:
                    i = path_parts.index("article")
                    oid = path_parts[i + 1]
                    # 최소 맵만 넣어 실사용: (필요에 따라 확장)
                    OID_MAP = {
                        "001": "연합뉴스",
                        "009": "매일경제",
                        "015": "한국경제",
                        "020": "동아일보",
                        "023": "조선일보",
                        "024": "매경이코노미",
                        "025": "중앙일보",
                        "032": "경향신문",
                        "056": "KBS",
                        "079": "노컷뉴스",
                        "119": "데일리안",
                        "277": "아시아경제",
                        "421": "뉴스1",
                        # 필요 언론사 계속 보강
                    }
                    press_from_oid = OID_MAP.get(oid)
                except Exception:
                    pass

            # oid로 못 찾았으면 네이버 링크에선 명확히 단정하지 않음
            return press_from_oid or "네이버 뉴스(원문 확인)"

        # 2) 주요 언론사 매핑 (서브도메인 포함 매칭은 base 기준으로)
        PRESS_MAP = {
            "chosun.com": "조선일보",
            "biz.chosun.com": "조선일보",
            "joongang.co.kr": "중앙일보",
            "donga.com": "동아일보",
            "hankyung.com": "한국경제",
            "magazine.hankyung.com": "한국경제",
            "mk.co.kr": "매일경제",
            "yna.co.kr": "연합뉴스",
            "fnnews.com": "파이낸셜뉴스",
            "edaily.co.kr": "이데일리",
            "asiae.co.kr": "아시아경제",
            "newspim.com": "뉴스핌",
            "newsis.com": "뉴시스",
            "heraldcorp.com": "헤럴드경제",
            "thebell.co.kr": "더벨",
            "businesspost.co.kr": "비즈니스포스트",
            "mt.co.kr": "머니투데이",
            "dailypharm.com": "데일리팜",
            "it.chosun.com": "IT조선",
            "itchosun.com": "IT조선",
        }

        # 정확/부분 매칭 (base가 map key이거나, base가 key의 서브도메인인 경우)
        if base in PRESS_MAP:
            return PRESS_MAP[base]
        # base가 예: it.chosun.com 이고 키가 chosun.com인 경우를 커버
        for k, v in PRESS_MAP.items():
            if base.endswith(k):
                return v

        # 3) originallink가 없다면, Naver Search API의 `link`에만 의존하므로
        #    이 경우엔 원문을 못찾을 수 있음 → target_url이 naver가 아니면 base 반환
        #    (단, 의미없는 첫 세그먼트 title()은 지양)
        return base

    except Exception:
        return "언론사 정보 없음"





def analyze_news_with_ai(news_list, category_name):
    """AI를 사용하여 뉴스 분석 및 언론사 판별 - 카테고리별 프롬프트 적용"""
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # 뉴스 목록을 텍스트로 변환
        news_text = ""
        for i, news in enumerate(news_list, 1):
            news_text += f"{i}. 제목: {news.get('title', '제목 없음')}\n"
            news_text += f"   요약: {news.get('summary', '요약 없음')}\n"
            news_text += f"   링크: {news.get('url', '링크 없음')}\n"
            news_text += f"   언론사: {news.get('press', '언론사 정보 없음')}\n"
            news_text += f"   날짜: {news.get('date', '날짜 없음')}\n"
            news_text += f"   검색키워드: {news.get('keyword', '키워드 없음')}\n\n"
        
        # 카테고리별 프롬프트 설정
        if category_name == "삼일PwC":
            # 삼일PwC 전용 상세 프롬프트
            analysis_prompt = f"""
당신은 회계법인 전문 뉴스 분석가입니다. 삼일PwC 관련 뉴스를 분석하여 중요한 뉴스만 선별해주세요.
무조건 1건의 기사는 포함해야합니다..

단 중복 내용의 기사는 제외해주세요





**제외(N)**
- 스포츠단 기사 (야구단, 축구단, 선수/감독 등)

- 단순 시스템 장애, 버그, 서비스 오류

- 목표주가 기사

- 광고성/스폰서/외국어 기사

1


**중요**: 
- **무조건 1개 이상의 뉴스를 반드시 선별해야 합니다.** 1개 미만으로 선별하면 안됩니다.
- 가능하면 5개까지 선별하되, 같은 이슈 중복 금지 원칙을 지켜 서로 다른 이슈만 담으세요.
- 내용 중복·이슈 중복 모두 금지.
- 언론사명은 정확하게 표기, 선별 이유는 간단명료하게.
- 삼일PwC 관련성이 명확한 뉴스를 우선.

다음 뉴스 목록에서 삼일PwC 관련성이 명확하고 중요한 뉴스만 선별해주세요:

{news_text}

선별된 뉴스를 다음과 같이 나열하세요:

[뉴스 제목]
선별 이유: [간단한 선별 이유]
링크: [뉴스 URL]

[뉴스 제목]
선별 이유: [간단한 선별 이유]
링크: [뉴스 URL]

...
"""
        elif category_name == "경쟁사":
            # 경쟁사 전용 상세 프롬프트
            analysis_prompt = f"""
당신은 회계법인 전문 뉴스 분석가입니다. 경쟁 회계법인(한영EY, 삼정KPMG, Deloitte, 안진회계법인 등) 관련 뉴스를 분석하여 중요한 뉴스만 선별해주세요. 무조건 1건의 기사는 남겨야합니다.

단 중복 내용의 기사는 제외해주세요



**제외(N)**
- 스포츠단 기사 (야구단, 축구단, 선수/감독 등)
- 신제품 홍보/사회공헌/ESG/기부 기사
- 단순 시스템 장애, 버그, 서비스 오류
- 기술 성능/품질/테스트 홍보 기사
- 목표주가 기사
- 단순 언급, 경력 소개, 배경 문장 수준
- 광고성/스폰서/외국어 기사


**중요**
- 무조건 1개 이상은 반드시 선별해야 함
- 가능하면 5–10개까지 선별하되, 같은 이슈 중복은 금지
- 기사 내용도 중복되면 안 됨
- 언론사명은 정확하게, 선별 이유는 간단명료하게 작성

다음 뉴스 목록에서 경쟁 회계법인 관련성이 명확하고 중요한 뉴스만 선별해주세요:

{news_text}

선별된 뉴스를 다음과 같이 나열하세요:

[뉴스 제목]
선별 이유: [간단한 선별 이유]
링크: [뉴스 URL]

[뉴스 제목]
선별 이유: [간단한 선별 이유]
링크: [뉴스 URL]

...
"""
        else:
            # 다른 카테고리용 일반 프롬프트
            analysis_prompt = f"""
다음은 '{category_name}' 카테고리로 수집된 뉴스 목록입니다.



[선별 기준]
- 재무/실적 정보 (매출, 영업이익, 순이익, 투자계획)
- 회계/감사 관련 (회계처리 변경, 감사의견, 회계법인 소식)
- 비즈니스 중요도 (신규사업, M&A, 조직변화, 경영진 인사)
- 산업 동향 (정책, 규제, 시장 변화)

"다음 조건 중 하나라도 해당하는 뉴스는 제외하세요:

1. 경기 관련 내용
   - 스포츠단 관련 내용
   - 키워드: 야구단, 축구단, 구단, KBO, 프로야구, 감독, 선수

2. 신제품 홍보, 사회공헌, ESG, 기부 등
   - 키워드: 출시, 기부, 환경 캠페인, 브랜드 홍보, 사회공헌, 나눔, 캠페인 진행, 소비자 반응

3. 단순 시스템 장애, 버그, 서비스 오류
   - 키워드: 일시 중단, 접속 오류, 서비스 오류, 버그, 점검 중, 업데이트 실패

4. 기술 성능, 품질, 테스트 관련 보도
   - 키워드: 우수성 입증, 기술력 인정, 성능 비교, 품질 테스트, 기술 성과
   
5. 목표가 관련 보도
   - 키워드: 목표가, 목표주가 달성, 목표주가 도달, 목표주가 향상, 목표가↑, 목표가

    기사 내용의 완성도
   - 더 자세한 정보를 포함한 기사 우선
   - 주요 인용문이나 전문가 의견이 포함된 기사 우선
   - 단순 보도보다 분석적 내용이 포함된 기사 우선

다음 기준에 해당하는 뉴스가 있다면 반드시 선택해야 합니다:

1. 재무/실적 관련 정보 (최우선 순위)
   - 매출, 영업이익, 순이익 등 실적 발표
   - 재무제표 관련 정보
   - 배당 정책 변경

2. 회계/감사 관련 정보 (최우선 순위)
   - 회계처리 방식 변경
   - 감사의견 관련 내용
   - 내부회계관리제도
   - 회계 감리 결과
   
3. 구조적 기업가치 변동 정보 (높은 우선순위)
    - 신규사업/투자/계약에 대한 내용
    - 대외 전략(정부 정책, 글로벌 파트너, 지정학 리스크 등)
    - 기업의 새로운 사업전략 및 방향성, 신사업 등
    - 기업의 전략 방향성에 영향을 미칠 수 있는 정보
    - 기존 수입모델/사업구조/고객구조 변화
    - 공급망/수요망 등 valuechain 관련 내용 (예: 대형 생산지 이전, 주력 사업군 정리 등) 

4. 기업구조 변경 정보 (높은 우선순위)
   - 인수합병(M&A)
   - 자회사 설립/매각
   - 지분 변동
   - 조직 개편

**언론사 신뢰도 판단 기준**
다음 언론사들의 기사를 우선적으로 선별하세요:
- 대형 언론사: 조선일보, 중앙일보, 동아일보, 한국경제, 매일경제, 연합뉴스
- 전문 경제지: 이데일리, 아시아경제, 뉴스핌, 뉴시스, 헤럴드경제, 더벨
- 전문 매체: 비즈니스포스트, 머니투데이, 한국경제TV

**중복 제거 기준**
다음 기준으로 중복 기사를 제거하세요:

1. **동일 이슈 중복 보도**
   - 같은 사건/이슈에 대한 여러 언론사 보도 중 가장 상세하고 신뢰할 수 있는 기사만 선택
   - 우선순위: 조선일보 > 중앙일보 > 동아일보 > 한국경제 > 매일경제 > 연합뉴스 등 대형·원문 보도 매체

2. **기사 품질 기준**
   - 더 자세한 정보를 포함한 기사 우선
   - 주요 인용문이나 전문가 의견이 포함된 기사 우선
   - 단순 보도보다 분석적 내용이 포함된 기사 우선

3. **시간 순서**
   - 최초 보도나 가장 최신 정보를 담은 기사 우선

4. **제목 유사성 판단**
   - 제목이 거의 동일하거나 핵심 내용이 같은 경우 중복으로 간주
   - 예: "삼성전자 실적 발표" vs "삼성전자, 2024년 실적 공개" → 중복
   - 예: "삼성전자 실적 발표" vs "삼성전자 신규 사업 진출" → 중복 아님

[응답 형식]
선별된 뉴스를 다음과 같이 나열해주세요:

1. [뉴스 제목]
  
   선별 이유: [간단한 선별 이유]
   링크: [뉴스 URL]

2. [뉴스 제목]
  
   선별 이유: [간단한 선별 이유]
   링크: [뉴스 URL]

...

**중요**: 
- **무조건 1개 이상의 뉴스를 반드시 선별해야 합니다.** 1개 미만으로 선별하면 안됩니다.
- 가능하면 7-10개까지 선별하되, 최소 1개는 반드시 선별하세요.
- 선별된 뉴스에 중복이 없어야 합니다.
- 내용도 반드시 중복되면 안됩니다.
- 언론사명은 정확하게 표기해주세요.
- 선별 이유는 간단명료하게 작성해주세요.
"""

        # 분석할 뉴스 목록 추가
        news_list_text = "\n".join([f"{i+1}. {news.get('title', '')} - {news.get('url', '')}" for i, news in enumerate(news_list)])
        analysis_prompt += f"\n\n분석할 뉴스 목록:\n{news_list_text}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 회계법인 관점에서 뉴스를 분석하는 전문가입니다."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        
        # AI 응답을 파싱하여 구조화된 데이터로 변환
        try:
            parsed_result = parse_ai_response(ai_response, news_list)
            
            # AI가 선별한 결과 그대로 사용 (화이트리스트 필터링 제거)
            if parsed_result.get("selected_news"):
                st.info(f"[AI 선별 결과] {category_name}: {len(parsed_result['selected_news'])}개 기사 선별")
            
            return parsed_result
        except Exception as parse_error:
            st.warning(f"AI 응답 파싱 중 오류: {str(parse_error)}")
            # 파싱 실패 시 기본 구조 반환
            return {
                "selected_news": [],
                "total_analyzed": len(news_list),
                "selected_count": 0,
                "error": f"응답 파싱 실패: {str(parse_error)}",
                "raw_response": ai_response  # 원본 응답도 포함
            }
            
    except Exception as e:
        st.error(f"AI 분석 중 오류: {str(e)}")
        return {
            "selected_news": [],
            "total_analyzed": len(news_list),
            "selected_count": 0,
            "error": f"AI 분석 실패: {str(e)}"
        }

def parse_ai_response(ai_response, news_list):
    """AI 응답을 파싱하여 구조화된 데이터로 변환 - 개선된 버전"""
    selected_news = []
    
    # AI 응답을 줄 단위로 분리
    lines = ai_response.strip().split('\n')
    
    current_news = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 새로운 뉴스 항목 시작 (숫자로 시작하는 줄)
        if re.match(r'^\d+\.', line):
            # 이전 뉴스가 있으면 저장
            if current_news and 'title' in current_news:
                selected_news.append(current_news)
            
            # 새 뉴스 시작
            current_news = {}
            # 제목 추출 (숫자와 점 제거)
            title = re.sub(r'^\d+\.\s*', '', line)
            current_news['title'] = title.strip()
            
        # 언론사 정보 (다양한 패턴 지원)
        elif any(line.startswith(prefix) for prefix in ['언론사:', '언론사명:', '언론사']):
            press = re.sub(r'^언론사[명]?:\s*', '', line).strip()
            current_news['press_analysis'] = press
            
        # 선별 이유
        elif any(line.startswith(prefix) for prefix in ['선별 이유:', '선별이유:', '이유:', '분석:']):
            reason = re.sub(r'^선별\s*이유[:\s]*', '', line).strip()
            current_news['selection_reason'] = reason
            
        # 링크
        elif any(line.startswith(prefix) for prefix in ['링크:', 'URL:', '주소:']):
            url = re.sub(r'^링크[:\s]*|URL[:\s]*|주소[:\s]*', '', line).strip()
            current_news['url'] = url
            
        # 날짜 (원본 뉴스에서 찾기)
        elif 'title' in current_news:
            # 원본 뉴스 목록에서 제목으로 매칭하여 날짜 찾기
            for news in news_list:
                if news['title'] in current_news['title'] or current_news['title'] in news['title']:
                    current_news['date'] = news['date']
                    if 'url' not in current_news:
                        current_news['url'] = news['url']
                    # 원본 뉴스의 키워드 정보 저장
                    current_news['keyword'] = news.get('keyword', '')
                    # 언론사 정보 우선순위: 우리 매핑 > AI 추출
                    original_press = news.get('press', '')
                    if original_press and original_press != '언론사 정보 없음':
                        # 우리가 매핑한 언론사명이 있으면 우선 사용
                        current_news['press_analysis'] = original_press
                    elif 'press_analysis' not in current_news:
                        # AI가 추출한 언론사명이 없으면 기본값
                        current_news['press_analysis'] = '언론사 정보 없음'
                    break
    
    # 마지막 뉴스 추가
    if current_news and 'title' in current_news:
        selected_news.append(current_news)
    
    # 필수 필드가 없는 경우 기본값 설정 및 원본 뉴스와 매칭
    for news in selected_news:
        if 'importance' not in news:
            news['importance'] = '보통'
        
        # 언론사 정보가 없는 경우 기본값 설정
        if 'press_analysis' not in news or not news['press_analysis']:
            news['press_analysis'] = '언론사 정보 없음'
        
        if 'selection_reason' not in news:
            news['selection_reason'] = 'AI가 선별한 뉴스'
        
        if 'date' not in news:
            news['date'] = '날짜 정보 없음'
        
        if 'keyword' not in news:
            news['keyword'] = '키워드 정보 없음'
    
    return {
        "selected_news": selected_news,
        "total_analyzed": len(news_list),
        "selected_count": len(selected_news)
    }

def main():
    # 메인 타이틀
    st.markdown("<h1 class='main-title'>PwC 뉴스 분석기</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #666;'>회계법인 관점에서 중요한 뉴스를 자동으로 분석하는 AI 도구</p>", unsafe_allow_html=True)
    
    # 사이드바 설정
    st.sidebar.title("🔍 설정")
    
    # 날짜 및 시간 필터
    st.sidebar.markdown("### 📅 날짜 및 시간 범위")
    now = datetime.now(KST)
    default_start = now - timedelta(days=1)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("시작일", value=default_start.date())
    with col2:
        end_date = st.date_input("종료일", value=now.date())
    
    # 시간 선택 추가
    st.sidebar.markdown("#### ⏰ 시간 범위")
    col3, col4 = st.sidebar.columns(2)
    with col3:
        start_time = st.time_input("시작 시간", value=time(0, 0), help="기본값: 오전 12시 (자정)")
    with col4:
        end_time = st.time_input("종료 시간", value=time(23, 59), help="기본값: 오후 11시 59분")
    
    # 카테고리 선택
    st.sidebar.markdown("### 🏷️ 분석할 카테고리")
    selected_categories = st.sidebar.multiselect(
        "카테고리를 선택하세요",
        options=list(KEYWORD_CATEGORIES.keys()),
        default=list(KEYWORD_CATEGORIES.keys()),
        help="분석할 카테고리를 선택하세요"
    )
    
    # 선택된 카테고리의 검색 키워드 표시
    if selected_categories:
        st.sidebar.markdown("### 🔍 검색 키워드")
        keywords_expander = st.sidebar.expander("키워드 상세보기", expanded=False)
        with keywords_expander:
            for category in selected_categories:
                keywords = KEYWORD_CATEGORIES[category]
                st.markdown(f"**{category}**:")
                keyword_text = ", ".join(keywords)
                st.info(keyword_text)
                st.markdown("---")
    
    # Sector별 Prompt 표시
    st.sidebar.markdown("### 📝 Sector별 Prompt")
    prompt_expander = st.sidebar.expander("프롬프트 보기", expanded=False)
    with prompt_expander:
        st.markdown("**삼일PwC 카테고리 프롬프트:**")
        st.markdown("""
        **포함 조건:**
        - 삼일회계법인/삼일PwC/PwC 자체가 기사의 주제인 경우
        - 삼일이 해당 사건에서 주된 역할을 맡은 경우
        - 삼일PwC가 주요 근거나 핵심 소스로 활용된 경우
        - 컨소시엄 참여 관련 (역할 명시, 단순 명단 포함)
        
        **제외 조건:**
        - 단순 언급 수준 (인물 경력 소개, 한 문장 배경 소개)
        - 기사 주제와 직접 관련성이 없는 경우
        - 중복 보도, 광고성 콘텐츠, 외국어 기사
        """)
        
        st.markdown("**일반 카테고리 프롬프트:**")
        st.markdown("""
        **최우선 순위:**
        - 재무/실적 정보 (매출, 영업이익, 순이익, 배당 정책)
        - 회계/감사 관련 (회계처리 변경, 감사의견, 내부회계관리제도)
        
        **높은 우선순위:**
        - 구조적 기업가치 변동 (신규사업, 투자, 전략 방향성)
        - 기업구조 변경 (M&A, 자회사 설립/매각, 지분 변동)
        
        **제외 조건:**
        - 경기 관련 내용 (스포츠단, 야구단, 축구단 등)
        - 신제품 홍보, 사회공헌, ESG, 기부 등
        - 단순 시스템 장애, 버그, 서비스 오류
        - 기술 성능, 품질, 테스트 관련 보도
        - 목표가 관련 보도
        """)
    
    # 선택 요약 표시
    if selected_categories:
        st.sidebar.markdown("### 📋 선택 요약")
        st.sidebar.info(f"**날짜**: {start_date} ~ {end_date}")
        st.sidebar.info(f"**시간**: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}")
        st.sidebar.info(f"**카테고리**: {len(selected_categories)}개 선택")
        
        # 선택된 카테고리의 총 키워드 수 계산
        total_keywords = sum(len(KEYWORD_CATEGORIES[cat]) for cat in selected_categories)
        st.sidebar.info(f"**총 키워드 수**: {total_keywords}개")
        
    
    # 메인 컨텐츠
    if st.button("🚀 뉴스 분석 시작", type="primary", use_container_width=True):
        if not selected_categories:
            st.error("분석할 카테고리를 선택해주세요.")
            return
        
        # 날짜 객체 생성 (사용자가 설정한 시간 범위 사용)
        start_dt = datetime.combine(start_date, start_time).replace(tzinfo=KST)
        end_dt = datetime.combine(end_date, end_time).replace(tzinfo=KST)
        
        # 진행 상황 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = {}
        
        # 카테고리별 분석
        for i, category in enumerate(selected_categories):
            status_text.text(f"📊 {category} 카테고리 분석 중...")
            progress_bar.progress((i + 1) / len(selected_categories))
            
            # 해당 카테고리의 키워드들
            category_keywords = KEYWORD_CATEGORIES[category]
            
            # 뉴스 수집
            with st.spinner(f"{category} 뉴스 수집 중..."):
                news_list = collect_news_from_naver_api(
                    category_keywords, 
                    start_dt, 
                    end_dt, 
                    category_name=category,
                    max_per_keyword=50
                )
            
            if not news_list:
                st.warning(f"{category} 카테고리에서 수집된 뉴스가 없습니다.")
                continue
            
            # AI 분석
            with st.spinner(f"{category} AI 분석 중..."):
                analysis_result = analyze_news_with_ai(news_list, category)
            
            all_results[category] = {
                'collected_news': news_list, # 원본 뉴스 목록
                'analysis_result': analysis_result
            }
        
        # 분석 완료
        st.success("✅ 모든 카테고리 분석 완료!")
        
        # 결과 표시
        display_results(all_results, selected_categories)
    
    else:
        # 초기 화면
        st.markdown("""
        <div style='text-align: center; margin: 50px 0;'>
            <h3>👋 PwC 뉴스 분석기에 오신 것을 환영합니다!</h3>
            <p>왼쪽 사이드바에서 분석할 카테고리와 날짜를 선택한 후 "뉴스 분석 시작" 버튼을 클릭하세요.</p>
        </div>
        """, unsafe_allow_html=True)

def display_results(all_results, selected_categories):
    """분석 결과 표시"""
    st.markdown("## 📊 분석 결과")
    
    # 전체 결과를 저장할 리스트 (엑셀 다운로드용)
    all_excel_data = []
    
    for category in selected_categories:
        if category not in all_results:
            continue
            
        result = all_results[category]
        collected_count = len(result['collected_news'])
        analysis = result['analysis_result']
        
        # 카테고리별 결과 카드
        with st.expander(f"🏷️ {category} ", expanded=True):
            if 'error' in analysis:
                st.error(f"분석 오류: {analysis['error']}")
                continue
            
            selected_news = analysis.get('selected_news', [])
            selected_count = analysis.get('selected_count', 0)
            
            st.info(f"📈 AI 분석 결과: {selected_count}건 선별")
            
            if selected_news:
                # 테이블 형태로 표시
                table_data = []
                for news in selected_news:
                    # UI용 테이블 데이터 (키워드, 언론사 제외)
                    table_data.append({
                        "뉴스제목": news.get('title', '제목 없음'),
                        "링크": f"[링크]({news.get('url', '')})" if news.get('url') else '링크 없음'
                    })
                
                # Streamlit 테이블로 표시
                st.table(table_data)
            else:
                st.info("AI 분석 결과 해당 카테고리에서 선별할 만한 뉴스가 없습니다.")
            
            # 엑셀용: 모든 수집된 뉴스 포함 (선별되지 않은 뉴스도 포함)
            all_collected_news = result['collected_news']
            for news in all_collected_news:
                # 선별된 뉴스인지 확인
                is_selected = any(selected.get('title', '') in news.get('title', '') or news.get('title', '') in selected.get('title', '') for selected in selected_news)
                
                # 선별 이유 또는 제외 이유 결정
                if is_selected:
                    selection_reason = next((selected.get('selection_reason', '') for selected in selected_news if selected.get('title', '') in news.get('title', '') or news.get('title', '') in selected.get('title', '')), '')
                else:
                    # 제외된 뉴스의 경우 제외 이유 추정
                    title = news.get('title', '').lower()
                    summary = news.get('summary', '').lower()
                    
                    # 제외 이유 판단 로직
                    if any(keyword in title or keyword in summary for keyword in ['야구단', '축구단', 'kbo', '선수', '감독', '구단']):
                        selection_reason = '스포츠단 관련 기사'
                    elif any(keyword in title or keyword in summary for keyword in ['출시', '기부', '환경', '캠페인', '사회공헌', '나눔', 'esg']):
                        selection_reason = '신제품 홍보/사회공헌/ESG/기부 기사'
                    elif any(keyword in title or keyword in summary for keyword in ['장애', '오류', '버그', '점검', '중단', '실패']):
                        selection_reason = '단순 시스템 장애/버그/서비스 오류'
                    elif any(keyword in title or keyword in summary for keyword in ['우수성', '기술력', '성능', '품질', '테스트']):
                        selection_reason = '기술 성능/품질/테스트 홍보 기사'
                    elif any(keyword in title or keyword in summary for keyword in ['목표가', '목표주가']):
                        selection_reason = '목표주가 기사'
                    elif any(keyword in title or keyword in summary for keyword in ['출신', '경력', '배경']):
                        selection_reason = '단순 언급/경력 소개/배경 문장'
                    else:
                        selection_reason = '관련성 부족 또는 기타 제외 사유'
                
                excel_data = {
                    "카테고리": category,
                    "검색키워드": news.get('keyword', '키워드 없음'),
                    "뉴스제목": news.get('title', '제목 없음'),
                    "언론사": news.get('press', '언론사 정보 없음'),
                    "링크": news.get('url', ''),
                    "발행일": news.get('date', '날짜 없음'),
                    "요약": news.get('summary', '요약 없음'),
                    "선별여부": "선별됨" if is_selected else "제외됨",
                    "선별/제외이유": selection_reason
                }
                all_excel_data.append(excel_data)
    
    # 엑셀 다운로드 버튼 (결과가 있을 때만 표시)
    if all_excel_data:
        st.markdown("---")
        st.markdown("### 📥 엑셀 다운로드")
        
        # pandas DataFrame 생성
        import pandas as pd
        df = pd.DataFrame(all_excel_data)
        
        # 엑셀 파일 생성
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='뉴스분석결과', index=False)
        
        # 파일명 생성 (현재 날짜 포함)
        from datetime import datetime
        filename = f"PwC_뉴스분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 다운로드 버튼
        st.download_button(
            label="📊 엑셀 파일 다운로드",
            data=output.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="선별이유와 검색키워드가 포함된 상세 분석 결과를 엑셀 파일로 다운로드합니다."
        )

if __name__ == "__main__":
    main()

