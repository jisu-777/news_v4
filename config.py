#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shared Configuration
-------------------
This file contains shared variables and configurations used across the news clipping application.
Centralizing these variables makes maintenance easier and ensures consistency.
"""

import os

# 네이버 뉴스 API 설정 (환경변수에서 가져옴)
NAVER_API_SETTINGS = {
    "client_id": os.getenv('NAVER_CLIENT_ID', ''),  # 환경변수에서 Client ID
    "client_secret": os.getenv('NAVER_CLIENT_SECRET', ''),  # 환경변수에서 Client Secret
    "base_url": "https://openapi.naver.com/v1/search/news.json",
    "max_results_per_keyword": 50,  # 키워드당 최대 검색 결과 수
    "sort": "date"  # 정렬 방식: date(최신순), sim(정확도순)
}

# 키워드 카테고리 정의 (UI에서는 카테고리만 표시, 키워드는 AI 분석 시에만 사용)
KEYWORD_CATEGORIES = {
    "삼일PwC": ["삼일PWC", "삼일회계법인", "삼일", "PWC"],
    "회계업계_일반": ["IFRS", "회계기준", "회계감독", "금감원", "금융감독원", "회계법인", "외부감사", "지정감사", "공인회계사"],
    "주요기업": ["삼성", "SK", "현대차", "LG", "포스코", "롯데", "현대모비스"],
    "산업동향": ["반도체", "배터리", "자동차", "철강", "석유화학", "조선", "건설", "바이오", "방산", "디스플레이", "AI", "에너지", "실적", "영업이익", "흑자", "적자", "투자", "수출", "수입", "구조조정", "폐업", "증설", "공장", "생산", "위기", "불황", "회복", "호황", "성장", "경쟁력", "추격", "역전", "도태", "생존", "관세", "보조금", "규제", "지원", "과징금", "IRA", "탄소", "ESG", "인허가", "R&D", "특허", "임상", "신약", "차세대", "친환경", "전기차", "수소", "원전", "재생에너지"],
    "경쟁사": ["한영EY", "삼정KPMG", "Deloitte", "안진회계법인", "한영회계법인", "삼정회계법인"],
    "M&A": ["M&A", "IPO", "상장", "인수", "매각", "합병", "분할"],
    "경제": ["경제", "금리", "환율", "물가", "GDP", "인플레이션", "경기"],
    "인사동정": ["CEO", "CFO", "임원", "승진", "취임", "사임", "인사"],
    "금융": ["금융", "보험", "증권", "카드", "캐피탈", "금융지주", "금융정책", "은행", "은행장", "한국은행", "산업은행", "국책은행", "저축은행", "증권", "PF", "카드사", "보험사", "보험업계"],
    "세제정책": ["법인세", "소득세", "상속세", "증여세", "디지털세", "세법", "조세", "세제", "과세", "세무조사", "세무진단", "세금", "가업승계", "세제정책"],
}

# AI 분석 프롬프트는 app.py에서 직접 정의 (자유 텍스트 응답 방식)

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

 
