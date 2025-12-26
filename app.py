import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote

# 페이지 설정
st.set_page_config(page_title="전자도서관 통합검색", page_icon="📚")

# (중략: libraries 데이터 및 search_libraries 함수는 기존과 동일)
libraries = [
    {"name": "성남시", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "경기대", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "용인시", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "수원시", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "고양시", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "강남구", "url": "https://ebook.gangnam.go.kr/elibbook/book_info.asp", "key_param": "strSearch", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"}
]

def search_libraries(book_name):
    results = []
    progress_bar = st.progress(0)
    total = len(libraries)

    for i, lib in enumerate(libraries):
        progress_bar.progress((i + 1) / total)
        try:
            encoded_query = quote(book_name.encode(lib["encoding"]))
            if lib["type"] == "gangnam":
                search_url = f"{lib['url']}?{lib['key_param']}={encoded_query}&search=title"
            else:
                search_url = f"{lib['url']}?{lib['key_param']}={encoded_query}&schClst=ctts%2Cautr&schDvsn=001"

            resp = requests.get(search_url, timeout=5)
            if resp.status_code == 200:
                tree = html.fromstring(resp.content)
                nodes = tree.xpath(lib["xpath"])
                count = 0
                if nodes:
                    count_match = re.findall(r'\d+', "".join(nodes))
                    count = int(count_match[0]) if count_match else 0
                display = f'<a href="{search_url}" target="_blank" style="text-decoration:none; color:#007bff;">{count}권</a>' if count > 0 else "없음"
            else:
                display = "접속지연"
        except:
            display = "확인불가"
        results.append({"도서관": lib['name'], "결과": display})

    encoded_utf8 = quote(book_name.encode("utf-8"))
    direct_links = [
        {"도서관": "서울도서관", "url": f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={encoded_utf8}"},
        {"도서관": "서초구", "url": f"https://e-book.seocholib.or.kr/search?keyword={encoded_utf8}"},
        {"도서관": "부천시", "url": f"https://ebook.bcl.go.kr:444/elibrary-front/search/searchList.ink?schTxt={encoded_utf8}&schClst=ctts%2Cautr&schDvsn=001"}
    ]
    
    for item in direct_links:
        results.append({"도서관": item["도서관"], "결과": f'<a href="{item["url"]}" target="_blank" style="text-decoration:none; color:#6c757d;">확인필요</a>'})

    progress_bar.empty()
    return results

# 화면 구성
st.title("📚 전자도서관 통합검색")
st.markdown("---")

query_params = st.query_params
url_keyword = query_params.get("search", "")
keyword = st.text_input("책 제목을 입력하세요", value=url_keyword, placeholder="예: 행복의 기원", key="search_input")

if keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        res = search_libraries(keyword)
        
        # HTML 테이블 생성 (모바일에서도 가로 레이아웃 유지)
        table_html = """
        <style>
            .lib-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .lib-table th { text-align: left; border-bottom: 2px solid #ddd; padding: 10px; font-size: 16px; }
            .lib-table td { padding: 10px; border-bottom: 1px solid #eee; font-size: 15px; }
            .lib-name { width: 60%; font-weight: bold; }
            .lib-res { width: 40%; text-align: right; }
        </style>
        <table class="lib-table">
            <thead>
                <tr>
                    <th class="lib-name">도서관 이름</th>
                    <th class="lib-res">소장 현황</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for item in res:
            table_html += f"""
                <tr>
                    <td class="lib-name">{item['도서관']}</td>
                    <td class="lib-res">{item['결과']}</td>
                </tr>
            """
        
        table_html += "</tbody></table>"
        
        # HTML 렌더링
        st.write(table_html, unsafe_allow_html=True)
