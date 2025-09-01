#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
News Service
------------
뉴스 수집 및 분석을 담당하는 비즈니스 로직 레이어
UI와 분리되어 독립적으로 사용 가능
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import re
from googlenews import GoogleNews
from config import (
    TRUSTED_PRESS_ALIASES,
    ADDITIONAL_PRESS_ALIASES,
    EXCLUSION_CRITERIA,
    DUPLICATE_HANDLING,
    SELECTION_CRITERIA,
    COMPANY_ADDITIONAL_EXCLUSION_CRITERIA,
    COMPANY_ADDITIONAL_DUPLICATE_HANDLING,
    COMPANY_ADDITIONAL_SELECTION_CRITERIA,
    KEYWORD_CATEGORIES
)


class NewsService:
    """뉴스 수집 및 분석 서비스"""
    
    def __init__(self):
        self.google_news = GoogleNews()
    
    def collect_news_by_keywords(self, keywords: List[str], max_results: int = 200, 
                                trusted_press: Dict = None) -> List[Dict[str, Any]]:
        """
        키워드 리스트로 뉴스 수집 (OR 조건으로 한번에 검색 + AI 필터링)
        
        Args:
            keywords: 검색할 키워드 리스트
            max_results: 전체 키워드에서 최대 결과 수 (기본값: 200)
            trusted_press: 신뢰할 수 있는 언론사 목록 (AI 필터링용)
            
        Returns:
            필터링된 뉴스 리스트
        """
        # OR 조건으로 모든 키워드를 한번에 검색
        combined_query = " OR ".join(keywords)
        print(f"통합 검색 시작: {combined_query}")
        
        # 전체 언론사에서 한번에 검색 (빠름)
        all_news = self.google_news.search_all_press_unified(combined_query, max_results)
        print(f"전체 검색 결과: {len(all_news)}개")
        
        # AI로 유효 언론사 필터링
        if trusted_press:
            print("AI로 유효 언론사 필터링 시작...")
            filtered_news = self._filter_by_gpt_trusted_press(all_news, trusted_press)
            print(f"AI 필터링 완료: {len(filtered_news)}개 뉴스 유지")
            return filtered_news
        else:
            print("신뢰할 수 있는 언론사 목록이 없어 전체 결과 반환")
            return all_news

    def collect_news_by_categories_sequential(self, categories: List[str] = None, 
                                            max_per_category: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """
        카테고리별로 각 키워드를 개별 검색하여 각각 50개씩 수집 (GPT 분석용)
        
        Args:
            categories: 검색할 카테고리 리스트 (None이면 전체 카테고리)
            max_per_category: 각 키워드당 최대 뉴스 수 (기본값: 50)
            
        Returns:
            카테고리별 뉴스 리스트를 담은 딕셔너리
        """
        
        if categories is None:
            categories = list(KEYWORD_CATEGORIES.keys())
        
        all_category_news = {}
        
        for category in categories:
            if category not in KEYWORD_CATEGORIES:
                print(f"알 수 없는 카테고리: {category}")
                continue
                
            keywords = KEYWORD_CATEGORIES[category]
            print(f"\n=== {category} 카테고리 검색 시작 ===")
            print(f"키워드: {keywords}")
            
            category_news = []
            
            # 각 키워드를 개별적으로 검색 (OR 조건 아님)
            for keyword in keywords:
                print(f"  - '{keyword}' 키워드 검색 중...")
                
                # 개별 키워드로 검색
                keyword_news = self.google_news.search_all_press_unified(keyword, max_per_category)
                print(f"    '{keyword}' 검색 결과: {len(keyword_news)}개")
                
                # 각 뉴스에 키워드 정보 추가
                for news in keyword_news:
                    news_with_keyword = news.copy()
                    news_with_keyword['search_keyword'] = keyword
                    category_news.append(news_with_keyword)
            
            print(f"{category} 카테고리 수집 완료: {len(category_news)}개 (키워드별 개별 검색)")
            all_category_news[category] = category_news
        
        print(f"\n=== 전체 카테고리 검색 완료 ===")
        total_news = sum(len(news) for news in all_category_news.values())
        print(f"총 수집된 뉴스: {total_news}개")
        
        return all_category_news

    def filter_by_date_range(self, news_data: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        날짜 범위로 뉴스 필터링
        
        Args:
            news_data: 뉴스 데이터 리스트
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            필터링된 뉴스 리스트
        """
        filtered_news = []
        
        for news_item in news_data:
            news_date_str = news_item.get('date', '')
            if not news_date_str:
                # 날짜 정보가 없는 뉴스는 포함 (최신 뉴스일 가능성)
                filtered_news.append(news_item)
                continue
            
            news_date = self._parse_news_date(news_date_str)
            if news_date and start_date <= news_date <= end_date:
                filtered_news.append(news_item)
        
        return filtered_news
    
    def _parse_news_date(self, date_str: str) -> Optional[datetime]:
        """뉴스 날짜 문자열을 파싱"""
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %Z',      # GMT 형식
            '%a, %d %b %Y %H:%M:%S GMT',     # GMT 형식 (명시적)
            '%Y-%m-%d %H:%M:%S',             # YYYY-MM-DD HH:MM:SS
            '%Y-%m-%d',                      # YYYY-MM-DD
            '%Y년 %m월 %d일',                # 한국어 형식
            '%m/%d/%Y',                      # MM/DD/YYYY
            '%d/%m/%Y',                      # DD/MM/YYYY
            '%Y.%m.%d',                      # YYYY.MM.DD
            '%m.%d.%Y',                      # MM.DD.YYYY
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        
        return None
    
    def filter_by_trusted_press(self, news_data: List[Dict]) -> List[Dict]:
        """신뢰할 수 있는 언론사로 필터링"""
        trusted_press = set()
        
        # TRUSTED_PRESS_ALIASES에서 모든 언론사명 추출
        for press_name, aliases in TRUSTED_PRESS_ALIASES.items():
            trusted_press.update(aliases)
        
        # ADDITIONAL_PRESS_ALIASES에서도 추출
        for press_name, aliases in ADDITIONAL_PRESS_ALIASES.items():
            trusted_press.update(aliases)
        
        filtered_news = []
        for news_item in news_data:
            press = news_item.get('press', '').lower()
            if any(trusted_press_name.lower() in press for trusted_press_name in trusted_press):
                filtered_news.append(news_item)
        
        return filtered_news
    
    def get_enhanced_criteria(self, companies: List[str], criteria_type: str) -> str:
        """회사별 추가 기준을 적용한 기준 반환"""
        base_criteria = ""
        additional_criteria = ""
        
        if criteria_type == "exclusion":
            base_criteria = EXCLUSION_CRITERIA
            for company in companies:
                additional_criteria += COMPANY_ADDITIONAL_EXCLUSION_CRITERIA.get(company, "")
        elif criteria_type == "duplicate":
            base_criteria = DUPLICATE_HANDLING
            for company in companies:
                additional_criteria += COMPANY_ADDITIONAL_DUPLICATE_HANDLING.get(company, "")
        elif criteria_type == "selection":
            base_criteria = SELECTION_CRITERIA
            for company in companies:
                additional_criteria += COMPANY_ADDITIONAL_SELECTION_CRITERIA.get(company, "")
        
        return base_criteria + additional_criteria

    def _filter_by_gpt_trusted_press(self, news_list: List[Dict], trusted_press: Dict) -> List[Dict]:
        """
        GPT를 사용하여 신뢰할 수 있는 언론사의 뉴스만 필터링
        
        Args:
            news_list: 전체 뉴스 리스트
            trusted_press: 신뢰할 수 있는 언론사 목록
            
        Returns:
            필터링된 뉴스 리스트
        """
        # 신뢰할 수 있는 언론사명과 별칭들을 평면화
        trusted_press_names = set()
        for press_name, aliases in trusted_press.items():
            trusted_press_names.add(press_name)
            trusted_press_names.update(aliases)
        
        print(f"신뢰할 수 있는 언론사 수: {len(trusted_press_names)}")
        
        # 언론사명 매칭으로 필터링
        filtered_news = []
        for news in news_list:
            press_name = news.get('press', '').strip()
            
            # 정확한 매칭 또는 부분 매칭 확인
            is_trusted = False
            for trusted_name in trusted_press_names:
                if (trusted_name.lower() in press_name.lower() or 
                    press_name.lower() in trusted_name.lower()):
                    is_trusted = True
                    break
            
            if is_trusted:
                filtered_news.append(news)
        
        return filtered_news


class NewsAnalysisService:
    """뉴스 AI 분석 서비스"""
    
    def __init__(self):
        self.news_service = NewsService()
    
    def analyze_news(self, keywords: List[str], start_date: datetime, end_date: datetime, 
                    companies: List[str] = None, trusted_press: Dict = None) -> Dict[str, Any]:
        """
        뉴스 수집부터 AI 분석까지 전체 프로세스 실행 (카테고리별 순차 검색)
        
        Args:
            keywords: 검색할 키워드 리스트 (사용하지 않음, 카테고리 기반으로 변경)
            start_date: 시작 날짜
            end_date: 종료 날짜
            companies: 회사 목록 (추가 기준 적용용)
            trusted_press: 신뢰할 수 있는 언론사 목록
            
        Returns:
            분석 결과 딕셔너리
        """
        # 1. 카테고리별로 순차 검색 (각 카테고리당 50개씩)
        print("=== 카테고리별 순차 검색 시작 ===")
        category_news = self.news_service.collect_news_by_categories_sequential(
            max_per_category=50
        )
        
        # 2. 모든 카테고리의 뉴스를 하나의 리스트로 통합
        all_collected_news = []
        for category, news_list in category_news.items():
            for news in news_list:
                news_with_category = news.copy()
                news_with_category['category'] = category
                all_collected_news.append(news_with_category)
        
        print(f"통합된 뉴스 수: {len(all_collected_news)}개")
        
        # 3. 날짜 필터링
        print("=== 날짜 필터링 시작 ===")
        date_filtered_news = self.news_service.filter_by_date_range(
            all_collected_news, start_date, end_date
        )
        
        # 4. 신뢰할 수 있는 언론사 필터링
        print("=== 언론사 필터링 시작 ===")
        if trusted_press:
            press_filtered_news = self.news_service._filter_by_gpt_trusted_press(
                date_filtered_news, trusted_press
            )
        else:
            press_filtered_news = date_filtered_news
        
        # 5. AI 분석
        print("=== AI 분석 시작 ===")
        analysis_result = self._perform_basic_analysis(press_filtered_news, companies)
        
        return {
            "collected_count": len(all_collected_news),
            "date_filtered_count": len(date_filtered_news),
            "press_filtered_count": len(press_filtered_news),
            "final_selection": analysis_result,
            "raw_news": press_filtered_news,
            "category_news": category_news,  # 카테고리별 뉴스 추가
            "borderline_news": [],
            "retained_news": [],
            "grouped_news": [],
            "is_reevaluated": False
        }
    
    def _perform_basic_analysis(self, news_data: List[Dict], companies: List[str] = None) -> List[Dict]:
        """기본적인 뉴스 분석 수행 (실제 AI 분석은 별도 구현 필요)"""
        # 여기서는 간단한 필터링만 수행
        # 실제로는 OpenAI API 등을 사용한 AI 분석이 필요
        
        if not companies:
            companies = []
        
        # 제외 기준 적용
        exclusion_criteria = self.news_service.get_enhanced_criteria(companies, "exclusion")
        
        # 간단한 키워드 기반 필터링 (실제로는 AI가 판단해야 함)
        filtered_news = []
        for i, news in enumerate(news_data):
            title = news.get('content', '').lower()
            
            # 제외 키워드 체크
            exclude_keywords = ['야구단', '축구단', '구단', 'KBO', '프로야구', '감독', '선수',
                              '출시', '기부', '환경 캠페인', '브랜드 홍보', '사회공헌', '나눔',
                              '일시 중단', '접속 오류', '서비스 오류', '버그', '점검 중',
                              '우수성 입증', '기술력 인정', '성능 비교', '품질 테스트',
                              '목표가', '목표주가']
            
            if not any(keyword in title for keyword in exclude_keywords):
                # 뉴스에 인덱스와 추가 정보 추가
                news_copy = news.copy()
                news_copy['index'] = i + 1
                news_copy['title'] = news.get('content', '제목 없음')
                news_copy['keywords'] = companies if companies else []
                news_copy['affiliates'] = companies if companies else []
                news_copy['reason'] = "기본 필터링을 통과한 뉴스"
                filtered_news.append(news_copy)
        
        return filtered_news[:10]  # 최대 10개 반환
