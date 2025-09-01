import streamlit as st
import requests
from datetime import datetime, timedelta, timezone
import json
import openai
import os
import re
from config import KEYWORD_CATEGORIES, NAVER_API_SETTINGS

# 페이지 설정
st.set_page_config(
    page_title="PwC 뉴스 분석기",
    page_icon="logo_orange.png",
    layout="wide"
)

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

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

def collect_news_from_naver_api(category_keywords, start_date, end_date, max_per_keyword=7):
    """네이버 뉴스 API에서 카테고리별 키워드로 뉴스 수집"""
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
    
    for keyword in category_keywords:
        try:
            # 네이버 뉴스 API 호출
            params = {
                "query": keyword,
                "display": min(max_per_keyword, 100),  # 최대 100개까지 요청 가능
                "start": 1,
                "sort": NAVER_API_SETTINGS["sort"]
            }
            
            response = requests.get(
                NAVER_API_SETTINGS["base_url"],
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                st.warning(f"'{keyword}' 검색 중 API 오류: {response.status_code}")
                continue
            
            # JSON 응답 파싱
            data = response.json()
            items = data.get('items', [])
            
            news_count = 0
            for item in items:
                if news_count >= max_per_keyword:
                    break
                
                # 날짜 파싱 (네이버 API는 ISO 8601 형식)
                try:
                    # 네이버 API 날짜 형식: "Wed, 15 Jan 2025 10:30:00 +0900"
                    date_str = item.get('pubDate', '')
                    if date_str:
                        # 간단한 날짜 파싱 (더 정확한 파싱이 필요할 수 있음)
                        pub_date = datetime.now()  # 기본값
                        # 실제 구현에서는 더 정교한 날짜 파싱 필요
                    else:
                        pub_date = datetime.now()
                except:
                    pub_date = datetime.now()
                
                # 날짜 범위 확인
                if start_date <= pub_date <= end_date:
                    # 언론사 정보 추출
                    press_info = extract_press_from_title(item.get('title', ''))
                    
                    news_item = {
                        'title': clean_html_entities(item.get('title', '')),
                        'url': item.get('link', ''),
                        'date': pub_date.strftime('%Y-%m-%d'),
                        'summary': clean_html_entities(item.get('description', '')),
                        'keyword': keyword,
                        'raw_press': press_info,
                        'extracted_press': press_info.get('extracted_press', '')
                    }
                    all_news.append(news_item)
                    news_count += 1
                    
        except Exception as e:
            st.warning(f"'{keyword}' 검색 중 오류: {str(e)}")
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

def extract_press_from_title(title):
    """뉴스 제목에서 언론사명 추출 - 개선된 버전"""
    if not title:
        return {
            'clean_title': '',
            'extracted_press': '',
            'original_title': ''
        }
    
    # 다양한 언론사 표기 패턴
    press_patterns = [
        # "제목 - 언론사명" 패턴 (가장 일반적)
        r'\s*[-–—]\s*([가-힣A-Za-z0-9\s&]+)$',
        # "제목 [언론사명]" 패턴
        r'\s*\[([가-힣A-Za-z0-9\s&]+)\]\s*$',
        # "제목 (언론사명)" 패턴
        r'\s*\(([가-힣A-Za-z0-9\s&]+)\)\s*$',
        # "제목 | 언론사명" 패턴
        r'\s*\|\s*([가-힣A-Za-z0-9\s&]+)$',
        # "제목 / 언론사명" 패턴
        r'\s*/\s*([가-힣A-Za-z0-9\s&]+)$',
        # "제목 : 언론사명" 패턴
        r'\s*:\s*([가-힣A-Za-z0-9\s&]+)$',
    ]
    
    clean_title = title
    extracted_press = ""
    
    for pattern in press_patterns:
        match = re.search(pattern, title)
        if match:
            # 그룹이 있는 경우 첫 번째 그룹 사용, 없는 경우 전체 매치 사용
            press_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
            extracted_press = press_text.strip()
            
            # 제목에서 언론사 부분 제거
            clean_title = re.sub(pattern, '', title).strip()
            
            # 추출된 언론사가 너무 길거나 의미없는 경우 필터링
            if len(extracted_press) > 20 or extracted_press.lower() in ['뉴스', '기사', '보도']:
                extracted_press = ""
                clean_title = title  # 원본 제목 유지
            else:
                break
    
    # 언론사가 추출되지 않은 경우 추가 시도
    if not extracted_press:
        # 제목 끝에 있는 일반적인 언론사명 패턴 확인
        common_press = [
            '연합뉴스', '뉴시스', '매일경제', '한국경제', '서울경제', '이데일리',
            '머니투데이', '아시아경제', '파이낸셜뉴스', '헤럴드경제', '경향신문',
            '조선일보', '중앙일보', '동아일보', '한겨레', '한국일보', '국민일보',
            '세계일보', '문화일보', '서울신문', '경기일보', '부산일보', '대구일보'
        ]
        
        for press in common_press:
            if press in title:
                extracted_press = press
                clean_title = title.replace(press, '').strip()
                break
    
    return {
        'clean_title': clean_title,
        'extracted_press': extracted_press,
        'original_title': title
    }

def analyze_news_with_ai(news_list, category_name):
    """AI를 사용하여 뉴스 분석 및 언론사 판별 - 카테고리별 프롬프트 적용"""
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # 카테고리별 프롬프트 설정
        if category_name == "삼일PwC":
            # 삼일PwC 전용 상세 프롬프트
            analysis_prompt = f"""
다음은 '{category_name}' 카테고리로 수집된 뉴스 목록입니다.

**1차 자동화 범위: 회계법인 중심 키워드로 축소**
- 회계법인명: 삼일회계, 삼일PwC, PwC삼일, PwC코리아, 삼정KPMG, 삼정회계, KPMG삼정, 딜로이트안진, 안진회계, 딜로이트코리아, 한영회계, EY한영, EY코리아
- 업계 통칭: Big4, 회계법인, 회계업계, 감사업계

**포함되어야 하는 기사 (Y)**
1. 삼일회계법인/삼일PwC/PwC 자체가 기사의 주제인 경우
   - 자체 활동: 리포트 발간, 자문·감정·매각주관 수행, 인사발령
   - 분쟁 당사자: 삼일 관련 소송, 압수수색, 각종 분쟁 사건
   - 기업 활동: 삼일PwC 자체 보도자료, 행사, 세미나 개최
   - 조직 변화: 조직 개편, 신규 사업 런칭, 파트너십 체결

2. 삼일이 해당 사건에서 주된 역할을 맡은 경우
   - 핵심 역할 담당: 매각주관, 감정, 자문, 보고서 작성, 대표 발표
   - 기사 핵심이 그 역할의 결과나 논쟁: 삼일이 수행한 업무의 결과물이 기사 주제
   - 결론·쟁점에 영향을 미치는 주체: 삼일이 사건 해결이나 판단에 직접적 영향

3. 삼일PwC가 주요 근거나 핵심 소스로 활용된 경우
   - 보고서·감정이 주요 근거: 삼일 보고서가 기사의 핵심 논거로 인용
   - 핵심 역할 맡은 결과: 주관·자문·감정 등을 맡아 그 결과가 기사 주제
   - 전문가 의견 제공: 삼일 관계자의 인터뷰나 코멘트가 기사 핵심 내용

4. 컨소시엄 참여 관련
   - 역할 명시: 컨소시엄 내에서 구체적 역할(과제 책임, 재무 파트 담당 등) 명시된 경우
   - 단순 명단 포함: 여러 기관 중 한 멤버로 이름만 열거된 경우도 포함
   - 리스트 나열: "A, B, C와 함께 PwC도 참여했다" 형태의 언급도 포함

5. 기타 포함 사례
   - 통계·근거 인용: 기사 본문에서 "~에 따르면(삼일회계법인)"으로 통계나 근거 인용
   - 삼일PwC 자체 보도자료·세미나 안내 (단, [보도자료] 라벨 표기)
   - 사설·칼럼·오피니언: 삼일PwC 관련 내용 다루는 경우 포함

**제외되어야 하는 기사 (N)**
1. 단순 언급 수준
   - 인물 경력 소개: "삼일회계법인 출신", 과거 경력 언급 정도
   - 한 문장 배경 소개: 한두 문장으로 배경 설명 차원에서만 언급
   - 통계 출처 표기: 단순히 자료 출처로만 언급 (기사 주제와 무관)
   - 리스트 단순 나열: 여러 기관을 나열하는 과정에서 형식적 언급

2. 기사 주제와 직접 관련성이 없는 경우
   - 주요 주제 무관: 삼일회계법인/삼일PwC/PwC가 기사 핵심 주제가 아닌 경우
   - 사례 인용: PwC가 단순 사례나 참고자료로만 인용된 경우
   - 배경 설명: 한 줄 통계·근거가 문맥상 기사 핵심 근거가 아니고 배경설명 수준인 경우

3. 기타 제외 사항
   - 중복 보도: 동일 이슈의 언론 보도 중 하나만 남기고 제거
   - 광고성 콘텐츠: 스폰서 콘텐츠, 기사형 보도자료 (단, 삼일 자체 보도자료는 포함)
   - 외국어 기사: 한국어/영어를 제외한 해외 기사
   - 단순 언급만: 주요 주제에 직접 관련되지 않고 언급만 된 기사

**중복 제거 기준**
우선순위 (상위가 우선)
1. 매체 우선순위: 조선일보 > 중앙일보 > 동아일보 > 한국경제 > 매일경제 > 연합뉴스 등 대형·원문 보도 매체
2. 기사 품질: 속보성, 제목 및 내용 명확성
3. 시간 순서: 최초 보도 날짜

**경계 사례 판단 기준**
- 명확한 포함 (Y): 컨소시엄 명단, 컨소시엄 역할, 통계·근거 인용 등
- 명확한 제외 (N): 경력 언급, 단순 배경 설명 등
- 애매한 경우: 포함 쪽으로 판단 후 추후 재검토

[응답 형식]
선별된 뉴스를 다음과 같이 나열해주세요:

1. [뉴스 제목]
   언론사: [언론사명]
   선별 이유: [간단한 선별 이유]
   링크: [뉴스 URL]

2. [뉴스 제목]
   언론사: [언론사명]
   선별 이유: [간단한 선별 이유]
   링크: [뉴스 URL]

...

**중요**: 
- 최소 3개 뉴스는 반드시 선별하고, 너무 엄격하게 선별하지 말고 비즈니스 관점에서 유용할 수 있는 정보라면 포함하세요.
- 언론사명은 정확하게 표기해주세요.
- 선별 이유는 간단명료하게 작성해주세요.
- 삼일PwC 관련성이 명확한 뉴스를 우선적으로 선별하세요.
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

[응답 형식]
선별된 뉴스를 다음과 같이 나열해주세요:

1. [뉴스 제목]
   언론사: [언론사명]
   선별 이유: [간단한 선별 이유]
   링크: [뉴스 URL]

2. [뉴스 제목]
   언론사: [언론사명]
   선별 이유: [간단한 선별 이유]
   링크: [뉴스 URL]

...

**중요**: 
- 최소 5개 뉴스는 반드시 선별하고, 너무 엄격하게 선별하지 말고 비즈니스 관점에서 유용할 수 있는 정보라면 포함하세요.
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
                    # 원본 뉴스의 언론사 정보도 활용
                    if 'press_analysis' not in current_news and news.get('raw_press', {}).get('extracted_press'):
                        current_news['press_analysis'] = news['raw_press']['extracted_press']
                    break
    
    # 마지막 뉴스 추가
    if current_news and 'title' in current_news:
        selected_news.append(current_news)
    
    # 필수 필드가 없는 경우 기본값 설정 및 원본 뉴스와 매칭
    for news in selected_news:
        if 'importance' not in news:
            news['importance'] = '보통'
        
        # 언론사 정보가 없는 경우 원본 뉴스에서 찾기
        if 'press_analysis' not in news or not news['press_analysis']:
            for original_news in news_list:
                if (news['title'] in original_news['title'] or 
                    original_news['title'] in news['title']):
                    extracted_press = original_news.get('raw_press', {}).get('extracted_press', '')
                    if extracted_press:
                        news['press_analysis'] = extracted_press
                    else:
                        news['press_analysis'] = '언론사 정보 없음'
                    break
            else:
                news['press_analysis'] = '언론사 정보 없음'
        
        if 'selection_reason' not in news:
            news['selection_reason'] = 'AI가 선별한 뉴스'
        
        if 'date' not in news:
            news['date'] = '날짜 정보 없음'
    
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
    
    # 날짜 필터
    st.sidebar.markdown("### 📅 날짜 범위")
    now = datetime.now()
    default_start = now - timedelta(days=1)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("시작일", value=default_start.date())
    with col2:
        end_date = st.date_input("종료일", value=now.date())
    
    # 카테고리 선택
    st.sidebar.markdown("### 🏷️ 분석할 카테고리")
    selected_categories = st.sidebar.multiselect(
        "카테고리를 선택하세요",
        options=list(KEYWORD_CATEGORIES.keys()),
        default=list(KEYWORD_CATEGORIES.keys()),
        help="분석할 카테고리를 선택하세요"
    )
    
    # 선택 요약 표시
    if selected_categories:
        st.sidebar.markdown("### 📋 선택 요약")
        st.sidebar.info(f"**날짜**: {start_date} ~ {end_date}")
        st.sidebar.info(f"**카테고리**: {len(selected_categories)}개 선택")
        
        # 선택된 카테고리의 총 키워드 수 계산
        total_keywords = sum(len(KEYWORD_CATEGORIES[cat]) for cat in selected_categories)
        
    
    # 메인 컨텐츠
    if st.button("🚀 뉴스 분석 시작", type="primary", use_container_width=True):
        if not selected_categories:
            st.error("분석할 카테고리를 선택해주세요.")
            return
        
        # 날짜 객체 생성
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
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
                    max_per_keyword=7
                )
            
            if not news_list:
                st.warning(f"{category} 카테고리에서 수집된 뉴스가 없습니다.")
                continue
            
            # AI 분석
            with st.spinner(f"{category} AI 분석 중..."):
                analysis_result = analyze_news_with_ai(news_list, category)
            
            all_results[category] = {
                'collected_news': news_list,
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
                    # 원본 뉴스에서 언론사 정보 확인
                    original_press = ""
                    for original_news in result['collected_news']:
                        if (news.get('title', '') in original_news.get('title', '') or 
                            original_news.get('title', '') in news.get('title', '')):
                            original_press = original_news.get('extracted_press', '')
                            break
                    
                    # AI 분석 결과와 원본 언론사 정보 비교
                    ai_press = news.get('press_analysis', '언론사 정보 없음')
                    final_press = ai_press if ai_press and ai_press != '언론사 정보 없음' else original_press
                    
                    table_data.append({
                        "카테고리": category,
                        "뉴스제목": news.get('title', '제목 없음'),
                        "언론사": final_press or '언론사 정보 없음',
                        "링크": f"[링크]({news.get('url', '')})" if news.get('url') else '링크 없음'
                    })
                
                # Streamlit 테이블로 표시
                st.table(table_data)
            else:
                st.info("AI 분석 결과 해당 카테고리에서 선별할 만한 뉴스가 없습니다.")
    
    # 전체 요약 섹션 제거

if __name__ == "__main__":
    main()
