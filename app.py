import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote

# 1. 페이지 설정
st.set_page_config(page_title="전자도서관 통합검색", page_icon="📚", layout="centered")

# 2. 보안 설정 (Secrets에서 API 키 가져오기)
SEOUL_API_KEY = st.secrets.get("seoul_api_key")

# 3. 도서관 데이터 정의
libraries = [
    {"name": "성남시", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "경기대", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "용인시", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "수원시", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "고양시", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "강남구", "url": "https://ebook.gangnam.go.kr/elibbook/book_search_result.asp", "key_param": "sarg1", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"},
    {"name": "서울도서관", "url": "http://openapi.seoul.go.kr:8088/", "encoding": "utf-8", "type": "seoul_api"}
]

def search_libraries(book_name):
    results = []
    progress_bar = st.progress(0)
    total = len(libraries)

    for i, lib in enumerate(libraries):
        progress_bar.progress((i + 1) / total)
        try:
            encoded_query = quote(book_name.encode(lib["encoding"]))
            
            # --- 서울도서관 API 전용 로직 (최종 수정본 반영) ---
            if lib["type"] == "seoul_api":
                if not SEOUL_API_KEY:
                    results.append({"name": lib['name'], "link": "#", "status": "키 설정 필요"})
                    continue
                
                unique_books = {}
                search_urls = [
                    f"{lib['url']}{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/500/{encoded_query}/%20/%20/%20/%20",
                    f"{lib['url']}{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/500/%20/{encoded_keyword}/%20/%20/%20"
                ]
                
                for url in search_urls:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        if "SeoulLibraryBookSearchInfo" in data:
                            rows = data["SeoulLibraryBookSearchInfo"].get("row", [])
                            for book in rows:
                                if book.get("BIB_TYPE_NAME") == "전자책":
                                    ctrl_no = book.get("CTRLNO")
                                    if ctrl_no:
                                        unique_books[ctrl_no] = book
                
                count = len(unique_books)
                display = f"{count}권" if count > 0 else "없음"
                web_link = f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={encoded_query}"
                results.append({"name": lib['name'], "link": web_link, "status": display})

            # --- 강남구 전용 로직 ---
            elif lib["type"] == "gangnam":
                search_url = (
                    f"{lib['url']}?scon1=TITLE&sarg1={encoded_query}"
                    f"&sopr2=OR&scon2=AUTHOR&sarg2={encoded_query}"
                )
                resp = requests.get(search_url, timeout=5)
                count = 0
                if resp.status_code == 200:
                    tree = html.fromstring(resp.content)
                    nodes = tree.xpath(lib["xpath"])
                    if nodes:
                        count_match = re.findall(r'\d+', "".join(nodes))
                        count = int(count_match[0]) if count_match else 0
                display = f"{count}권" if count > 0 else "없음"
                results.append({"name": lib['name'], "link": search_url, "status": display})

            # --- 일반 도서관 (.ink 방식) ---
            else:
                search_url = f"{lib['url']}?{lib['key_param']}={encoded_query}&schClst=ctts%2Cautr&schDvsn=001"
                resp = requests.get(search_url, timeout=5)
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

    # 직접 확인 도서관 추가 (서울도서관은 이제 위에서 검색되므로 제외)
    encoded_utf8 = quote(book_name.encode("utf-8"))
    direct_links = [
        {"name": " ", "link": None, "status": ""},
        {"name": "서초구", "link": f"https://e-book.seocholib.or.kr/search?keyword={encoded_utf8}", "status": "링크 확인"},
        {"name": "부천시", "link": f"https://ebook.bcl.go.kr:444/elibrary-front/search/searchList.ink?schTxt={encoded_utf8}&schClst=ctts%2Cautr&schDvsn=001", "status": "링크 확인"}
    ]
    results.extend(direct_links)
    progress_bar.empty()
    return results

# --- 화면 구성 ---
st.markdown('<h2 style="font-size:24px; margin-top:-50px; margin-bottom:10px;">📚 전자도서관 통합검색</h2>', unsafe_allow_html=True)
url_params = st.query_params
url_keyword = url_params.get("search", "")

keyword = st.text_input("책 제목을 입력하세요", value=url_keyword, placeholder="예: 행복의 기원", key="search_input")

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
            # 링크가 없는 구분선 행 처리
            if item['link'] is None:
                html_code += f"""
                    <tr style="background-color: #f1f3f5;">
                        <td colspan="2" style="padding: 8px; text-align: center; font-size: 12px; color: #666;">직접 링크 확인 도서관</td>
                    </tr>
                """
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
