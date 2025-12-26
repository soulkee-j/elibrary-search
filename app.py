import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote

# 페이지 설정
st.set_page_config(page_title="도서관 통합 검색", page_icon="📚")

# 실시간 결과 추출이 가능한 6개 도서관
libraries = [
    {"name": "성남시 전자도서관", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "경기대학교", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "용인시 전자책도서관", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "수원시 전자도서관", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "고양시 도서관센터", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "강남구 전자도서관", "url": "https://ebook.gangnam.go.kr/elibbook/book_info.asp", "key_param": "strSearch", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"}
]

def search_libraries(book_name):
    results = []
    progress_bar = st.progress(0)
    total = len(libraries)

    # 1. 기존 6개 도서관 실시간 검색
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
                
                display = f"[{count}권 발견]({search_url})" if count > 0 else "없음"
            else:
                display = "접속지연"
        except:
            display = "확인불가"
        results.append({"도서관": lib['name'], "결과": display})

    # 2. 직접 확인 도서관 3곳 추가 (고정 링크)
    encoded_utf8 = quote(book_name.encode("utf-8"))
    
    direct_links = [
        {"도서관": "서울도서관", "url": f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={encoded_utf8}"},
        {"도서관": "서초구 전자도서관", "url": f"https://e-book.seocholib.or.kr/search?keyword={encoded_utf8}"},
        {"도서관": "부천시립도서관", "url": f"https://ebook.bcl.go.kr:444/elibrary-front/search/searchList.ink?schTxt={encoded_utf8}&schClst=ctts%2Cautr&schDvsn=001"}
    ]
    
    for item in direct_links:
        results.append({"도서관": item["도서관"], "결과": f"[직접 확인]({item['url']})"})

    progress_bar.empty()
    return results

# 화면 구성
st.title("📚 통합 전자도서관 검색")
st.write("제목 입력 후 **엔터(Enter)**를 누르세요. (Alfred 연동 지원)")
st.markdown("---")

# Alfred 연동을 위한 URL 파라미터 읽기
query_params = st.query_params
url_keyword = query_params.get("search", "")

# 입력창 (URL에 검색어가 있으면 자동 입력됨)
keyword = st.text_input("책 제목을 입력하세요", value=url_keyword, placeholder="예: 행복의 기원", key="search_input")

if keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        res = search_libraries(keyword)
        
        col1, col2 = st.columns([2, 1])
        col1.write("**도서관 이름**")
        col2.write("**소장 현황 (클릭 시 이동)**")
        st.divider()

        for item in res:
            c1, c2 = st.columns([2, 1])
            c1.write(item["도서관"])
            c2.markdown(item["결과"])
