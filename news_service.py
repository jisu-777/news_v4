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
    COMPANY_ADDITIONAL_SELECTION_CRITERIA
)


class NewsService:
    """뉴스 수집 및 분석 서비스"""
    
    def __init__(self):
        self.google_news = GoogleNews()
    
    def collect_news_by_keywords(self, keywords: List[str], max_results: int = 50, 
                                trusted_press: Dict = None) -> List[Dict[str, Any]]:
        """
        키워드 리스트로 뉴스 수집 (신뢰할 수 있는 언론사에서만)
        
        Args:
            keywords: 검색할 키워드 리스트
            max_results: 각 키워드당 최대 결과 수 (기본값: 50)
            trusted_press: 신뢰할 수 있는 언론사 목록
            
        Returns:
            수집된 뉴스 리스트
        """
        all_news_data = []
        
        # 신뢰할 수 있는 언론사가 지정된 경우
        if trusted_press:
            print(f"신뢰할 수 있는 언론사에서만 뉴스 수집 시작: {len(trusted_press)}개 언론사")
            for keyword in keywords:
                print(f"키워드 '{keyword}' 검색 중... (신뢰할 수 있는 언론사에서만)")
                news_results = self.google_news.search_by_keyword(
                    keyword, 
                    k=max_results, 
                    trusted_press=trusted_press
                )
                all_news_data.extend(news_results)
                print(f"키워드 '{keyword}' 검색 결과: {len(news_results)}개")
        else:
            # 기존 로직: 전체 언론사에서 검색
            print("전체 언론사에서 뉴스 수집 시작")
            for keyword in keywords:
                print(f"키워드 '{keyword}' 검색 중...")
                news_results = self.google_news.search_by_keyword(keyword, k=max_results)
                all_news_data.extend(news_results)
                print(f"키워드 '{keyword}' 검색 결과: {len(news_results)}개")
        
        # 중복 URL 제거
        unique_urls = set()
        unique_news_data = []
        
        for news_item in all_news_data:
            url = news_item.get('url', '')
            if url and url not in unique_urls:
                unique_urls.add(url)
                unique_news_data.append(news_item)
        
        print(f"중복 제거 후 전체 뉴스 수: {len(unique_news_data)}개")
        return unique_news_data
    
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


class NewsAnalysisService:
    """뉴스 AI 분석 서비스"""
    
    def __init__(self):
        self.news_service = NewsService()
    
    def analyze_news(self, keywords: List[str], start_date: datetime, end_date: datetime, 
                    companies: List[str] = None, trusted_press: Dict = None) -> Dict[str, Any]:
        """
        뉴스 수집부터 AI 분석까지 전체 프로세스 실행
        
        Args:
            keywords: 검색 키워드
            start_date: 시작 날짜
            end_date: 종료 날짜
            companies: 회사 목록 (추가 기준 적용용)
            trusted_press: 신뢰할 수 있는 언론사 목록
            
        Returns:
            분석 결과 딕셔너리
        """
        # 1. 뉴스 수집 (신뢰할 수 있는 언론사에서만)
        print("=== 뉴스 수집 시작 ===")
        collected_news = self.news_service.collect_news_by_keywords(
            keywords, 
            max_results=50,  # 키워드당 50개로 제한
            trusted_press=trusted_press
        )
        
        # 2. 날짜 필터링
        print("=== 날짜 필터링 시작 ===")
        date_filtered_news = self.news_service.filter_by_date_range(
            collected_news, start_date, end_date
        )
        
        # 3. 신뢰할 수 있는 언론사 필터링 (이미 신뢰할 수 있는 언론사에서만 수집했으므로 생략 가능)
        print("=== 언론사 필터링 시작 ===")
        if trusted_press:
            # 이미 신뢰할 수 있는 언론사에서만 수집했으므로 필터링 생략
            print("신뢰할 수 있는 언론사에서만 수집했으므로 언론사 필터링 생략")
            press_filtered_news = date_filtered_news
        else:
            # 기존 로직: 전체 언론사에서 수집한 경우 필터링 수행
            press_filtered_news = self.news_service.filter_by_trusted_press(date_filtered_news)
        
        # 4. AI 분석 (여기서는 기본 필터링만 수행, 실제 AI 분석은 별도 구현 필요)
        print("=== AI 분석 시작 ===")
        analysis_result = self._perform_basic_analysis(press_filtered_news, companies)
        
        return {
            "collected_count": len(collected_news),
            "date_filtered_count": len(date_filtered_news),
            "press_filtered_count": len(press_filtered_news),
            "final_selection": analysis_result,
            "raw_news": press_filtered_news
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
        for news in news_data:
            title = news.get('content', '').lower()
            
            # 제외 키워드 체크
            exclude_keywords = ['야구단', '축구단', '구단', 'KBO', '프로야구', '감독', '선수',
                              '출시', '기부', '환경 캠페인', '브랜드 홍보', '사회공헌', '나눔',
                              '일시 중단', '접속 오류', '서비스 오류', '버그', '점검 중',
                              '우수성 입증', '기술력 인정', '성능 비교', '품질 테스트',
                              '목표가', '목표주가']
            
            if not any(keyword in title for keyword in exclude_keywords):
                filtered_news.append(news)
        
        return filtered_news[:10]  # 최대 10개 반환
