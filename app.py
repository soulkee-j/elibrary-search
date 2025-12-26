import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="전자도서관 통합검색", page_icon="📚")

# 2. 도서관 데이터 정의
libraries = [
    {"name": "성남시", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "경기대", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "용인시", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "수원시", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "고양시", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "강남구", "url": "https://ebook.gangnam.go.kr/elibbook/book_info.asp", "key_param": "strSearch", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"}
]

# 3. 검색 함수 정의
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
            count = 0
            if resp.status_code == 200:
                tree = html.fromstring(resp.content)
                nodes = tree.xpath(lib["xpath"])
                if nodes:
                    count_match = re.findall(r'\d+', "".join(nodes))
                    count = int(count_match[0]) if count_match else 0
            
            # 표에 표시할 텍스트 결정
            status_text = f"{count}권" if count > 0 else "없음"
            results.append({"도서관 이름": lib['name'], "링크": search_url, "소장 현황": status_text})
        except:
            results.append({"도서관 이름": lib['name'], "링크": "#", "소장 현황": "확인불가"})

    # 직접 확인 도서관 추가
    encoded_utf8 = quote(book_name.encode("utf-8"))
    direct_links = [
        {"도서관 이름": "서울도서관", "링크": f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={encoded_utf8}", "소장 현황": "링크 확인"},
        {"도서관 이름": "서초구", "링크": f"https://e-book.seocholib.or.kr/search?keyword={encoded_utf8}", "소장 현황": "링크 확인"},
        {"도서관 이름": "부천시", "링크": f"https://ebook.bcl.go.kr:444/elibrary-front/search/searchList.ink?schTxt={encoded_utf8}&schClst=ctts%2Cautr&schDvsn=001", "소장 현황": "링크 확인"}
    ]
    results.extend(direct_links)
    
    progress_bar.empty()
    return results

# 4. 화면 구성
st.title("📚 전자도서관 통합검색")
st.write("제목 입력 후 엔터(Enter)를 누르세요.")
st.markdown("---")

# URL 파라미터 읽기
url_keyword = st.query_params.get("search", "")

# 입력창
keyword = st.text_input("책 제목을 입력하세요", value=url_keyword, placeholder="예: 행복의 기원", key="search_input")

# 5. 검색 실행 및 결과 출력
if keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        raw_data = search_libraries(keyword)
        df = pd.DataFrame(raw_data)
        
        # [핵심] 2컬럼 레이아웃 구현
        st.dataframe(
            df,
            column_config={
                "도서관 이름": st.column_config.TextColumn("도서관 이름", width="medium"),
                "소장 현황": st.column_config.LinkColumn(
                    "소장 현황", 
                    width="small",
                    # '링크' 컬럼에 있는 URL을 사용하되, 화면에는 '소장 현황' 컬럼의 텍스트를 표시함
                    display_text=r"^.*$", # 셀의 텍스트를 그대로 링크 텍스트로 사용하라는 정규식
                ),
                "링크": None # URL 컬럼은 데이터 소스로만 쓰고 화면에선 숨김
            },
            column_order=("도서관 이름", "소장 현황"),
            hide_index=True,
            use_container_width=True
        )
