import streamlit as st
import re


# ✅ 무조건 첫 Streamlit 명령어
st.set_page_config(
    page_title="PwC 뉴스 분석기",
    page_icon="📊",
    layout="wide",
)



from datetime import datetime, timedelta, timezone
import os
from PIL import Image
import docx
from docx.shared import Pt, RGBColor, Inches
import io
from urllib.parse import urlparse
from news_service import NewsAnalysisService

# Import centralized configuration
from config import (
    COMPANY_CATEGORIES,
    COMPANY_KEYWORD_MAP,
    COMPANY_GROUP_MAPPING,
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
    # 새로 추가되는 회사별 기준들
    COMPANY_ADDITIONAL_EXCLUSION_CRITERIA,
    COMPANY_ADDITIONAL_DUPLICATE_HANDLING,
    COMPANY_ADDITIONAL_SELECTION_CRITERIA
)

# 한국 시간대(KST) 정의
KST = timezone(timedelta(hours=9))


def parse_press_config(press_dict_str: str) -> Dict[str, List[str]]:
    """UI에서 설정한 언론사 문자열을 딕셔너리로 파싱하는 함수"""
    press_config = {}
    if isinstance(press_dict_str, str) and press_dict_str.strip():
        try:
            lines = press_dict_str.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and ': ' in line:
                    press_name, aliases_str = line.split(':', 1)
                    try:
                        # 문자열 형태의 리스트를 실제 리스트로 변환
                        aliases = eval(aliases_str.strip())
                        press_config[press_name.strip()] = aliases
                    except Exception as e:
                        print(f"언론사 파싱 실패: {line}, 오류: {str(e)}")
        except Exception as e:
            print(f"전체 언론사 파싱 실패: {str(e)}")
    
    return press_config


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

# 회사별 추가 기준을 적용하는 함수들
def get_enhanced_exclusion_criteria(companies):
    """회사별 제외 기준을 추가한 프롬프트 반환 (여러 회사 지원)"""
    base_criteria = EXCLUSION_CRITERIA
    
    # companies가 문자열이면 리스트로 변환
    if isinstance(companies, str):
        companies = [companies]
    
    # 선택된 모든 회사의 추가 기준을 합침
    all_additional_criteria = ""
    for company in companies:
        additional_criteria = COMPANY_ADDITIONAL_EXCLUSION_CRITERIA.get(company, "")
        if additional_criteria:
            all_additional_criteria += additional_criteria
    
    return base_criteria + all_additional_criteria

def get_enhanced_duplicate_handling(companies):
    """회사별 중복 처리 기준을 추가한 프롬프트 반환 (여러 회사 지원)"""
    base_criteria = DUPLICATE_HANDLING
    
    # companies가 문자열이면 리스트로 변환
    if isinstance(companies, str):
        companies = [companies]
    
    # 선택된 모든 회사의 추가 기준을 합침
    all_additional_criteria = ""
    for company in companies:
        additional_criteria = COMPANY_ADDITIONAL_DUPLICATE_HANDLING.get(company, "")
        if additional_criteria:
            all_additional_criteria += additional_criteria
    
    return base_criteria + all_additional_criteria

def get_enhanced_selection_criteria(companies):
    """회사별 선택 기준을 추가한 프롬프트 반환 (여러 회사 지원)"""
    base_criteria = SELECTION_CRITERIA
    
    # companies가 문자열이면 리스트로 변환
    if isinstance(companies, str):
        companies = [companies]
    
    # 선택된 모든 회사의 추가 기준을 합침
    all_additional_criteria = ""
    for company in companies:
        additional_criteria = COMPANY_ADDITIONAL_SELECTION_CRITERIA.get(company, "")
        if additional_criteria:
            all_additional_criteria += additional_criteria
    
    return base_criteria + all_additional_criteria
            
# 워드 파일 생성 함수
def create_word_document(keyword, final_selection, analysis=""):
    # 새 워드 문서 생성
    doc = docx.Document()
    
    # 제목 스타일 설정
    title = doc.add_heading(f'PwC 뉴스 분석 보고서: {keyword}', level=0)
    for run in title.runs:
        run.font.color.rgb = RGBColor(208, 74, 2)  # PwC 오렌지 색상
    
    # 분석 요약 추가
    if analysis:
        doc.add_heading('회계법인 관점의 분석 결과', level=1)
        doc.add_paragraph(analysis)
    
    # 선별된 주요 뉴스 추가
    doc.add_heading('선별된 주요 뉴스', level=1)
    
    for i, news in enumerate(final_selection):
        p = doc.add_paragraph()
        p.add_run(f"{i+1}. {news['title']}").bold = True
        
        # 날짜 정보 추가
        date_str = news.get('date', '날짜 정보 없음')
        date_paragraph = doc.add_paragraph()
        date_paragraph.add_run(f"날짜: {date_str}").italic = True
        
        # 선정 사유 추가
        reason = news.get('reason', '')
        if reason:
            doc.add_paragraph(f"선정 사유: {reason}")
        
        # 키워드 추가
        keywords = news.get('keywords', [])
        if keywords:
            doc.add_paragraph(f"키워드: {', '.join(keywords)}")
        
        # 관련 계열사 추가
        affiliates = news.get('affiliates', [])
        if affiliates:
            doc.add_paragraph(f"관련 계열사: {', '.join(affiliates)}")
        
        # 언론사 추가
        press = news.get('press', '알 수 없음')
        doc.add_paragraph(f"언론사: {press}")
        
        # URL 추가
        url = news.get('url', '')
        if url:
            doc.add_paragraph(f"출처: {url}")
        
        # 구분선 추가
        if i < len(final_selection) - 1:
            doc.add_paragraph("").add_run().add_break()
    
    # 날짜 및 푸터 추가
    current_date = datetime.now().strftime("%Y년 %m월 %d일")
    doc.add_paragraph(f"\n보고서 생성일: {current_date}")
    doc.add_paragraph("© 2024 PwC 뉴스 분석기 | 회계법인 관점의 뉴스 분석 도구")
    
    return doc

# BytesIO 객체로 워드 문서 저장
def get_binary_file_downloader_html(doc, file_name):
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

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

# 로고와 제목
col1, col2 = st.columns([1, 5])
with col1:
    # 로고 표시
    logo_path = "pwc_logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=100)
    else:
        st.error("로고 파일을 찾을 수 없습니다. 프로젝트 루트에 'pwc_logo.png' 파일을 추가해주세요.")

with col2:
    st.markdown("<h1 class='main-title'>PwC 뉴스 분석기</h1>", unsafe_allow_html=True)
    st.markdown("회계법인 관점에서 중요한 뉴스를 자동으로 분석하는 AI 도구")

# 기본 선택 카테고리를 Anchor로 설정
COMPANIES = COMPANY_CATEGORIES["Anchor"]

# 사이드바 설정
st.sidebar.title("🔍 분석 설정")

# 0단계: 기본 설정
st.sidebar.markdown("### 📋 0단계: 기본 설정")

# 유효 언론사 설정
valid_press_dict = st.sidebar.text_area(
    "📰 유효 언론사 설정",
    value="""조선일보: ["조선일보", "chosun", "chosun.com"]
    중앙일보: ["중앙일보", "joongang", "joongang.co.kr", "joins.com"]
    동아일보: ["동아일보", "donga", "donga.com"]
    조선비즈: ["조선비즈", "chosunbiz", "biz.chosun.com"]
    매거진한경: ["매거진한경", "magazine.hankyung", "magazine.hankyung.com"]
    한국경제: ["한국경제", "한경", "hankyung", "hankyung.com", "한경닷컴"]
    매일경제: ["매일경제", "매경", "mk", "mk.co.kr"]
    연합뉴스: ["연합뉴스", "yna", "yna.co.kr"]
    파이낸셜뉴스: ["파이낸셜뉴스", "fnnews", "fnnews.com"]
    데일리팜: ["데일리팜", "dailypharm", "dailypharm.com"]
    IT조선: ["it조선", "it.chosun.com", "itchosun"]
    머니투데이: ["머니투데이", "mt", "mt.co.kr"]
    비즈니스포스트: ["비즈니스포스트", "businesspost", "businesspost.co.kr"]
    이데일리: ["이데일리", "edaily", "edaily.co.kr"]
    아시아경제: ["아시아경제", "asiae", "asiae.co.kr"]
    뉴스핌: ["뉴스핌", "newspim", "newspim.com"]
    뉴시스: ["뉴시스", "newsis", "newsis.com"]
    헤럴드경제: ["헤럴드경제", "herald", "heraldcorp", "heraldcorp.com"]""",
    help="분석에 포함할 신뢰할 수 있는 언론사와 그 별칭을 설정하세요. 형식: '언론사: [별칭1, 별칭2, ...]'",
    key="valid_press_dict"
)

# 추가 언론사 설정 (재평가 시에만 사용됨)
additional_press_dict = st.sidebar.text_area(
    "📰 추가 언론사 설정 (재평가 시에만 사용)",
    value="""철강금속신문: ["철강금속신문", "snmnews", "snmnews.com"]
    에너지신문: ["에너지신문", "energy-news", "energy-news.co.kr"]
    이코노믹데일리: ["이코노믹데일리", "economidaily", "economidaily.com"]""",
    help="기본 언론사에서 뉴스가 선택되지 않을 경우, 재평가 단계에서 추가로 고려할 언론사와 별칭을 설정하세요. 형식: '언론사: [별칭1, 별칭2, ...]'",
    key="additional_press_dict"
)

# 구분선 추가
st.sidebar.markdown("---")

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

# 기업 선택 섹션 제목
st.sidebar.markdown("### 🏢 분석할 기업 선택")

# 기업 카테고리 선택
selected_category = st.sidebar.radio(
    "기업 카테고리를 선택하세요",
    options=list(COMPANY_CATEGORIES.keys()),
    index=0,  # Anchor를 기본값으로 설정
    help="분석할 기업 카테고리를 선택하세요. Anchor(핵심), Growth(성장), Whitespace(신규) 중에서 선택할 수 있습니다."
)

# 선택된 카테고리에 따라 그룹 목록 가져오기
GROUPS = COMPANY_CATEGORIES[selected_category]

# 그룹별로 기업 선택
selected_companies = []
st.sidebar.markdown("**그룹별로 분석할 기업을 선택하세요:**")

for group in GROUPS:
    if group in COMPANY_GROUP_MAPPING:
        companies_in_group = COMPANY_GROUP_MAPPING[group]
        
        # 그룹별로 expander 생성
        with st.sidebar.expander(f"📁 {group} ({len(companies_in_group)}개 기업)", expanded=True):
            st.markdown(f"**{group} 그룹 기업들:**")
            
            # 그룹 내 기업들을 체크박스로 선택
            selected_in_group = st.multiselect(
                f"{group} 그룹에서 선택",
                options=companies_in_group,
                default=companies_in_group[:3] if len(companies_in_group) > 3 else companies_in_group,  # 최대 3개 기본 선택
                max_selections=min(5, len(companies_in_group)),  # 그룹당 최대 5개
                help=f"{group} 그룹에서 분석할 기업을 선택하세요. 최대 {min(5, len(companies_in_group))}개까지 선택 가능합니다.",
                key=f"group_{group}"
            )
            
            # 선택된 기업들을 전체 목록에 추가
            selected_companies.extend(selected_in_group)
            
            # 선택된 기업 수 표시
            if selected_in_group:
                st.success(f"✅ {group}: {len(selected_in_group)}개 기업 선택됨")
            else:
                st.info(f"ℹ️ {group}: 선택된 기업 없음")

# 전체 선택된 기업 수 표시
if selected_companies:
    st.sidebar.success(f"🎯 **총 {len(selected_companies)}개 기업 선택됨**")
    st.sidebar.markdown("**선택된 기업들:**")
    for company in selected_companies:
        st.sidebar.markdown(f"• {company}")
else:
    st.sidebar.warning("⚠️ 분석할 기업을 선택해주세요!")

# 새로운 기업 추가 섹션 (그룹 선택 포함)
st.sidebar.markdown("---")
st.sidebar.markdown("### ➕ 새로운 기업 추가")

new_company_group = st.sidebar.selectbox(
    "새 기업을 추가할 그룹 선택",
    options=GROUPS,
    help="새로운 기업을 추가할 그룹을 선택하세요."
)

new_company = st.sidebar.text_input(
    "새로운 기업명",
    value="",
    help="분석하고 싶은 기업명을 입력하고 Enter를 누르세요. (예: 네이버, 카카오, 현대중공업 등)"
)

# 새로운 기업 추가 로직 수정
if new_company and new_company not in selected_companies:
    # 선택된 그룹에 기업 추가
    if new_company_group in COMPANY_GROUP_MAPPING:
        COMPANY_GROUP_MAPPING[new_company_group].append(new_company)
        
        # 세션 상태도 업데이트
        if 'company_group_mapping' not in st.session_state:
            st.session_state.company_group_mapping = COMPANY_GROUP_MAPPING.copy()
        else:
            st.session_state.company_group_mapping[new_company_group].append(new_company)
        
        # 새 기업에 대한 기본 연관 키워드 설정 (기업명 자체만 포함)
        COMPANY_KEYWORD_MAP[new_company] = [new_company]
        
        # 세션 상태도 함께 업데이트
        if 'company_keyword_map' not in st.session_state:
            st.session_state.company_keyword_map = COMPANY_KEYWORD_MAP.copy()
        else:
            st.session_state.company_keyword_map[new_company] = [new_company]
        
        st.sidebar.success(f"✅ '{new_company}'이(가) '{new_company_group}' 그룹에 추가되었습니다!")
        
        # 페이지 새로고침을 위한 버튼
        if st.sidebar.button("🔄 페이지 새로고침", key="refresh_page"):
            st.rerun()

# 연관 키워드 관리 섹션
st.sidebar.markdown("### 🔍 연관 키워드 관리")
st.sidebar.markdown("각 기업의 연관 키워드를 확인하고 편집할 수 있습니다.")

# 세션 상태에 COMPANY_KEYWORD_MAP 및 COMPANY_GROUP_MAPPING 저장 (초기화)
if 'company_keyword_map' not in st.session_state:
    st.session_state.company_keyword_map = COMPANY_KEYWORD_MAP.copy()
    
if 'company_group_mapping' not in st.session_state:
    st.session_state.company_group_mapping = COMPANY_GROUP_MAPPING.copy()

# 연관 키워드 UI 개선 (선택된 기업이 있을 때만 표시)
if selected_companies:
    # 선택된 기업 중에서 관리할 기업 선택
    company_to_edit = st.sidebar.selectbox(
        "연관 키워드를 관리할 기업 선택",
        options=selected_companies,
        help="키워드를 확인하거나 추가할 기업을 선택하세요."
    )
    
    if company_to_edit:
        # 현재 연관 키워드 표시 (세션 상태에서 가져옴)
        current_keywords = st.session_state.company_keyword_map.get(company_to_edit, [company_to_edit])
        st.sidebar.markdown(f"**현재 '{company_to_edit}'의 연관 키워드:**")
        keyword_list = ", ".join(current_keywords)
        st.sidebar.code(keyword_list)
        
        # 연관 키워드 편집
        new_keywords = st.sidebar.text_area(
            "연관 키워드 편집",
            value=keyword_list,
            help="쉼표(,)로 구분하여 키워드를 추가/편집하세요.",
            key=f"edit_{company_to_edit}"  # 고유 키 추가
        )
        
        # 키워드 업데이트 함수
        def update_keywords():
            # 쉼표로 구분된 텍스트를 리스트로 변환
            updated_keywords = [kw.strip() for kw in new_keywords.split(",") if kw.strip()]
            
            # 업데이트
            if updated_keywords:
                st.session_state.company_keyword_map[company_to_edit] = updated_keywords
                st.sidebar.success(f"'{company_to_edit}'의 연관 키워드가 업데이트되었습니다!")
            else:
                # 비어있으면 기업명 자체만 포함
                st.session_state.company_keyword_map[company_to_edit] = [company_to_edit]
                st.sidebar.warning(f"연관 키워드가 비어있어 기업명만 포함됩니다.")
        
        # 변경 사항 적용 버튼
        if st.sidebar.button("연관 키워드 업데이트", key=f"update_{company_to_edit}", on_click=update_keywords):
            pass  # 실제 업데이트는 on_click에서 처리되므로 여기서는 아무것도 하지 않음

# 미리보기 버튼 - 모든 검색어 확인
with st.sidebar.expander("🔍 전체 검색 키워드 미리보기"):
    if selected_companies:
        for i, company in enumerate(selected_companies, 1):
            # 세션 상태에서 키워드 가져오기
            company_keywords = st.session_state.company_keyword_map.get(company, [company])
            st.markdown(f"**{i}. {company}**")
            # 연관 키워드 표시
            for j, kw in enumerate(company_keywords, 1):
                st.write(f"  {j}) {kw}")
    else:
        st.info("먼저 분석할 기업을 선택해주세요.")

# 선택된 키워드들을 통합 (검색용)
keywords = []
for company in selected_companies:
    # 기업명 자체와 연관 키워드 모두 추가 (세션 상태에서 가져옴)
    company_keywords = st.session_state.company_keyword_map.get(company, [company])
    keywords.extend(company_keywords)

# 중복 제거
keywords = list(set(keywords))

# 구분선 추가
st.sidebar.markdown("---")

# 회사별 특화 기준 관리 섹션
st.sidebar.markdown("### 🎯 회사별 특화 기준 관리")
st.sidebar.markdown("각 기업의 AI 분석 특화 기준을 확인하고 편집할 수 있습니다.")

# 회사별 특화 기준 관리 UI (선택된 기업이 있을 때만 표시)
if selected_companies:
    # 선택된 기업 중에서 관리할 기업 선택
    company_to_manage = st.sidebar.selectbox(
        "특화 기준을 관리할 기업 선택",
        options=selected_companies,
        help="AI 분석 특화 기준을 확인하거나 편집할 기업을 선택하세요.",
        key="company_to_manage"
    )
    
    if company_to_manage:
        # 탭 형태로 1~3단계 기준을 구분
        criteria_tabs = st.sidebar.radio(
            f"'{company_to_manage}' 특화 기준 선택",
            ["1단계: 제외 기준", "2단계: 그룹핑 기준", "3단계: 선택 기준"],
            key=f"criteria_tabs_{company_to_manage}"
        )
        
        # 세션 상태에서 회사별 특화 기준 관리 (초기화)
        if 'company_additional_exclusion_criteria' not in st.session_state:
            st.session_state.company_additional_exclusion_criteria = COMPANY_ADDITIONAL_EXCLUSION_CRITERIA.copy()
        if 'company_additional_duplicate_handling' not in st.session_state:
            st.session_state.company_additional_duplicate_handling = COMPANY_ADDITIONAL_DUPLICATE_HANDLING.copy()
        if 'company_additional_selection_criteria' not in st.session_state:
            st.session_state.company_additional_selection_criteria = COMPANY_ADDITIONAL_SELECTION_CRITERIA.copy()
        
        if criteria_tabs == "1단계: 제외 기준":
            current_criteria = st.session_state.company_additional_exclusion_criteria.get(company_to_manage, "")
            st.sidebar.markdown(f"**현재 '{company_to_manage}'의 제외 특화 기준:**")
            if current_criteria.strip():
                st.sidebar.code(current_criteria, language="text")
            else:
                st.sidebar.info("설정된 특화 기준이 없습니다.")
            
            # 편집 영역
            new_exclusion_criteria = st.sidebar.text_area(
                "제외 특화 기준 편집",
                value=current_criteria,
                help="이 회사에만 적용될 추가 제외 기준을 입력하세요.",
                key=f"edit_exclusion_{company_to_manage}",
                height=150
            )
            
            # 업데이트 함수
            def update_exclusion_criteria():
                st.session_state.company_additional_exclusion_criteria[company_to_manage] = new_exclusion_criteria
                st.sidebar.success(f"'{company_to_manage}'의 제외 특화 기준이 업데이트되었습니다!")
            
            # 업데이트 버튼
            if st.sidebar.button("제외 기준 업데이트", key=f"update_exclusion_{company_to_manage}", on_click=update_exclusion_criteria):
                pass
                
        elif criteria_tabs == "2단계: 그룹핑 기준":
            current_criteria = st.session_state.company_additional_duplicate_handling.get(company_to_manage, "")
            st.sidebar.markdown(f"**현재 '{company_to_manage}'의 그룹핑 특화 기준:**")
            if current_criteria.strip():
                st.sidebar.code(current_criteria, language="text")
            else:
                st.sidebar.info("설정된 특화 기준이 없습니다.")
            
            # 편집 영역
            new_duplicate_criteria = st.sidebar.text_area(
                "그룹핑 특화 기준 편집",
                value=current_criteria,
                help="이 회사에만 적용될 추가 그룹핑 기준을 입력하세요.",
                key=f"edit_duplicate_{company_to_manage}",
                height=150
            )
            
            # 업데이트 함수
            def update_duplicate_criteria():
                st.session_state.company_additional_duplicate_handling[company_to_manage] = new_duplicate_criteria
                st.sidebar.success(f"'{company_to_manage}'의 그룹핑 특화 기준이 업데이트되었습니다!")
            
            # 업데이트 버튼
            if st.sidebar.button("그룹핑 기준 업데이트", key=f"update_duplicate_{company_to_manage}", on_click=update_duplicate_criteria):
                pass
                
        elif criteria_tabs == "3단계: 선택 기준":
            current_criteria = st.session_state.company_additional_selection_criteria.get(company_to_manage, "")
            st.sidebar.markdown(f"**현재 '{company_to_manage}'의 선택 특화 기준:**")
            if current_criteria.strip():
                st.sidebar.code(current_criteria, language="text")
            else:
                st.sidebar.info("설정된 특화 기준이 없습니다.")
            
            # 편집 영역
            new_selection_criteria = st.sidebar.text_area(
                "선택 특화 기준 편집",
                value=current_criteria,
                help="이 회사에만 적용될 추가 선택 기준을 입력하세요.",
                key=f"edit_selection_{company_to_manage}",
                height=150
            )
            
            # 업데이트 함수
            def update_selection_criteria():
                st.session_state.company_additional_selection_criteria[company_to_manage] = new_selection_criteria
                st.sidebar.success(f"'{company_to_manage}'의 선택 특화 기준이 업데이트되었습니다!")
            
            # 업데이트 버튼
            if st.sidebar.button("선택 기준 업데이트", key=f"update_selection_{company_to_manage}", on_click=update_selection_criteria):
                pass
else:
    st.sidebar.info("먼저 분석할 기업을 선택해주세요.")

# 미리보기 버튼 - 모든 회사별 특화 기준 확인
with st.sidebar.expander("🔍 전체 회사별 특화 기준 미리보기"):
    if selected_companies:
        # 세션 상태가 초기화되지 않은 경우를 위한 안전장치
        if 'company_additional_exclusion_criteria' not in st.session_state:
            st.session_state.company_additional_exclusion_criteria = COMPANY_ADDITIONAL_EXCLUSION_CRITERIA.copy()
        if 'company_additional_duplicate_handling' not in st.session_state:
            st.session_state.company_additional_duplicate_handling = COMPANY_ADDITIONAL_DUPLICATE_HANDLING.copy()
        if 'company_additional_selection_criteria' not in st.session_state:
            st.session_state.company_additional_selection_criteria = COMPANY_ADDITIONAL_SELECTION_CRITERIA.copy()
            
        for i, company in enumerate(selected_companies, 1):
            st.markdown(f"**{i}. {company}**")
            
            # 1단계 제외 기준 (세션 상태에서 가져오기)
            exclusion_criteria_text = st.session_state.company_additional_exclusion_criteria.get(company, "")
            if exclusion_criteria_text.strip():
                st.markdown("📝 **제외 특화 기준:**")
                st.text(exclusion_criteria_text[:100] + "..." if len(exclusion_criteria_text) > 100 else exclusion_criteria_text)
            
            # 2단계 그룹핑 기준 (세션 상태에서 가져오기)
            duplicate_criteria_text = st.session_state.company_additional_duplicate_handling.get(company, "")
            if duplicate_criteria_text.strip():
                st.markdown("🔄 **그룹핑 특화 기준:**")
                st.text(duplicate_criteria_text[:100] + "..." if len(duplicate_criteria_text) > 100 else duplicate_criteria_text)
            
            # 3단계 선택 기준 (세션 상태에서 가져오기)
            selection_criteria_text = st.session_state.company_additional_selection_criteria.get(company, "")
            if selection_criteria_text.strip():
                st.markdown("✅ **선택 특화 기준:**")
                st.text(selection_criteria_text[:100] + "..." if len(selection_criteria_text) > 100 else selection_criteria_text)
            
            if not (exclusion_criteria_text.strip() or duplicate_criteria_text.strip() or selection_criteria_text.strip()):
                st.info("설정된 특화 기준이 없습니다.")
            
            st.markdown("---")
    else:
        st.info("먼저 분석할 기업을 선택해주세요.")

# 구분선 추가
st.sidebar.markdown("---")

# GPT 모델 선택 섹션
st.sidebar.markdown("### 🤖 GPT 모델 선택")

selected_model = st.sidebar.selectbox(
    "분석에 사용할 GPT 모델을 선택하세요",
    options=list(GPT_MODELS.keys()),
    index=list(GPT_MODELS.keys()).index(DEFAULT_GPT_MODEL) if DEFAULT_GPT_MODEL in GPT_MODELS else 0,
    format_func=lambda x: f"{x} - {GPT_MODELS[x]}",
    help="각 모델의 특성:\n" + "\n".join([f"• {k}: {v}" for k, v in GPT_MODELS.items()])
)

# 모델 설명 표시
st.sidebar.markdown(f"""
<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
    <strong>선택된 모델:</strong> {selected_model}<br>
    <strong>특징:</strong> {GPT_MODELS[selected_model]}
</div>
""", unsafe_allow_html=True)

# 구분선 추가
st.sidebar.markdown("---")

# 검색 결과 수 - 키워드당 50개로 설정 (신뢰할 수 있는 언론사에서만)
max_results = 50

# AI 프롬프트 설정 (사용자 편집 가능)
st.sidebar.markdown("### 🤖 AI 프롬프트 설정")
st.sidebar.info("AI 분석에 사용되는 프롬프트는 config.py에서 관리됩니다.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 1단계: 제외 판단 기준")

# 제외 기준 설정 - 기본 기준만 표시하고 사용자 수정 허용
exclusion_criteria = st.sidebar.text_area(
    "❌ 제외 기준",
    value=EXCLUSION_CRITERIA,
    help="분석에서 제외할 뉴스의 기준을 설정하세요. 실제 분석 시 각 회사별 특화 기준이 추가로 적용됩니다.",
    key="exclusion_criteria",
    height=300
)


# 구분선 추가
st.sidebar.markdown("---")

# 2단계: 그룹핑 기준
st.sidebar.markdown("### 📋 2단계: 그룹핑 기준")

# 중복 처리 기준 설정 - 기본 기준만 표시하고 사용자 수정 허용
duplicate_handling = st.sidebar.text_area(
    "🔄 중복 처리 기준",
    value=DUPLICATE_HANDLING,
    help="중복된 뉴스를 처리하는 기준을 설정하세요. 실제 분석 시 각 회사별 특화 기준이 추가로 적용됩니다.",
    key="duplicate_handling",
    height=300
)

# 구분선 추가
st.sidebar.markdown("---")

# 3단계: 선택 기준
st.sidebar.markdown("### 📋 3단계: 선택 기준")

# 선택 기준 설정 - 기본 기준만 표시하고 사용자 수정 허용
selection_criteria = st.sidebar.text_area(
    "✅ 선택 기준",
    value=SELECTION_CRITERIA,
    help="뉴스 선택에 적용할 주요 기준들을 나열하세요. 실제 분석 시 각 회사별 특화 기준이 추가로 적용됩니다.",
    key="selection_criteria",
    height=300
)

# 응답 형식 설정
response_format = st.sidebar.text_area(
    "📝 응답 형식",
    value="""선택된 뉴스 인덱스: [1, 3, 5]와 같은 형식으로 알려주세요.

각 선택된 뉴스에 대해:
제목: (뉴스 제목)
언론사: (언론사명)
발행일: (발행일자)
선정 사유: (구체적인 선정 이유)
분석 키워드: (해당 기업 그룹의 주요 계열사들)

[제외된 주요 뉴스]
제외된 중요 뉴스들에 대해:
인덱스: (뉴스 인덱스)
제목: (뉴스 제목)
제외 사유: (구체적인 제외 이유)""",
    help="분석 결과의 출력 형식을 설정하세요.",
    key="response_format",
    height=200
)

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
{valid_press_dict}

[중복 처리 기준]
{duplicate_handling}
"""

# 메인 컨텐츠
if st.button("뉴스 분석 시작", type="primary"):
    # 뉴스 분석 서비스 초기화
    news_service = NewsAnalysisService()
    
    # 유효 언론사 설정을 딕셔너리로 파싱
    valid_press_config = parse_press_config(valid_press_dict)
    
    # 이메일 미리보기를 위한 전체 내용 저장
    email_content = "[Client Intelligence]\n\n"
    
    # 모든 키워드 분석 결과를 저장할 딕셔너리
    all_results = {}
    
    for i, company in enumerate(selected_companies, 1):
        with st.spinner(f"'{company}' 관련 뉴스를 수집하고 분석 중입니다..."):
            # 해당 회사의 연관 키워드 확장 (세션 상태에서 가져옴)
            company_keywords = st.session_state.company_keyword_map.get(company, [company])
            
            # 연관 키워드 표시
            st.write(f"'{company}' 연관 키워드로 검색 중: {', '.join(company_keywords)}")
            
            # 날짜/시간 객체 생성
            start_dt = datetime.combine(start_date, start_time)
            end_dt = datetime.combine(end_date, end_time)
            
            # 뉴스 분석 서비스 호출 (신뢰할 수 있는 언론사에서만 수집)
            try:
                analysis_result = news_service.analyze_news(
                    keywords=company_keywords,
                    start_date=start_dt,
                    end_date=end_dt,
                    companies=[company],
                    trusted_press=valid_press_config  # 신뢰할 수 있는 언론사 전달
                )
                
                # 결과 저장
                all_results[company] = analysis_result
                
                # 결과 표시
                st.success(f"'{company}' 분석 완료!")
                st.write(f"수집된 뉴스: {analysis_result['collected_count']}개")
                st.write(f"날짜 필터링 후: {analysis_result['date_filtered_count']}개")
                st.write(f"언론사 필터링 후: {analysis_result['press_filtered_count']}개")
                st.write(f"최종 선별: {len(analysis_result['final_selection'])}개")
                
                # 최종 선별된 뉴스 표시
                if analysis_result['final_selection']:
                    st.subheader(f"📰 {company} 최종 선별 뉴스")
                    for j, news in enumerate(analysis_result['final_selection'], 1):
                        with st.expander(f"{j}. {news.get('content', '제목 없음')}"):
                            st.write(f"**언론사:** {news.get('press', '알 수 없음')}")
                            st.write(f"**날짜:** {news.get('date', '날짜 정보 없음')}")
                            st.write(f"**URL:** {news.get('url', '')}")
                
            except Exception as e:
                st.error(f"'{company}' 분석 중 오류 발생: {str(e)}")
                continue
            
            
            # 분석 완료 후 결과 요약
            st.success(f"✅ {company} 분석 완료!")
            
            # 이메일 내용에 추가
            email_content += f"\n=== {company} 분석 결과 ===\n"
            email_content += f"수집된 뉴스: {analysis_result['collected_count']}개\n"
            email_content += f"날짜 필터링 후: {analysis_result['date_filtered_count']}개\n"
            email_content += f"언론사 필터링 후: {analysis_result['press_filtered_count']}개\n"
            email_content += f"최종 선별: {len(analysis_result['final_selection'])}개\n\n"
            
            # 보류 뉴스
            with st.expander("⚠️ 보류 뉴스"):
                for news in analysis_result["borderline_news"]:
                    st.markdown(f"<div class='excluded-news'>[{news['index']}] {news['title']}<br/>└ {news['reason']}</div>", unsafe_allow_html=True)
            
            # 유지 뉴스
            with st.expander("✅ 유지 뉴스"):
                for news in analysis_result["retained_news"]:
                    st.markdown(f"<div class='excluded-news'>[{news['index']}] {news['title']}<br/>└ {news['reason']}</div>", unsafe_allow_html=True)
            
            # 4단계: 그룹핑 결과 표시
            st.markdown("<div class='subtitle'>🔍 4단계: 뉴스 그룹핑 결과</div>", unsafe_allow_html=True)
            
            with st.expander("📋 그룹핑 결과 보기"):
                for group in analysis_result["grouped_news"]:
                    st.markdown(f"""
                    <div class="analysis-section">
                        <h4>그룹 {group['indices']}</h4>
                        <p>선택된 기사: {group['selected_index']}</p>
                        <p>선정 이유: {group['reason']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 5단계: 최종 선택 결과 표시
            st.markdown("<div class='subtitle'>🔍 5단계: 최종 선택 결과</div>", unsafe_allow_html=True)
            
            # 재평가 여부 확인 (is_reevaluated 필드 있으면 재평가된 것)
            was_reevaluated = analysis_result.get("is_reevaluated", False)
            
            # 재평가 여부에 따라 메시지와 스타일 변경
            if was_reevaluated:
                # 재평가가 수행된 경우 6단계 표시
                st.warning("5단계에서 선정된 뉴스가 없어 6단계 재평가를 진행했습니다.")
                st.markdown("<div class='subtitle'>🔍 6단계: 재평가 결과</div>", unsafe_allow_html=True)
                st.markdown("### 📰 재평가 후 선정된 뉴스")
                # 재평가 스타일 적용
                news_style = "border-left: 4px solid #FFA500; background-color: #FFF8DC;"
                reason_prefix = "<span style=\"color: #FFA500; font-weight: bold;\">재평가 후</span> 선별 이유: "
            else:
                # 정상적으로 5단계에서 선정된 경우
                st.markdown("### 📰 최종 선정된 뉴스")  
                # 일반 스타일 적용
                news_style = ""
                reason_prefix = "선별 이유: "
            
            # 최종 선정된 뉴스 표시
            for news in analysis_result["final_selection"]:
                # 날짜 형식 변환
                
                date_str = format_date(news.get('date', ''))
                
                try:
                    # YYYY-MM-DD 형식으로 가정
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%m/%d')
                except Exception as e:
                    try:
                        # GMT 형식 시도
                        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        formatted_date = date_obj.strftime('%m/%d')
                    except Exception as e:
                        formatted_date = date_str if date_str else '날짜 정보 없음'

                url = news.get('url', 'URL 정보 없음')
                press = news.get('press', '언론사 정보 없음')
                
                # 뉴스 정보 표시
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
                
                # 구분선 추가
                st.markdown("---")
            

            
            # 디버그 정보 (간소화)
            st.info("AI 분석이 완료되었습니다. 상세한 분석 과정은 로그에서 확인할 수 있습니다.")
            
            # 이메일 내용 추가
            email_content += f"{i}. {company}\n"
            for news in analysis_result["final_selection"]:
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
                email_content += f"  - {news['title']} ({formatted_date}) {url}\n"
            email_content += "\n"
            
            # 키워드 구분선 추가
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

    for i, company in enumerate(selected_companies, 1):
        # HTML 버전에서 키워드를 파란색으로 표시
        html_email_content += f"<div style='font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px; color: #0000FF;'>{i}. {company}</div>"
        html_email_content += "<ul style='list-style-type: none; padding-left: 20px; margin: 0;'>"
        
        # 텍스트 버전에서도 키워드 구분을 위해 줄바꿈 추가
        plain_email_content += f"{i}. {company}\n"
        
        # 해당 키워드의 뉴스 가져오기
        news_list = all_results.get(company, [])
        
        if not news_list:
            # 최종 선정 뉴스가 0건인 경우 안내 문구 추가
            html_email_content += "<li style='margin-bottom: 8px; font-size: 14px; color: #888;'>AI 분석결과 금일자로 회계법인 관점에서 특별히 주목할 만한 기사가 없습니다.</li>"
            plain_email_content += "  - AI 분석결과 금일자로 회계법인 관점에서 특별히 주목할 만한 기사가 없습니다.\n"
        else:
            for news in news_list:
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
st.markdown("© 2024 PwC 뉴스 분석기 | 회계법인 관점의 뉴스 분석 도구")
