import streamlit as st
import re
from typing import Dict, List
import feedparser
import requests
from bs4 import BeautifulSoup
import json
import openai


# ✅ 무조건 첫 Streamlit 명령어
st.set_page_config(
    page_title="PwC 뉴스 분석기",
    page_icon="logo_orange.png",
    layout="wide",
)



from datetime import datetime, timedelta, timezone
import os
from PIL import Image

import io
from urllib.parse import urlparse

import pandas as pd  # 엑셀 생성을 위해 pandas 추가
import html  # HTML 엔티티 디코딩을 위해 추가

# Import centralized configuration
from config import (
    COMPANY_CATEGORIES,
    TRUSTED_PRESS_ALIASES,
    ADDITIONAL_PRESS_ALIASES,
    SYSTEM_PROMPT_1,
    SYSTEM_PROMPT_2,
    SYSTEM_PROMPT_3,
    EXCLUSION_CRITERIA,
    DUPLICATE_HANDLING,
    SELECTION_CRITERIA, 
    GPT_MODELS,
    DEFAULT_GPT_MODEL,
    KEYWORD_CATEGORIES,
    DEFAULT_NEWS_COUNT
)

# 한국 시간대(KST) 정의
KST = timezone(timedelta(hours=9))

def clean_html_entities(text):
    """HTML 엔티티를 정리하고 &quot; 등의 문제를 해결하는 함수"""
    if not text:
        return ""
    
    # HTML 엔티티 디코딩
    cleaned_text = html.unescape(str(text))
    
    # 추가적인 정리 작업
    cleaned_text = cleaned_text.replace('&quot;', '"')
    cleaned_text = cleaned_text.replace('&amp;', '&')
    cleaned_text = cleaned_text.replace('&lt;', '<')
    cleaned_text = cleaned_text.replace('&gt;', '>')
    cleaned_text = cleaned_text.replace('&apos;', "'")
    
    # 연속된 공백 정리
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text





def format_date(date_str):
    """Format date to MM/DD format with proper timezone handling"""
    try:
        # Try YYYY-MM-DD format
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%m/%d')
    except Exception:
        try:
            # Try GMT format and convert to KST
            date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            # Convert UTC to KST (add 9 hours)
            date_obj_kst = date_obj + timedelta(hours=9)
            return date_obj_kst.strftime('%m/%d')
        except Exception:
            try:
                # Try GMT format without timezone indicator
                date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S GMT')
                # Convert UTC to KST (add 9 hours)
                date_obj_kst = date_obj + timedelta(hours=9)
                return date_obj_kst.strftime('%m/%d')
            except Exception:
                # Return original if parsing fails
                return date_str if date_str else '날짜 정보 없음'

# 회사별 추가 기준 함수들 제거됨 (개별 키워드 50개씩 수집 방식으로 단순화)
            
# 워드 파일 생성 함수들 제거됨 (현재 사용하지 않음)

# 커스텀 CSS
st.markdown("""
<style>
    .title-container {
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    .main-title {
        color: #d04a02;
        font-size: 2.5rem;
        font-weight: 700;
    }
    .news-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid #d04a02;
    }
    .news-title {
        font-weight: 600;
        font-size: 1.1rem;
    }
    .news-url {
        color: #666;
        font-size: 0.9rem;
    }
    .news-date {
        color: #666;
        font-size: 0.9rem;
        font-style: italic;
        margin-top: 5px;
    }
    .analysis-box {
        background-color: #f5f5ff;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        border-left: 4px solid #d04a02;
    }
    .subtitle {
        color: #dc582a;
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .download-box {
        background-color: #eaf7f0;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        border-left: 4px solid #00a36e;
        text-align: center;
    }
    .analysis-section {
        background-color: #f8f9fa;
        border-left: 4px solid #d04a02;
        padding: 20px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .selected-news {
        border-left: 4px solid #0077b6;
        padding: 15px;
        margin: 10px 0;
        background-color: #f0f8ff;
        border-radius: 5px;
    }
    .excluded-news {
        color: #666;
        padding: 5px 0;
        margin: 5px 0;
        font-size: 0.9em;
    }
    .news-meta {
        color: #666;
        font-size: 0.9em;
        margin: 3px 0;
    }
    .selection-reason {
        color: #666;
        margin: 5px 0;
        font-size: 0.95em;
    }
    .keywords {
        color: #666;
        font-size: 0.9em;
        margin: 5px 0;
    }
    .affiliates {
        color: #666;
        font-size: 0.9em;
        margin: 5px 0;
    }
    .news-url {
        color: #0077b6;
        font-size: 0.9em;
        margin: 5px 0;
        word-break: break-all;
    }
    .news-title-large {
        font-size: 1.2em;
        font-weight: 600;
        color: #000;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .news-url {
        color: #0077b6;
        font-size: 0.9em;
        margin: 5px 0 10px 0;
        word-break: break-all;
    }
    .news-summary {
        color: #444;
        font-size: 0.95em;
        margin: 10px 0;
        line-height: 1.4;
    }
    .selection-reason {
        color: #666;
        font-size: 0.95em;
        margin: 10px 0;
        line-height: 1.4;
    }
    .importance-high {
        color: #d04a02;
        font-weight: 700;
        margin: 5px 0;
    }
    .importance-medium {
        color: #0077b6;
        font-weight: 700;
        margin: 5px 0;
    }
    .group-indices {
        color: #666;
        font-size: 0.9em;
    }
    .group-selected {
        color: #00a36e;
        font-weight: 600;
    }
    .group-reason {
        color: #666;
        font-size: 0.9em;
        margin-top: 5px;
    }
    .not-selected-news {
        color: #666;
        padding: 5px 0;
        margin: 5px 0;
        font-size: 0.9em;
    }
    .importance-low {
        color: #666;
        font-weight: 700;
        margin: 5px 0;
    }
    .not-selected-reason {
        color: #666;
        margin: 5px 0;
        font-size: 0.95em;
    }
    .email-preview {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 20px;
        margin: 20px 0;
        overflow-y: auto;
        max-height: 500px;
    }
    .copy-button {
        background-color: #d04a02;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        margin: 10px 0;
    }
    .copy-button:hover {
        background-color: #b33d00;
    }
</style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown("---")
col1, col2 = st.columns([1, 4])
with col1:
    st.image("logo_orange.png", width=100, use_container_width=False)
with col2:
    st.markdown("<h1 class='main-title'>PwC 뉴스 분석기</h1>", unsafe_allow_html=True)
st.markdown("회계법인 관점에서 중요한 뉴스를 자동으로 분석하는 AI 도구")

# 브라우저 탭 제목 설정
st.markdown("<script>document.title = 'PwC 뉴스 분석기';</script>", unsafe_allow_html=True)

# 기본 선택 키워드 카테고리를 삼일PwC_핵심으로 설정
DEFAULT_KEYWORDS = COMPANY_CATEGORIES["Anchor"]

# 사이드바 설정
st.sidebar.title("🔍 PwC 뉴스 분석기")



# 날짜 필터 설정
st.sidebar.markdown("### 📅 날짜 필터")

# 현재 시간 가져오기
now = datetime.now()

# 기본 시작 날짜/시간 계산
default_start_date = now - timedelta(days=1)

# Set time to 8:00 AM for both start and end - 한국 시간 기준
start_datetime = datetime.combine(default_start_date.date(), 
                                    datetime.strptime("08:00", "%H:%M").time(), KST)
end_datetime = datetime.combine(now.date(), 
                                datetime.strptime("08:00", "%H:%M").time(), KST)

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "시작 날짜",
        value=default_start_date.date(),
        help="이 날짜부터 뉴스를 검색합니다. 월요일인 경우 지난 금요일, 그 외에는 전일로 자동 설정됩니다."
    )
    start_time = st.time_input(
        "시작 시간",
        value=start_datetime.time(),
        help="시작 날짜의 구체적인 시간을 설정합니다. 기본값은 오전 8시입니다."
    )
with col2:
    end_date = st.date_input(
        "종료 날짜",
        value=now.date(),
        help="이 날짜까지의 뉴스를 검색합니다."
    )
    end_time = st.time_input(
        "종료 시간",
        value=end_datetime.time(),
        help="종료 날짜의 구체적인 시간을 설정합니다. 기본값은 오전 8시입니다."
    )

# 구분선 추가
st.sidebar.markdown("---")

# 키워드 선택 UI
st.sidebar.markdown("### 🔍 분석할 키워드 선택")

# 테스트용 버튼 추가
if st.sidebar.button("🧪 테스트 모드: 삼일PwC만 검색", type="secondary"):
    st.sidebar.success("테스트 모드 활성화: 삼일PwC만 검색합니다.")

# 키워드 카테고리 복수 선택 (테스트용으로 삼일PwC_핵심만 기본 선택)
selected_categories = st.sidebar.multiselect(
    "키워드 카테고리를 선택하세요 (복수 선택 가능)",
    options=list(KEYWORD_CATEGORIES.keys()),
    default=["삼일PwC_핵심"],  # 테스트용으로 삼일PwC만 기본 선택
    help="분석할 키워드 카테고리를 하나 이상 선택하세요. 테스트용으로 삼일PwC_핵심이 기본 선택됩니다."
)

# 선택된 카테고리들의 모든 키워드 수집
SELECTED_KEYWORDS = []
for category in selected_categories:
    SELECTED_KEYWORDS.extend(KEYWORD_CATEGORIES[category])

# 선택된 키워드들
selected_keywords = SELECTED_KEYWORDS.copy()

# 선택요약 표시
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 선택요약")
st.sidebar.info(f"**날짜범위:** {start_date} ~ {end_date}")
st.sidebar.info(f"**선택된 카테고리:** {len(selected_categories)}개")

# 검색용 키워드 리스트 (간소화 - 직접 사용)
search_keywords = selected_keywords.copy()

# 구분선 추가
st.sidebar.markdown("---")

# 기본 모델 설정 (UI에서 선택 불가)
selected_model = DEFAULT_GPT_MODEL

# 검색 결과 수 - 키워드당 100개로 설정 (신뢰할 수 있는 언론사에서만)
max_results = 100

# config.py의 설정값들을 직접 사용
exclusion_criteria = EXCLUSION_CRITERIA
duplicate_handling = DUPLICATE_HANDLING
selection_criteria = SELECTION_CRITERIA

# 최종 프롬프트 생성
analysis_prompt = f"""
당신은 회계법인의 전문 애널리스트입니다. 아래 뉴스 목록을 분석하여 회계법인 관점에서 가장 중요한 뉴스를 선별하세요. 

[선택 기준]
{selection_criteria}

[제외 대상]
{exclusion_criteria}

[응답 요구사항]
1. 선택 기준에 부합하는 뉴스가 많다면 최대 3개까지 선택 가능합니다.
2. 선택 기준에 부합하는 뉴스가 없다면, 그 이유를 명확히 설명해주세요.

[응답 형식]
다음과 같은 JSON 형식으로 응답해주세요:

{{
    "selected_news": [
        {{
            "index": 1,
            "title": "뉴스 제목",
            "press": "언론사명",
            "date": "발행일자",
            "reason": "선정 사유",
            "keywords": ["키워드1", "키워드2"]
        }},
        ...
    ],
    "excluded_news": [
        {{
            "index": 2,
            "title": "뉴스 제목",
            "reason": "제외 사유"
        }},
        ...
    ]
}}

[유효 언론사]
{TRUSTED_PRESS_ALIASES}

[중복 처리 기준]
{duplicate_handling}
"""

# 메인 컨텐츠
if st.button("뉴스 분석 시작", type="primary"):
    # 유효 언론사 설정을 딕셔너리로 파싱
    valid_press_config = TRUSTED_PRESS_ALIASES
    
    # 이메일 미리보기를 위한 전체 내용 저장
    email_content = "[Client Intelligence]\n\n"
    
    # 모든 키워드 분석 결과를 저장할 딕셔너리
    all_results = {}
    
    # 분석 프롬프트 설정
    analysis_prompt = f"""
    당신은 회계법인의 전문 애널리스트입니다. 아래 뉴스 목록을 분석하여 회계법인 관점에서 가장 중요한 뉴스를 선별하세요. 
    
    [선택 기준]
    {selection_criteria}
    
    [제외 대상]
    {exclusion_criteria}
    
    [언론사 중요도 판단 기준]
    - 일반지: 조선일보, 중앙일보, 동아일보, 한국일보, 경향신문, 한겨레, 서울신문 (높은 신뢰도)
    - 경제지: 매일경제, 한국경제, 이데일리, 머니투데이, 파이낸셜뉴스, 아시아경제 (경제 뉴스 전문성)
    - 통신사: 뉴스1, 연합뉴스, 뉴시스 (신속성과 객관성)
    - 스포츠지: 스포츠조선, 스포츠동아, 스포츠한국, 스포츠경향 (스포츠 관련 뉴스는 제외 기준에 따라 AI가 판단)
    
    [응답 요구사항]
    1. 선택 기준에 부합하는 뉴스가 많다면 최대 3개까지 선택 가능합니다.
    2. 선택 기준에 부합하는 뉴스가 없다면, 그 이유를 명확히 설명해주세요.
    3. 언론사의 신뢰도와 전문성을 고려하여 선별하세요.
    
    [응답 형식]
    다음과 같은 JSON 형식으로 응답해주세요:
    
    {{
        "selected_news": [
            {{
                "index": 1,
                "title": "뉴스 제목",
                "press": "언론사명",
                "date": "발행일자",
                "reason": "선정 사유 (언론사 신뢰도 포함)",
                "keywords": ["키워드1", "키워드2"]
            }},
            ...
        ],
        "excluded_news": [
            {{
                "index": 2,
                "title": "뉴스 제목",
                "reason": "제외 사유 (언론사 품질 포함)"
            }},
            ...
        ]
    }}
    
    [중복 처리 기준]
    {duplicate_handling}
    """
    # st.info("📊 **회계법인 기준 적용됨**")  # UI에서 숨김
    
    # 키워드별 분석 실행
    for i, keyword in enumerate(selected_keywords, 1):
        with st.spinner(f"뉴스를 수집하고 분석 중입니다..."):
            # 날짜/시간 객체 생성
            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)
            
            # 직접 구현한 뉴스 분석 함수 호출
            try:
                analysis_result = analyze_news_direct(
                    keyword=keyword,
                    start_date=start_dt,
                    end_date=end_dt,
                    trusted_press=valid_press_config,
                    analysis_prompt=analysis_prompt
                )
                
                # 결과 저장
                all_results[keyword] = analysis_result
                
                # 결과 표시 (UI에서 숨김) - 키워드별 개별 표시 제거
                # st.success(f"'{keyword}' 분석 완료!")  # 키워드별 개별 표시 제거
                
            except Exception as e:
                st.error(f"'{keyword}' 분석 중 오류 발생: {str(e)}")
                continue
            
            # 분석 완료 후 결과 요약 (UI에서 숨김) - 중복 제거
            
            # 이메일 내용에 추가 (카테고리 기반으로 구성)
            # email_content += f"\n=== {keyword} 분석 결과 ===\n"  # 키워드별 개별 표시 제거
            # email_content += f"수집된 뉴스: {analysis_result['collected_count']}개\n"
            # email_content += f"날짜 필터링 후: {analysis_result['date_filtered_count']}개\n"
            # email_content += f"언론사 필터링 후: {analysis_result['press_filtered_count']}개\n"
            # email_content += f"최종 선별: {len(analysis_result['final_selection'])}개\n\n"
            
            # 디버깅 정보는 UI에서 숨김 (보류 뉴스, 유지 뉴스, 그룹핑 결과 등)
            
            st.markdown("---")
            
          
            # 5단계: 최종 선택 결과 표시
            st.markdown("<div class='subtitle'>🔍 최종 선택 결과</div>", unsafe_allow_html=True)
            
            # 재평가 여부 확인 (UI에서 숨김)
            # was_reevaluated = analysis_result.get("is_reevaluated", False)
            
            # if was_reevaluated:
            #     st.warning("5단계에서 선정된 뉴스가 없어 6단계 재평가를 진행했습니다.")
            #     st.markdown("<div class='subtitle'>🔍 6단계: 재평가 결과</div>", unsafe_allow_html=True)
            #     st.markdown("### 📰 재평가 후 선정된 뉴스")
            #     news_style = "border-left: 4px solid #FFA500; background-color: #FFF8DC;"
            #     reason_prefix = "<span style=\"color: #FFA500; font-weight: bold;\">재평가 후</span> 선별 이유: "
            # else:
            #     st.markdown("### 📰 최종 선정된 뉴스")  
            #     news_style = ""
            #     reason_prefix = "선별 이유: "
            
            # 기본 스타일과 프리픽스 설정 (재평가 여부와 관계없이)
            news_style = ""
            reason_prefix = "선별 이유: "
            
            # 최종 선정된 뉴스 표시
            for news in analysis_result["final_selection"]:
                date_str = format_date(news.get('date', ''))
                
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%m/%d')
                except Exception as e:
                    try:
                        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        formatted_date = date_obj.strftime('%m/%d')
                    except Exception as e:
                        formatted_date = date_str if date_str else '날짜 정보 없음'

                url = news.get('url', 'URL 정보 없음')
                press = news.get('press', '언론사 정보 없음')
                
                st.markdown(f"""
                    <div class="selected-news" style="{news_style}">
                        <div class="news-title-large">{news['title']} ({formatted_date})</div>
                        <div class="news-url">🔗 <a href="{url}" target="_blank">{url}</a></div>
                        <div class="selection-reason">
                            • {reason_prefix}{news['reason']}
                        </div>
                        <div class="news-summary">
                            • 키워드: {', '.join(news['keywords'])} | 관련 계열사: {', '.join(news['affiliates'])} | 언론사: {press}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
            
          
            # 이메일 내용 추가
            email_content += f"{i}. {keyword}\n"
            for news in analysis_result["final_selection"]:
                date_str = news.get('date', '')
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%m/%d')
                except Exception as e:
                    try:
                        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        formatted_date = date_obj.strftime('%m/%d')
                    except Exception as e:
                        formatted_date = date_str if date_str else '날짜 정보 없음'
                
                url = news.get('url', '')
                email_content += f"  - {news['title']} ({formatted_date}) {url}\n"
            email_content += "\n"
            
            st.markdown("---")

    # 모든 키워드 분석이 끝난 후 카테고리별 통합 완료 메시지
    st.success(f"✅ 선택된 {len(selected_categories)}개 카테고리 분석 완료!")
    
    # 5단계: 최종 선택 결과 표시 (루프 바깥으로 이동)
    st.markdown("<div class='subtitle'>🔍 최종 선택 결과</div>", unsafe_allow_html=True)
    
    # 모든 키워드의 최종 선정 뉴스를 통합하여 표시
    all_final_news = []
    for keyword, result in all_results.items():
        if 'final_selection' in result:
            all_final_news.extend(result['final_selection'])
    
    # 최종 선정된 뉴스 표시
    for news in all_final_news:
        date_str = format_date(news.get('date', ''))
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%m/%d')
        except Exception as e:
            try:
                date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                formatted_date = date_obj.strftime('%m/%d')
            except Exception as e:
                formatted_date = date_str if date_str else '날짜 정보 없음'

        url = news.get('url', 'URL 정보 없음')
        press = news.get('press', '언론사 정보 없음')
        
        st.markdown(f"""
            <div class="selected-news">
                <div class="news-title-large">{news['title']} ({formatted_date})</div>
                <div class="news-url">🔗 <a href="{url}" target="_blank">{url}</a></div>
                <div class="selection-reason">
                    • 선별 이유: {news['reason']}
                </div>
                <div class="news-summary">
                    • 키워드: {', '.join(news.get('keywords', []))} | 관련 계열사: {', '.join(news.get('affiliates', []))} | 언론사: {press}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # 모든 키워드 분석이 끝난 후 이메일 미리보기 섹션 추가
    st.markdown("<div class='subtitle'>📧 이메일 미리보기</div>", unsafe_allow_html=True)
    
    # HTML 버전 생성
    html_email_content = "<div style='font-family: Arial, sans-serif; max-width: 800px; font-size: 14px; line-height: 1.5;'>"
    
    html_email_content += "<div style='margin-top: 20px; font-size: 14px;'>안녕하세요, 좋은 아침입니다!<br>오늘의 Client Intelligence 전달 드립니다.<br><br></div>"
    plain_email_content = "\n안녕하세요, 좋은 아침입니다!\n오늘의 Client Intelligence 전달 드립니다."
    
    html_email_content += "<div style='font-size: 14px; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #000;'>[Client Intelligence]</div>"
    
    # 일반 텍스트 버전 생성 (복사용)
    plain_email_content += "[Client Intelligence]\n\n"
    
    def clean_title(title):
        """Clean title by removing the press name pattern at the end"""
        # Remove the press pattern (e.g., '제목 - 조선일보', '제목-조선일보', '제목 - Chosun Biz')
        title = re.sub(r"\s*-\s*[가-힣A-Za-z0-9\s]+$", "", title).strip()
        return title

    # 카테고리별로 뉴스 그룹화
    for i, category in enumerate(selected_categories, 1):
        # HTML 버전에서 카테고리를 파란색으로 표시
        html_email_content += f"<div style='font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px; color: #0000FF;'>{i}. {category}</div>"
        html_email_content += "<ul style='list-style-type: none; padding-left: 20px; margin: 0;'>"
        
        # 텍스트 버전에서도 카테고리 구분을 위해 줄바꿈 추가
        plain_email_content += f"{i}. {category}\n"
        
        # 해당 카테고리의 모든 키워드 뉴스 수집
        category_news = []
        for keyword in KEYWORD_CATEGORIES.get(category, []):
            if keyword in all_results:
                news_list = all_results[keyword]
                if isinstance(news_list, dict) and 'final_selection' in news_list:
                    category_news.extend(news_list['final_selection'])
        
        if not category_news:
            # 최종 선정 뉴스가 0건인 경우 안내 문구 추가
            html_email_content += "<li style='margin-bottom: 8px; font-size: 14px; color: #888;'>AI 분석결과 금일자로 회계법인 관점에서 특별히 주목할 만한 기사가 없습니다.</li>"
            plain_email_content += "  - AI 분석결과 금일자로 회계법인 관점에서 특별히 주목할 만한 기사가 없습니다.\n"
        else:
            for news in category_news:
                # news 객체 유효성 검사
                if not news or not isinstance(news, dict):
                    print(f"유효하지 않은 뉴스 객체: {news}")
                    continue
                
                # 날짜 형식 변환
                date_str = news.get('date', '')
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%m/%d')
                except Exception as e:
                    try:
                        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        formatted_date = date_obj.strftime('%m/%d')
                    except Exception as e:
                        formatted_date = date_str if date_str else '날짜 정보 없음'
                
                url = news.get('url', '')
                title = news.get('title', '')
                # 이메일 미리보기에서는 언론사 패턴 제거
                title = clean_title(title)
                # HTML 버전 - 링크를 [파일 링크]로 표시하고 글자 크기 통일, 본문 bold 처리
                html_email_content += f"<li style='margin-bottom: 8px; font-size: 14px;'><span style='font-weight: bold;'>- {title} ({formatted_date})</span> <a href='{url}' style='color: #1a0dab; text-decoration: none;'>[기사 링크]</a></li>"
                
                # 텍스트 버전 - 링크를 [파일 링크]로 표시하고 실제 URL은 그 다음 줄에
                plain_email_content += f"  - {title} ({formatted_date}) [기사 링크]\n    {url}\n"
        
        html_email_content += "</ul>"
        plain_email_content += "\n"
    
    # 서명 추가
    html_email_content += "<div style='margin-top: 20px; font-size: 14px;'><br>감사합니다.<br>Client & Market 드림</div>"
    plain_email_content += "\n감사합니다.\nClient & Market 드림"
    
    html_email_content += "</div>"
    
    # 이메일 미리보기 표시
    st.markdown(f"<div class='email-preview'>{html_email_content}</div>", unsafe_allow_html=True)

    # 워드 문서 다운로드 섹션 제거됨 (현재 사용하지 않음)
    
    # CSV 다운로드 섹션 (인코딩 문제 해결)
    st.markdown("<div class='subtitle'>📊 CSV 다운로드 (인코딩 문제 해결)</div>", unsafe_allow_html=True)
    
    if all_results:
        try:
            # CSV용 데이터 준비
            csv_data = []
            for keyword, result in all_results.items():
                if 'final_selection' in result:
                    for news in result['final_selection']:
                        # news 객체 유효성 검사
                        if not news or not isinstance(news, dict):
                            print(f"CSV 생성 중 유효하지 않은 뉴스 객체: {news}")
                            continue
                        
                        csv_data.append({
                            '키워드': clean_html_entities(keyword),
                            '제목': clean_html_entities(news.get('title', '')),
                            '날짜': clean_html_entities(news.get('date', '')),
                            '언론사': clean_html_entities(news.get('press', '')),
                            '선별이유': clean_html_entities(news.get('reason', '')),
                            '키워드': clean_html_entities(', '.join(news.get('keywords', []))),
                            '관련계열사': clean_html_entities(', '.join(news.get('affiliates', []))),
                            'URL': clean_html_entities(news.get('url', ''))
                        })
            
            if csv_data:
                # DataFrame 생성
                df = pd.DataFrame(csv_data)
                
                # CSV 파일 생성 (인코딩 문제 해결)
                csv_buffer = io.StringIO()
                # UTF-8 BOM을 추가하여 Excel에서 한글이 깨지지 않도록 함
                df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_content = csv_buffer.getvalue()
                
                # CSV 다운로드 버튼
                current_date = datetime.now().strftime("%Y%m%d")
                csv_filename = f"PwC_뉴스분석_{current_date}.csv"
                
                st.download_button(
                    label="📥 CSV 다운로드 (.csv) - 인코딩 문제 해결됨",
                    data=csv_content,
                    file_name=csv_filename,
                    mime="text/csv"
                )
                
                st.success("CSV 파일이 생성되었습니다. UTF-8 BOM 인코딩으로 한글이 깨지지 않습니다.")
                
                # 미리보기 표시 (클릭 가능한 링크 포함)
                st.markdown("**CSV 미리보기:**")
                
                # HTML 테이블로 표시하여 링크를 클릭 가능하게 만듦
                html_table = df.to_html(
                    index=False, 
                    escape=False,  # HTML 이스케이프 방지
                    formatters={
                        'URL': lambda x: f'<a href="{x}" target="_blank" style="color: #0077b6; text-decoration: underline;">🔗 링크</a>' if x else ''
                    }
                )
                
                # HTML 테이블 스타일링
                styled_html = f"""
                <div style="overflow-x: auto;">
                    <style>
                        table {{
                            border-collapse: collapse;
                            width: 100%;
                            font-family: Arial, sans-serif;
                        }}
                        th, td {{
                            border: 1px solid #ddd;
                            padding: 8px;
                            text-align: left;
                            vertical-align: top;
                        }}
                        th {{
                            background-color: #f2f2f2;
                            font-weight: bold;
                        }}
                        tr:nth-child(even) {{
                            background-color: #f9f9f9;
                        }}
                        tr:hover {{
                            background-color: #f5f5f5;
                        }}
                        a {{
                            color: #0077b6;
                            text-decoration: underline;
                        }}
                        a:hover {{
                            color: #0056b3;
                        }}
                    </style>
                    {html_table}
                </div>
                """
                
                st.markdown(styled_html, unsafe_allow_html=True)
                
                # 원본 DataFrame도 표시 (데이터 확인용)
                st.markdown("**원본 데이터 (편집용):**")
                st.dataframe(df)
            else:
                st.warning("CSV로 다운로드할 뉴스가 없습니다.")
                
        except Exception as e:
            st.error(f"CSV 생성 중 오류가 발생했습니다: {str(e)}")



else:
    # 초기 화면 설명 (주석 처리됨)
    """
    ### 👋 PwC 뉴스 분석기에 오신 것을 환영합니다!
    
    이 도구는 입력한 키워드에 대한 최신 뉴스를 자동으로 수집하고, 회계법인 관점에서 중요한 뉴스를 선별하여 분석해드립니다.
    
    #### 주요 기능:
    1. 최신 뉴스 자동 수집 (기본 100개)
    2. 신뢰할 수 있는 언론사 필터링
    3. 6단계 AI 기반 뉴스 분석 프로세스:
       - 1단계: 뉴스 수집 - 키워드 기반으로 최신 뉴스 데이터 수집
       - 2단계: 유효 언론사 필터링 - 신뢰할 수 있는 언론사 선별
       - 3단계: 제외/보류/유지 판단 - 회계법인 관점에서의 중요도 1차 분류
       - 4단계: 유사 뉴스 그룹핑 - 중복 기사 제거 및 대표 기사 선정
       - 5단계: 중요도 평가 및 최종 선정 - 회계법인 관점의 중요도 평가
       - 6단계: 필요시 재평가 - 선정된 뉴스가 없을 경우 AI가 기준을 완화하여 재평가
    4. 선별된 뉴스에 대한 상세 정보 제공
       - 제목 및 날짜
       - 원문 링크
       - 선별 이유
       - 키워드, 관련 계열사, 언론사 정보
    5. 분석 결과 이메일 형식 미리보기
    
    #### 사용 방법:
    1. 사이드바에서 분석할 기업을 선택하세요 (최대 10개)
       - 기본 제공 기업 목록에서 선택
       - 새로운 기업 직접 추가 가능
    2. GPT 모델을 선택하세요
       - gpt-4o: 빠르고 실시간 (기본값)
    3. 날짜 필터를 설정하세요
       - 기본값: 어제 또는 지난 금요일(월요일인 경우)부터 오늘까지
    4. "뉴스 분석 시작" 버튼을 클릭하세요
    
    #### 분석 결과 확인:
    - 각 키워드별 최종 선정된 중요 뉴스
    - 선정 과정의 중간 결과(제외/보류/유지, 그룹핑 등)
    - 선정된 모든 뉴스의 요약 이메일 미리보기
    - 디버그 정보 (시스템 프롬프트, AI 응답 등)
    
    """

# 푸터
st.markdown("---")
st.markdown("© 2025 PwC 뉴스 분석기 | 회계법인 관점의 뉴스 분석 도구")

# RSS 기반 뉴스 수집 함수들
def collect_news_from_rss(keyword, start_date, end_date):
    """RSS 피드에서 뉴스 수집 - 모든 언론사에서 키워드 기반으로 수집"""
    news_list = []
    
    # 주요 언론사 RSS 피드 목록 (한국 주요 언론사들)
    rss_feeds = {
        '조선일보': 'https://www.chosun.com/arc/outboundfeeds/rss/',
        '중앙일보': 'https://rss.joins.com/joins_news_list.xml',
        '동아일보': 'https://www.donga.com/news/RSS/newsflash.xml',
        '한국일보': 'https://www.hankookilbo.com/rss/rss.xml',
        '경향신문': 'https://www.khan.co.kr/rss/rssdata/kh_news.xml',
        '한겨레': 'https://www.hani.co.kr/rss/',
        '서울신문': 'https://www.seoul.co.kr/rss/',
        '매일경제': 'https://www.mk.co.kr/rss/30000001/',
        '한국경제': 'https://www.hankyung.com/rss/',
        '이데일리': 'https://www.edaily.co.kr/rss/',
        '머니투데이': 'https://www.mt.co.kr/rss/',
        '파이낸셜뉴스': 'https://www.fnnews.com/rss/rss.xml',
        '아시아경제': 'https://www.asiae.co.kr/rss/',
        '뉴스1': 'https://www.news1.kr/rss/',
        '연합뉴스': 'https://www.yonhapnews.co.kr/feed/',
        '뉴시스': 'https://www.newsis.com/rss/',
        '스포츠조선': 'https://sports.chosun.com/rss/',
        '스포츠동아': 'https://sports.donga.com/rss/',
        '스포츠한국': 'https://sports.hankooki.com/rss/',
        '스포츠경향': 'https://sports.khan.co.kr/rss/'
    }
    
    for press_name, rss_url in rss_feeds.items():
        try:
            # RSS 피드 파싱
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries:
                # 키워드 검색 (제목과 요약에서 검색)
                if keyword.lower() in entry.title.lower() or keyword.lower() in entry.description.lower():
                    # 날짜 파싱
                    pub_date = parse_rss_date(entry.published)
                    
                    # 날짜 필터링만 적용 (언론사 필터링 제거)
                    if start_date <= pub_date <= end_date:
                        news_item = {
                            'title': clean_title(entry.title),
                            'url': entry.link,
                            'date': pub_date.strftime('%Y-%m-%d'),
                            'press': press_name,
                            'summary': clean_summary(entry.description),
                            'keywords': [keyword],
                            'affiliates': []
                        }
                        news_list.append(news_item)
                        
        except Exception as e:
            st.warning(f"{press_name} RSS 파싱 오류: {str(e)}")
            continue
    
    return news_list

def parse_rss_date(date_str):
    """RSS 날짜 문자열을 datetime 객체로 변환"""
    try:
        # 다양한 RSS 날짜 형식 처리
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S %z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
                
        # 기본값: 현재 시간
        return datetime.now()
        
    except:
        return datetime.now()

def clean_title(title):
    """뉴스 제목 정리"""
    # 언론사명 패턴 제거 (예: "제목 - 조선일보")
    title = re.sub(r'\s*-\s*[가-힣A-Za-z0-9\s]+$', '', title).strip()
    return title

def clean_summary(summary):
    """뉴스 요약 정리"""
    # HTML 태그 제거
    soup = BeautifulSoup(summary, 'html.parser')
    clean_text = soup.get_text()
    # 연속된 공백 정리
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def analyze_news_with_ai(news_list, analysis_prompt):
    """AI를 사용하여 뉴스 분석 및 선별"""
    try:
        # OpenAI API 호출 (실제 API 키는 환경변수에서 가져와야 함)
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # 뉴스 목록을 JSON 형태로 변환
        news_data = json.dumps([{
            'title': news['title'],
            'summary': news['summary'],
            'press': news['press'],
            'date': news['date']
        } for news in news_list], ensure_ascii=False)
        
        # AI 분석 요청
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": f"다음 뉴스 목록을 분석해주세요:\n\n{news_data}"}
            ],
            temperature=0.3
        )
        
        # AI 응답 파싱
        ai_response = response.choices[0].message.content
        
        # JSON 응답 파싱 시도
        try:
            result = json.loads(ai_response)
            return result
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 구조 반환
            return {
                "selected_news": [],
                "excluded_news": [],
                "error": "AI 응답을 파싱할 수 없습니다."
            }
            
    except Exception as e:
        st.error(f"AI 분석 중 오류 발생: {str(e)}")
        return {
            "selected_news": [],
            "excluded_news": [],
            "error": f"AI 분석 실패: {str(e)}"
        }

def analyze_news_direct(keyword, start_date, end_date, trusted_press, analysis_prompt):
    """직접 구현한 뉴스 분석 함수"""
    
    # 1단계: RSS에서 뉴스 수집
    with st.spinner(f"'{keyword}' 관련 뉴스를 RSS에서 수집 중..."):
        collected_news = collect_news_from_rss(keyword, start_date, end_date)
    
    if not collected_news:
        return {
            "collected_count": 0,
            "final_selection": [],
            "error": "수집된 뉴스가 없습니다."
        }
    
    # 2단계: AI 분석 및 선별
    with st.spinner(f"'{keyword}' 뉴스 분석 중..."):
        analysis_result = analyze_news_with_ai(collected_news, analysis_prompt)
    
    # 3단계: 결과 정리
    if "selected_news" in analysis_result:
        # AI 응답을 기존 형식에 맞게 변환
        final_selection = []
        for selected in analysis_result["selected_news"]:
            # 원본 뉴스에서 해당 항목 찾기
            for news in collected_news:
                if news['title'] == selected['title']:
                    final_selection.append(news)
                    break
        
        return {
            "collected_count": len(collected_news),
            "final_selection": final_selection,
            "ai_analysis": analysis_result
        }
    else:
        return {
            "collected_count": len(collected_news),
            "final_selection": [],
            "error": analysis_result.get("error", "알 수 없는 오류")
        }
