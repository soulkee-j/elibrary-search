import streamlit as st
import requests
import pandas as pd
from lxml import html
import re
from urllib.parse import quote

# 1. 페이지 설정
st.set_page_config(page_title="전자도서관 통합검색", page_icon="📚", layout="centered")

# 2. 보안 설정 (서울도서관 API 키)
SEOUL_API_KEY = st.secrets.get("seoul_api_key")

# 3. 서초구 CSV 데이터 로드 함수 (캐싱 적용)
@st.cache_data(ttl=3600)  # 1시간 동안 메모리에 유지
def get_seocho_data():
    url = "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003242287&fileDetailSn=1&dataNm=%EC%84%9C%EC%9A%B8%ED%8A%B9%EB%B3%84%EC%8B%9C%20%EC%84%9C%EC%B4%88%EA%B5%AC_%EC%A0%84%EC%9E%90%EB%8F%84%EC%84%9C%EA%B4%80%20%EB%8F%84%EC%84%9C%EC%A0%95%EB%B3%B4_20250909"
    try:
        # EUC-KR 인코딩으로 데이터 로드
        df = pd.read_csv(url, encoding='euc-kr')
        # '형식' 컬럼에서 '전자책'이 포함된 행만 필터링
        df_ebook = df[df['형식'].str.contains("전자책", na=False)].copy()
        return df_ebook
    except:
        return None

# 4. 도서관 데이터 정의
libraries = [
    {"name": "성남시", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "경기대", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "용인시", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "수원시", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "고양시", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "강남구", "url": "https://ebook.gangnam.go.kr/elibbook/book_search_result.asp", "key_param": "sarg1", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"},
    {"name": "서울도서관", "url": "http://openapi.seoul.go.kr:8088/", "encoding": "utf-8", "type": "seoul_api"},
    {"name": "서초구", "type": "seocho_csv"}
]

def search_libraries(book_name):
    results = []
    progress_bar = st.progress(0)
    total = len(libraries)

    for i, lib in enumerate(libraries):
        progress_bar.progress((i + 1) / total)
        try:
            # --- 1. 서초구 CSV 검색 로직 ---
            if lib["type"] == "seocho_csv":
                df_seocho = get_seocho_data()
                count = 0
                if df_seocho is not None:
                    mask = (df_seocho['도서명'].str.contains(book_name, na=False, case=False)) | \
                           (df_seocho['저자명'].str.contains(book_name, na=False, case=False))
                    # 도서명, 저자명 기준으로 중복 제거 후 카운트
                    count = len(df_seocho[mask].drop_duplicates(subset=['도서명', '저자명']))
                
                display = f"{count}권" if count > 0 else "없음"
                link = f"https://e-book.seocholib.or.kr/search?keyword={quote(book_name)}"
                results.append({"name": lib['name'], "link": link, "status": display})

            # --- 2. 서울도서관 API 로직 ---
            elif lib["type"] == "seoul_api":
                if not SEOUL_API_KEY:
                    results.append({"name": lib['name'], "link": "#", "status": "키 설정 필요"})
                    continue
                
                unique_books = {}
                encoded_query = quote(book_name)
                search_urls = [
                    f"{lib['url']}{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/500/{encoded_query}/%20/%20/%20/%20",
                    f"{lib['url']}{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/500/%20/{encoded_query}/%20/%20/%20"
                ]
                
                for url in search_urls:
                    resp = requests.get(url, timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        if "SeoulLibraryBookSearchInfo" in data:
                            rows = data["SeoulLibraryBookSearchInfo"].get("row", [])
                            for book in rows:
                                if book.get("BIB_TYPE_NAME") == "전자책":
                                    ctrl_no = book.get("CTRLNO")
                                    if ctrl_no: unique_books[ctrl_no] = book
                
                count = len(unique_books)
                display = f"{count}권" if count > 0 else "없음"
                link = f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={encoded_query}"
                results.append({"name": lib['name'], "link": link, "status": display})

            # --- 3. 강남구 및 기타 도서관 스크래핑 로직 ---
            else:
                encoded_query = quote(book_name.encode(lib["encoding"]))
                if lib["type"] == "gangnam":
                    search_url = f"{lib['url']}?scon1=TITLE&sarg1={encoded_query}&sopr2=OR&scon2=AUTHOR&sarg2={encoded_query}"
                else:
                    search_url = f"{lib['url']}?{lib['key_param']}={encoded_query}&schClst=ctts%2Cautr&schDvsn=001"
                
                resp = requests.get(search_url, timeout=10)
                count = 0
                if resp.status_code == 200:
                    tree = html.fromstring(resp.content)
                    nodes = tree.xpath(lib["xpath"])
                    if nodes:
                        count_match = re.findall(r'\d+', "".join(nodes))
                        count = int(count_match[0]) if count_match else 0
                
                display = f"{count}권" if count > 0 else "없음"
                results.append({"name": lib['name'], "link": search_url, "status": display})

        except:
            results.append({"name": lib['name'], "link": "#", "status": "확인불가"})

    # 하단 직접 확인 링크
    encoded_utf8 = quote(book_name)
    results.append({"name": " ", "link": None, "status": ""})
    results.append({"name": "부천시", "link": f"https://ebook.bcl.go.kr:444/elibrary-front/search/searchList.ink?schTxt={encoded_utf8}&schClst=ctts%2Cautr&schDvsn=001", "status": "링크 확인"})
    
    progress_bar.empty()
    return results

# --- 화면 구성 ---
st.markdown('<h2 style="font-size:24px; margin-top:-50px; margin-bottom:10px;">📚 전자도서관 통합검색</h2>', unsafe_allow_html=True)
keyword = st.text_input("책 제목을 입력하세요", placeholder="예: 행복의 조건", key="search_input")

if keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        data = search_libraries(keyword)
        
        html_code = f"""
        <div style="font-family: sans-serif;">
            <table style="width:100%; border-collapse: collapse; table-layout: fixed;">
                <thead>
                    <tr style="border-bottom: 2px solid #ddd; background-color: #f8f9fa;">
                        <th style="text-align:left; padding: 12px; width: 60%;">도서관 이름</th>
                        <th style="text-align:right; padding: 12px; width: 40%;">소장 현황</th>
                    </tr>
                </thead>
                <tbody>
        """
        for item in data:
            if item['link'] is None:
                html_code += """<tr style="background-color: #f1f3f5;"><td colspan="2" style="padding: 8px; text-align: center; font-size: 12px; color: #666;">기타 도서관 바로가기</td></tr>"""
            else:
                html_code += f"""
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 12px; font-weight: bold; color: #333;">{item['name']}</td>
                        <td style="padding: 12px; text-align: right;">
                            <a href="{item['link']}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold;">{item['status']}</a>
                        </td>
                    </tr>
                """
        html_code += "</tbody></table></div>"
        st.components.v1.html(html_code, height=len(data) * 52 + 60, scrolling=False)
