#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shared Configuration
-------------------
This file contains shared variables and configurations used across the news clipping application.
Centralizing these variables makes maintenance easier and ensures consistency.
"""

# 키워드 카테고리 정의 (UI에서는 카테고리만 표시, 키워드는 AI 분석 시에만 사용)
KEYWORD_CATEGORIES = {
    "삼일PwC": ["삼일PwC", "삼일회계법인", "PwC코리아", "삼일PwC코리아"],
    "회계업계_일반": ["회계법인", "외부감사", "공인회계사", "회계처리", "감사의견"],
    "주요기업": ["삼성", "SK", "현대차", "LG", "포스코", "롯데", "현대모비스"],
    "산업동향": ["반도체", "배터리", "자동차", "조선", "바이오", "AI", "신재생에너지"],
    "경쟁사": ["한영EY", "삼정KPMG", "Deloitte", "안진회계법인", "한일회계법인"],
    "M&A": ["M&A", "IPO", "상장", "인수", "매각", "합병", "분할"],
    "경제": ["경제", "금리", "환율", "물가", "GDP", "인플레이션", "경기"],
    "인사동정": ["CEO", "CFO", "임원", "승진", "취임", "사임", "인사"],
    "금융": ["은행", "증권", "보험", "카드", "금융지주", "금융권", "투자"],
    "세제정책": ["법인세", "소득세", "상속세", "세무조사", "세법개정", "조세정책"],
}

# AI 분석 프롬프트 (언론사 판별 포함)
AI_ANALYSIS_PROMPT = """당신은 회계법인 관점에서 뉴스를 분석하고 선별하는 전문가입니다.

[분석 기준]
1. **회계법인 관점의 중요도**
   - 삼일PwC 관련 뉴스 (최우선)
   - 재무/실적 정보 (매출, 영업이익, 순이익, 투자계획)
   - 회계/감사 관련 (회계처리 변경, 감사의견, 회계법인 소식)
   - 비즈니스 중요도 (신규사업, M&A, 조직변화, 경영진 인사)
   - 산업 동향 (정책, 규제, 시장 변화)

2. **언론사 신뢰도 판별**
   - **1순위**: 경제 전문지 (한국경제, 매일경제, 조선비즈, 파이낸셜뉴스, 이데일리)
   - **2순위**: 종합 일간지 (조선일보, 중앙일보, 동아일보, 한국일보)
   - **3순위**: 통신사 (연합뉴스, 뉴스1, 뉴시스)
   - **4순위**: 기타 언론사

3. **선별 원칙**
   - 최소 3개 뉴스는 반드시 포함
   - 애매한 경우 포함하는 방향으로 판단
   - 중복 뉴스는 언론사 우선순위와 발행시간 고려하여 1개만 선택

[제외 기준]
- 순수 스포츠 관련 (야구단, 축구단 등)
- 개인 일상, 연예, 문화 관련
- 단순 투자정보 제공
- 단순 기술 성능 홍보
- 광고성 콘텐츠

[응답 형식]
다음 JSON 형식으로 응답해주세요:

{
    "selected_news": [
        {
            "title": "뉴스 제목",
            "url": "뉴스 URL",
            "date": "날짜",
            "importance": "높음/보통/낮음",
            "press_analysis": "언론사 분석 및 신뢰도 평가",
            "selection_reason": "선별 이유 (회계법인 관점에서의 중요성)"
        }
    ],
    "total_analyzed": 총 분석 뉴스 수,
    "selected_count": 선별된 뉴스 수
}

**중요**: 
- 너무 엄격하게 선별하지 말고, 비즈니스 관점에서 유용할 수 있는 정보라면 포함하세요.
- 언론사 신뢰도를 고려하여 선별하되, 내용의 중요도가 더 우선시되어야 합니다."""

# GPT 모델 설정
GPT_MODELS = {
    "gpt-4o": "빠르고 실시간, 멀티모달 지원",
    "gpt-4-turbo": "최고 성능, 비용은 좀 있음",
    "gpt-4o-mini": "성능 높고 비용 저렴, 정밀한 분류·요약에 유리",
    "gpt-3.5-turbo": "아주 저렴, 간단한 분류 작업에 적당"
}

# 기본 GPT 모델
DEFAULT_GPT_MODEL = "gpt-4o-mini"

# 기본 뉴스 수집 개수 (키워드당)
DEFAULT_NEWS_COUNT_PER_KEYWORD = 50

# 이메일 설정 (간소화)
EMAIL_SETTINGS = {
    "from": "kr_client_and_market@pwc.com",
    "default_to": "youngin.kang@pwc.com",
    "default_cc": "youngin.kang@pwc.com",
    "default_subject": "Client Intelligence - 뉴스 분석 보고서"
}

# Teams 설정 (간소화)
TEAMS_SETTINGS = {
    "enabled": True,
    "title": "[PwC] 뉴스 분석 보고서",
    "subtitle": "AI가 선별한 오늘의 주요 뉴스"
}

# SharePoint 설정 (간소화)
SHAREPOINT_SETTINGS = {
    "enabled": False,  # 필요시 활성화
    "site_url": "",
    "list_id": ""
}

 
