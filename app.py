import streamlit as st
import requests
from datetime import datetime, timedelta, timezone
import json
import openai
import os
import re
from config import KEYWORD_CATEGORIES, AI_ANALYSIS_PROMPT, NAVER_API_SETTINGS

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

def collect_news_from_naver_api(category_keywords, start_date, end_date, max_per_keyword=50):
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
                    news_item = {
                        'title': clean_html_entities(item.get('title', '')),
                        'url': item.get('link', ''),
                        'date': pub_date.strftime('%Y-%m-%d'),
                        'summary': clean_html_entities(item.get('description', '')),
                        'keyword': keyword,
                        'raw_press': extract_press_from_title(item.get('title', ''))
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
    """뉴스 제목에서 언론사명 추출 (AI가 판별할 수 있도록 원본 정보 제공)"""
    # 기본적인 언론사명 패턴 제거
    press_patterns = [
        r'\s*-\s*[가-힣A-Za-z0-9\s]+$',  # "제목 - 언론사명" 패턴
        r'\s*\[[가-힣A-Za-z0-9\s]+\]\s*$',  # "제목 [언론사명]" 패턴
    ]
    
    clean_title = title
    extracted_press = ""
    
    for pattern in press_patterns:
        match = re.search(pattern, title)
        if match:
            extracted_press = match.group().strip(' -[]')
            clean_title = re.sub(pattern, '', title).strip()
            break
    
    return {
        'clean_title': clean_title,
        'extracted_press': extracted_press,
        'original_title': title
    }

def analyze_news_with_ai(news_list, category_name):
    """AI를 사용하여 뉴스 분석 및 언론사 판별"""
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # AI 분석 프롬프트 (config에서 가져온 프롬프트 사용)
        analysis_prompt = AI_ANALYSIS_PROMPT + f"\n\n분석할 뉴스 목록:\n{json.dumps([{'title': news['title'], 'url': news['url'], 'date': news['date'], 'raw_press_info': news['raw_press']} for news in news_list], ensure_ascii=False)}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 회계법인 관점에서 뉴스를 분석하는 전문가입니다."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        
        try:
            result = json.loads(ai_response)
            return result
        except json.JSONDecodeError:
            return {
                "selected_news": [],
                "total_analyzed": len(news_list),
                "selected_count": 0,
                "error": "AI 응답 파싱 실패"
            }
            
    except Exception as e:
        st.error(f"AI 분석 중 오류: {str(e)}")
        return {
            "selected_news": [],
            "total_analyzed": len(news_list),
            "selected_count": 0,
            "error": f"AI 분석 실패: {str(e)}"
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
        default=["삼일PwC"],
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
                    max_per_keyword=50
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
            <p><strong>주의:</strong> UI에서는 카테고리만 표시되며, 키워드는 AI 분석 시에만 사용됩니다.</p>
            <p><strong>API 설정:</strong> 환경변수에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요.</p>
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
        with st.expander(f"🏷️ {category} (수집: {collected_count}건)", expanded=True):
            if 'error' in analysis:
                st.error(f"분석 오류: {analysis['error']}")
                continue
            
            selected_news = analysis.get('selected_news', [])
            selected_count = analysis.get('selected_count', 0)
            
            st.info(f"📈 AI 분석 결과: {collected_count}건 중 {selected_count}건 선별")
            
            if selected_news:
                for news in selected_news:
                    with st.container():
                        st.markdown(f"""
                        <div class="news-item">
                            <div class="news-title">{news['title']}</div>
                            <div class="news-meta">
                                📅 {news['date']} | 
                                ⭐ 중요도: {news['importance']} | 
                                📰 {news['press_analysis']}
                            </div>
                            <div class="news-url">
                                🔗 <a href="{news['url']}" target="_blank">{news['url']}</a>
                            </div>
                            <div class="news-meta">
                                💡 선별 이유: {news['selection_reason']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("AI 분석 결과 해당 카테고리에서 선별할 만한 뉴스가 없습니다.")
    
    # 전체 요약
    st.markdown("## 📋 전체 요약")
    total_collected = sum(len(result['collected_news']) for result in all_results.values())
    total_selected = sum(
        len(result['analysis_result'].get('selected_news', [])) 
        for result in all_results.values() 
        if 'error' not in result['analysis_result']
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("분석 카테고리", len(selected_categories))
    with col2:
        st.metric("수집된 뉴스", total_collected)
    with col3:
        st.metric("AI 선별 뉴스", total_selected)

if __name__ == "__main__":
    main()
