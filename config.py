#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shared Configuration
-------------------
This file contains shared variables and configurations used across the news clipping application.
Centralizing these variables makes maintenance easier and ensures consistency.
"""

# Company categories and definitions
COMPANY_CATEGORIES = {
    "Anchor": [
        "주요기업", "산업동향", "경쟁사", "전문영역", "삼일 및 PwC 관련"
    ]
}

# 키워드 카테고리 정의 (간소화된 버전)
KEYWORD_CATEGORIES = {
    "삼일PwC": ["삼일PwC", "삼일회계법인", "PwC코리아"],
    "회계업계_일반": ["회계법인", "외부감사", "공인회계사"],
    "주요기업": ["삼성", "SK", "현대차", "LG", "포스코", "롯데"],
    "산업동향": ["반도체", "배터리", "자동차", "조선", "바이오", "AI"],
    "경쟁사": ["한영EY", "삼정KPMG", "Deloitte"],
    "M&A": ["M&A", "IPO", "상장", "인수", "매각"],
    "경제": ["경제", "금리", "환율", "물가", "GDP"],
    "인사동정": ["CEO", "CFO", "임원", "승진", "취임"],
    "금융": ["은행", "증권", "보험", "카드", "금융지주"],
    "세제정책": ["법인세", "소득세", "상속세", "세무조사"],
}

# 그룹과 회사 연결 매핑 (사용하지 않음 - KEYWORD_CATEGORIES로 대체됨)
# COMPANY_GROUP_MAPPING = {
#     "주요기업": ["삼성", "SK", "현대차", "LG", "포스코", "롯데", "한화", "카카오", "네이버"],
#     "산업동향": ["반도체", "배터리", "자동차", "철강", "석유화학", "조선", "건설", "바이오", "방산", "디스플레이", "AI", "에너지"],
#     "경쟁사": ["한영EY", "삼정KPMG", "Deloitte"],
#     "전문영역": ["M&A", "경제", "인사동정", "금융", "세제정책"],
#     "삼일 및 PwC 관련": ["삼일 및 PwC 관련"]
# }

# 카테고리별 활성화 설정
ACTIVE_CATEGORIES = {
    "Anchor": True,
    "Growth": False,
    "Whitespace": False
}

# Default to Test companies for testing
DEFAULT_COMPANIES = COMPANY_CATEGORIES["Anchor"]  # 테스트용으로 변경

# Company keyword map (사용하지 않음 - KEYWORD_CATEGORIES로 대체됨)
# COMPANY_KEYWORD_MAP = {
#     # 주요기업 그룹 - 각 기업별 맞춤 키워드
#     "삼성": ["영업이익", "매출", "실적", "순이익", "적자", "흑자", "투자", "인수", "합병", "M&A", "매각", "분사", "구조조정", "감원", "공장", "신규사업", "증설", "폐쇄", "CEO", "경영진", "주주총회", "배당", "자사주"],
#     "SK": ["영업이익", "매출", "실적", "순이익", "적자", "흑자", "투자", "인수", "합병", "M&A", "매각", "분사", "구조조정", "감원", "공장", "신규사업", "증설", "폐쇄", "CEO", "경영진", "주주총회", "배당", "자사주"],
#     # ... (기타 회사별 키워드들)
# }

# Trusted press aliases
TRUSTED_PRESS_ALIASES = {
    "조선일보": ["조선일보", "chosun", "chosun.com"],
    "중앙일보": ["중앙일보", "joongang", "joongang.co.kr", "joins.com"],
    "동아일보": ["동아일보", "donga", "donga.com"],
    "조선비즈": ["조선비즈", "chosunbiz", "biz.chosun.com"],
    "매거진한경": ["매거진한경", "magazine.hankyung", "magazine.hankyung.com"],
    "한국경제": ["한국경제", "한경", "hankyung", "hankyung.com", "한경닷컴"],
    "매일경제": ["매일경제", "매경", "mk", "mk.co.kr"],
    "연합뉴스": ["연합뉴스", "yna", "yna.co.kr"],
    "파이낸셜뉴스": ["파이낸셜뉴스", "fnnews", "fnnews.com"],
    "데일리팜": ["데일리팜", "dailypharm", "dailypharm.com"],
    "IT조선": ["it조선", "it.chosun.com", "itchosun"],
    "머니투데이": ["머니투데이", "mt", "mt.co.kr"],
    "비즈니스포스트": ["비즈니스포스트", "businesspost", "businesspost.co.kr"],
    "이데일리": ["이데일리", "edaily", "edaily.co.kr"],
    "아시아경제": ["아시아경제", "asiae", "asiae.co.kr"],
    "뉴스핌": ["뉴스핌", "newspim", "newspim.com"],
    "뉴시스": ["뉴시스", "newsis", "newsis.com"],
    "헤럴드경제": ["헤럴드경제", "herald", "heraldcorp", "heraldcorp.com"]
}

# Additional press aliases for re-evaluation
ADDITIONAL_PRESS_ALIASES = {
    "철강금속신문": ["철강금속신문", "snmnews", "snmnews.com"],
    "에너지신문": ["에너지신문", "energy-news", "energy-news.co.kr"],
    "이코노믹데일리": ["이코노믹데일리", "economidaily", "economidaily.com"]
}

# GPT 모델 설정
GPT_MODELS = {
    "GPT-4": "gpt-4",
    "GPT-4 Turbo": "gpt-4-turbo-preview",
    "GPT-3.5 Turbo": "gpt-3.5-turbo"
}

# 기본 GPT 모델
DEFAULT_GPT_MODEL = "GPT-4"

# System prompts
SYSTEM_PROMPT_1 = """당신은 뉴스 분석 전문가입니다. 뉴스의 중요성을 판단하여 제외/보류/유지로 분류하는 작업을 수행합니다. 

[기본 원칙]
- **포함 우선**: 애매한 경우에는 포함하는 방향으로 판단
- **유연한 기준**: 너무 엄격하게 제외하지 말고, 비즈니스 관점에서 유용한 정보라면 포함
- **컨텍스트 고려**: 기사의 전체 맥락을 보고 판단

[포함되어야 하는 기사 (Y)]
1. **삼일PwC 관련** (최우선)
   - 삼일PwC가 기사 주제이거나 주요 역할을 담당
   - 삼일PwC의 활동, 성과, 인사, 조직 변화
   - 삼일PwC가 언급된 모든 기사 (단순 언급도 포함)

2. **비즈니스 중요도**
   - 기업의 실적, 매출, 영업이익, 투자, M&A
   - 산업 동향, 정책 변화, 시장 변화
   - 경영진 인사, 조직 개편, 신사업 진출
   - 경쟁사 동향, 시장 점유율 변화

3. **경제적 영향**
   - 주가 변동 (특별한 사건이 있는 경우)
   - 투자 관련 (기업 투자, 정부 정책 등)
   - 무역, 환율, 금리 등 경제 지표

[제외되어야 하는 기사 (N)]
1. **명확한 제외 사항만**
   - 순수 스포츠 관련 (야구단, 축구단 등)
   - 개인 일상, 연예, 문화 관련
   - 단순 기술 성능 홍보 (성능 비교, 테스트 결과 등)
   - 광고성 콘텐츠

2. **애매한 경우**
   - **포함하는 방향으로 판단**
   - 비즈니스 관점에서 유용할 수 있는 정보라면 포함

[판단 기준]
- **포함 (Y)**: 삼일PwC 관련, 비즈니스 중요도 높음, 경제적 영향 있음
- **보류**: 애매하거나 추가 정보 필요
- **제외 (N)**: 명확히 관련 없는 경우만

**중요**: 너무 엄격하게 제외하지 말고, 비즈니스 관점에서 유용할 수 있는 정보라면 포함하는 방향으로 판단하세요."""



SYSTEM_PROMPT_2 = """당신은 뉴스 분석 전문가입니다. 유사한 뉴스를 그룹화하고 대표성을 갖춘 기사를 선택하는 작업을 수행합니다. 같은 사안에 대해 숫자, 기업 ,계열사, 맥락, 주요 키워드 등이 유사하면 중복으로 판단합니다. 언론사의 신뢰도와 기사의 상세도를 고려하여 대표 기사를 선정합니다."""

SYSTEM_PROMPT_3 = """당신은 뉴스 분석 전문가입니다. 뉴스의 중요도를 평가하고 최종 선정하는 작업을 수행합니다.

[선별 원칙]
- **포함 우선**: 애매한 경우에는 포함하는 방향으로 판단
- **비즈니스 관점**: 회계법인뿐만 아니라 일반적인 비즈니스 관점에서도 유용한 정보 포함
- **유연한 기준**: 너무 엄격하게 선별하지 말고, 다양한 관점의 유용한 정보 포함

[중요도 평가 기준]
- **상**: 삼일PwC 관련, 재무/실적, 회계/감사, M&A, 주요 계약, 법적 분쟁
- **중**: 산업 동향, 정책 변화, 경영진 인사, 조직 개편, 신사업 진출, 경쟁사 동향

[선별 개수]
- 최대 5개 기사 선별
- 애매한 경우 더 많이 포함해도 됨
- 각 뉴스의 핵심 키워드와 관련 계열사도 식별

**중요**: 너무 엄격하게 선별하지 말고, 비즈니스 관점에서 유용할 수 있는 정보라면 포함하는 방향으로 판단하세요."""

# Criteria definitions
EXCLUSION_CRITERIA = """다음 조건에 해당하는 뉴스만 제외하세요 (너무 엄격하게 제외하지 마세요):

1. **순수 스포츠 관련** (명확한 경우만)
   - 키워드: 야구단, 축구단, 구단, KBO, 프로야구, 감독, 선수
   - 단, 기업 스포츠팀의 경영 관련은 포함

2. **개인 일상/연예/문화** (명확한 경우만)
   - 개인 사생활, 연예인 소식, 문화 이벤트
   - 단, 기업 문화, ESG 활동은 포함

3. **단순 기술 성능 홍보** (명확한 경우만)
   - 키워드: 우수성 입증, 기술력 인정, 성능 비교, 품질 테스트
   - 단, 기술 혁신, 신기술 개발은 포함

4. **광고성 콘텐츠** (명확한 경우만)
   - 스폰서 콘텐츠, 기사형 보도자료
   - 단, 기업 보도자료는 포함

**중요**: 애매한 경우에는 제외하지 말고 포함하는 방향으로 판단하세요."""

DUPLICATE_HANDLING = """중복 뉴스가 존재할 경우 다음 우선순위로 1개만 선택하십시오:
1. 언론사 우선순위 (높은 순위부터)
   - 1순위: 경제 전문지 (한국경제, 매일경제, 조선비즈, 파이낸셜뉴스)
   - 2순위: 종합 일간지 (조선일보, 중앙일보, 동아일보)
   - 3순위: 통신사 (연합뉴스, 뉴스핌, 뉴시스)
   - 4순위: 기타 언론사

2. 발행 시간 (같은 언론사 내에서)
   - 최신 기사 우선
   - 정확한 시간 정보가 없는 경우, 날짜만 비교

3. 기사 내용의 완성도
   - 더 자세한 정보를 포함한 기사 우선
   - 주요 인용문이나 전문가 의견이 포함된 기사 우선
   - 단순 보도보다 분석적 내용이 포함된 기사 우선

4. 제목의 명확성
   - 더 구체적이고 명확한 제목의 기사 우선
   - 핵심 키워드가 포함된 제목 우선"""

SELECTION_CRITERIA = """다음 기준에 해당하는 뉴스가 있다면 반드시 선택해야 합니다:

1. **삼일PwC 관련** (최우선 순위)
   - 삼일PwC가 언급된 모든 기사
   - 삼일PwC의 활동, 성과, 인사, 조직 변화
   - 삼일PwC가 참여한 프로젝트, 컨소시엄

2. **재무/실적 관련 정보** (높은 우선순위)
   - 매출, 영업이익, 순이익 등 실적 발표
   - 재무제표 관련 정보
   - 배당 정책 변경
   - 투자 계획, 자본금 변동

3. **회계/감사 관련 정보** (높은 우선순위)
   - 회계처리 방식 변경
   - 감사의견 관련 내용
   - 내부회계관리제도
   - 회계 감리 결과
   - 회계법인 관련 소식
   
4. **비즈니스 중요도** (높은 우선순위)
   - 신규사업/투자/계약에 대한 내용
   - 대외 전략(정부 정책, 글로벌 파트너, 지정학 리스크 등)
   - 기업의 새로운 사업전략 및 방향성, 신사업 등
   - 기업의 전략 방향성에 영향을 미칠 수 있는 정보
   - 기존 수입모델/사업구조/고객구조 변화
   - 공급망/수요망 등 valuechain 관련 내용

5. **기업구조 변경 정보** (높은 우선순위)
   - 인수합병(M&A)
   - 자회사 설립/매각
   - 지분 변동
   - 조직 개편
   - 경영진 인사

6. **산업 동향** (중간 우선순위)
   - 주요 산업의 변화, 정책, 규제
   - 시장 점유율 변화
   - 경쟁사 동향
   - 기술 혁신, 신기술 개발

**중요**: 너무 엄격하게 선별하지 말고, 비즈니스 관점에서 유용할 수 있는 정보라면 포함하는 방향으로 판단하세요."""

# GPT Model options (업데이트된 버전)
GPT_MODELS = {
    #"openai.gpt-4.1-2025-04-14" : "chatpwc",#pwc
    "gpt-4.1": "최신모델",
    "gpt-4o": "빠르고 실시간, 멀티모달 지원",
    "gpt-4-turbo": "최고 성능, 비용은 좀 있음",
    "gpt-4.1-mini": "성능 높고 비용 저렴, 정밀한 분류·요약에 유리",
    "gpt-4.1-nano": "초고속·초저가, 단순 태그 분류에 적합",
    "gpt-3.5-turbo": "아주 저렴, 간단한 분류 작업에 적당"
}

# Default GPT model to use
DEFAULT_GPT_MODEL = "gpt-4.1"

# 기본 뉴스 수집 개수
DEFAULT_NEWS_COUNT = 100 

# Email settings
EMAIL_SETTINGS = {
    "from": "kr_client_and_market@pwc.com", #from #kr_client_and_market@pwc.com"
    "default_to": "youngin.kang@pwc.com",
    "default_cc": "youngin.kang@pwc.com",
    "default_bcc": "",  # 기본 bcc 설정
    "default_subject": "Client Intelligence",
    "importance": "Normal"
}

# 카테고리별 이메일 설정
EMAIL_SETTINGS_BY_CATEGORY = {
    "Anchor": {
        "to": "youngin.kang@pwc.com",  # Anchor 카테고리 수신자
        "cc": "youngin.kang@pwc.com",  # Anchor 카테고리 참조
        "bcc": "youngin.kang@pwc.com",  # Anchor 카테고리 숨은 참조
        "subject_prefix": "Anchor"
    },
    "Growth": {
        "to": "youngin.kang@pwc.com",  # Growth 카테고리 수신자 (나중에 변경)
        "cc": "youngin.kang@pwc.com",  # Growth 카테고리 참조 (나중에 변경)
        "bcc": "",  # Growth 카테고리 숨은 참조
        "subject_prefix": "Growth"
    },
    "Whitespace": {
        "to": "youngin.kang@pwc.com",  # Whitespace 카테고리 수신자 (나중에 변경)
        "cc": "youngin.kang@pwc.com",  # Whitespace 카테고리 참조 (나중에 변경)
        "bcc": "",  # Whitespace 카테고리 숨은 참조
        "subject_prefix": "Whitespace"
    }
}

# Teams settings
TEAMS_SETTINGS = {
    "enabled": True,
    "title": "[PwC] 뉴스 분석 보고서",
    "subtitle": "AI가 선별한 오늘의 주요 뉴스",
    "use_plain_text": True  # False면 HTML 사용, True면 텍스트 사용
}

# Teams 채널별 설정 (카테고리별)
TEAMS_CHANNEL_SETTINGS = {
    "Anchor": {
        "groupId": "",  # Anchor 팀 그룹 ID
        "channels": {
            "삼일 및 PwC 관련": {
                "channelId": "",
                "parentMessageId": ""
            },
            "회계": {
                "channelId": "",
                "parentMessageId": ""
            },
            "세제·정책": {
                "channelId": "",
                "parentMessageId": ""
            },
            "주요 기업": {
                "channelId": "",
                "parentMessageId": ""
            },
            "산업 동향": {
                "channelId": "",
                "parentMessageId": ""
            },
            "금융": {
                "channelId": "",
                "parentMessageId": ""
            },
            "M&A 및 자본시장": {
                "channelId": "",
                "parentMessageId": ""
            },
            "경제": {
                "channelId": "",
                "parentMessageId": ""
            },
            "인사 동정": {
                "channelId": "",
                "parentMessageId": ""
            },
            "경쟁사": {
                "channelId": "",
                "parentMessageId": ""
            }
        }
    }
}

# SharePoint List 설정 (카테고리별 -> 회사별)
SHAREPOINT_LIST_SETTINGS = {
    "Anchor": {
        "enabled": True,
        "companies": {
             
     "삼일 및 PwC 관련": {
                "site_url": "",  # SharePoint 사이트 URL (예: https://company.sharepoint.com/sites/news)
                "list_id": "",   # SharePoint List ID
                "column_ids": {
                    "month": "",     # Month 컬럼 ID
                    "date": "",      # 날짜 컬럼 ID
                    "title": "",     # 제목 컬럼 ID
                    "link": ""       # 링크 컬럼 ID
                }
            },
            "회계": {
                "site_url": "https://pwckor.sharepoint.com/teams/KR-INT-xLoS-SK-GSP-/",
                "list_id": "ec97b948-d61e-47b7-9f1c-45bf62c46ec3",
                "column_ids": {
                    "month": "Month",
                    "date": "OData__xb0a0__xc9dc_",
                    "title": "Title",
                    "link": "OData__xb9c1__xd06c_"
                }
            },
            "세제·정책": {
                "site_url": "",
                "list_id": "",
                "column_ids": {
                    "month": "",
                    "date": "",
                    "title": "",
                    "link": ""
                }
            },
            "주요 기업": {
                "site_url": "",
                "list_id": "",
                "column_ids": {
                    "month": "",
                    "date": "",
                    "title": "",
                    "link": ""
                }
            },
            "산업 동향": {
                "site_url": "",
                "list_id": "",
                "column_ids": {
                    "month": "",
                    "date": "",
                    "title": "",
                    "link": ""
                }
            },
             "금융": {
                "site_url": "",
                "list_id": "",
                "column_ids": {
                    "month": "",
                    "date": "",
                    "title": "",
                    "link": ""
                }
            },
             "M&A 및 자본시장": {
                "site_url": "",
                "list_id": "",
                "column_ids": {
                    "month": "",
                    "date": "",
                    "title": "",
                    "link": ""
                }
            },
             "경제": {
                "site_url": "",
                "list_id": "",
                "column_ids": {
                    "month": "",
                    "date": "",
                    "title": "",
                    "link": ""
                }
            },
             "인사 동정": {
                "site_url": "",
                "list_id": "",
                "column_ids": {
                    "month": "",
                    "date": "",
                    "title": "",
                    "link": ""
                }
            },
             "경쟁사": {
                "site_url": "",
                "list_id": "",
                "column_ids": {
                    "month": "",
                    "date": "",
                    "title": "",
                    "link": ""
                }
            }
        }
    },
    
}

# API endpoint for email - 환경변수에서 가져옴
# EMAIL_API_ENDPOINT는 환경변수 EMAIL_API_ENDPOINT 또는 POWERAUTOMATE_WEBHOOK_URL에서 가져옵니다 

# Company-specific additional criteria for each AI stage
# 1단계: 제외 판단 추가 기준
COMPANY_ADDITIONAL_EXCLUSION_CRITERIA = {
    # "현대차": """
    
    # 6. 현대차그룹 특화 제외 기준 (추가):
    # 1) 노사 갈등 및 임단협 관련 보도
    # - 키워드: 현대차證""",
    #     "롯데": """
    
    # 6. 롯데그룹 특화 제외 기준 (추가):
    # - 키워드: 롯데카드, 롯데손보, 롯데손해보험"""
   
}

# 2단계: 그룹핑 추가 기준
COMPANY_ADDITIONAL_DUPLICATE_HANDLING = {
}

# 3단계: 선택 기준 추가
COMPANY_ADDITIONAL_SELECTION_CRITERIA = {
#     "CJ": """

# 5. CJ그룹(CJ제일제당, CJ대한통운, CJ ENM 등) 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 콘텐츠 전략: 콘텐츠 IP, OTT, 제작비, 콘텐츠 투자, 스튜디오드래곤, CJ ENM 전략
#    - 유통/물류 구조: 풀필먼트, 물류센터, 냉장물류, SCM, 글로벌 유통망, CJ대한통운
#    - 사업구조 변화: 인적분할, 물적분할, 계열 분할, 자회사 설립, 사업부 분리, 지분 매각""",

#     "NH": """

# 5. NH농협금융지주그룹(NH투자증권, NH농협은행 등) 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 금융 디지털화: 스마트팜 금융, 디지털전환, 플랫폼 전략, 모바일뱅킹, 금융앱, AI대출
#    - 농협 특수성: 조합원, 상호금융, 농민 금융, 지역 농협, 농업 지원 정책
#    - 계열 전략: NH투자증권, NH-Amundi, NH캐피탈, 계열사 구조, 지주 전략""",

#     "우리금융": """

# 5. 우리금융지주 (우리은행, 우리카드, 우리금융캐피탈 등) 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 지배구조 이슈: 예금보험공사, 공적자금, 지분 매각, 민영화, 최대주주, 지분 구조 변화
#    - 경영진 인사: 대표이사, 행장, 회장단, 연임, 경영진 교체, 이사회 구성
#    - PF/리스크 이슈: PF대출, 부동산 리스크, 부실채권, 충당금, 건전성, BIS비율""",

#     "HD현대": """

# 5. HD현대 (HD한국조선해양, HD현대중공업, HD현대오일뱅크 등) 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 무인화/자동화 전략: 스마트조선소, 자동용접, 무인운반, 디지털 조선, AI 기반 설계, 로봇공정
#    - 친환경/에너지 전환: 암모니아 추진선, 수소엔진, 친환경선박, 탄소중립, 그린수소, 해상풍력, 에너지저장장치(ESS)
#    - 글로벌 인프라 전략: 중동 플랜트, 오만 수주, 사우디 프로젝트, 글로벌 조선 수주, 선박 계약""",

#     "신한금융": """

# 5. 신한금융지주 (신한은행, 신한카드, 신한투자증권 등) 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 포트폴리오 재편: 비은행 강화, 카드·증권 통합, 신사업 진출, 핀테크 투자, 디지털 플랫폼화, 디지털 전환 전략
#    - 경영 인사 및 지배구조: 차기 회장, 행장 인선, 경영진 재편, 지주사 체제 개편, CEO 리스크, 내부통제 강화
#    - 리스크 대응: 금리 민감도, 충당금 적립, 부동산 익스포저""",

#     "신세계": """

# 5. 신세계그룹 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 리테일 전략: 복합몰 전략, 스타필드, 프리미엄 아울렛, 이마트 구조조정, 백화점 실적, 온라인 통합몰
#    - 사업구조 변화: 신세계인터내셔날, 지분 매각, 신사업 확장""",

#     "KDB금융": """

# 5. KDB금융지주 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 정책금융 역할: 정책금융, 구조조정 주도, 산업은행, 매각 자문, 국책은행 역할
#    - 기업 구조개편: 출자전환, PF 위험 평가, 기업 구조개편, 인수금융, 구조개편 지원""",

#     "GS": """

# 5. GS그룹 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 에너지 전환: GS에너지, RE100, LNG 인프라, 그린수소, 탄소 포집
#    - 리테일 혁신: GS리테일, 편의점 수익, 통합 물류
#    - 그룹 구조 개편: 계열사 재편, 미래 성장 포트폴리오""",

#     "LS": """

# 5. LS그룹 특화 기준 (위 기준 3, 4에 추가 해당)
#    해당 키워드가 포함되어 있을 경우에도 위 기준 3 또는 4에 해당하므로 반드시 선택합니다:
#    - 전력 인프라: 전선사업, 배터리 소재, 전력 인프라, ESS, LS일렉트릭 전략
#    - 친환경 소재: 동소재, 전기차 부품, 탄소저감 소재
#    - 사업구조 재편: LS엠트론, 계열 분할, 신성장 동력"""
} 

# 성능 최적화 설정 (개별 키워드 50개씩 수집 방식)
PERFORMANCE_SETTINGS = {
    "use_individual_keyword_search": True,  # 개별 키워드 검색 사용
    "max_news_per_keyword": 50,            # 각 키워드당 50개씩
    "timeout_seconds": 15,                  # HTTP 요청 타임아웃
    "enable_parallel_processing": False,    # 병렬 처리 사용 여부 (향후 구현)
    "cache_enabled": False,                 # 캐싱 사용 여부 (향후 구현)
    "search_method": "individual_keywords", # 개별 키워드 검색 방식
}

# 검색 전략 설정 (개별 키워드 50개씩)
SEARCH_STRATEGY = {
    "primary": "individual_keyword_search",  # 주요 검색 방식: 개별 키워드 검색
    "fallback": "none",                      # 대체 검색 방식: 없음
    "max_per_keyword": 50,                  # 각 키워드당 최대 50개
    "retry_count": 3,                        # 재시도 횟수
    "optimization": "keyword_by_keyword",    # 최적화: 키워드별 개별 검색
} 
