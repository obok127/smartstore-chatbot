from urllib.parse import urlencode

BASE = "https://help.sell.smartstore.naver.com/faq/search.help"

def build_help_search_url(keyword: str, category_no: int = 0) -> str:
    """스마트스토어 도움말 검색 URL을 생성합니다."""
    # 안전 인코딩
    qs = urlencode({"categoryNo": str(category_no), "searchKeyword": keyword})
    return f"{BASE}?{qs}"
