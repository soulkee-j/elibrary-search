import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote

# 페이지 설정
st.set_page_config(page_title="도서관 통합 검색", page_icon="📚")

# 도서관 데이터 설정
libraries = [
    {"name": "성남시 전자도서관", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8"},
    {"name": "경기대학교", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8"},
    {"name": "용인시 전자책도서관", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8"},
    {"name": "수원시 전자도서관", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8"},
    {"name": "고양시 도서관센터", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8"},
    {"name": "강남구 전자도서관", "url": "https://ebook.gangnam.go.kr/elibbook/book_info.asp", "key_param": "strSearch", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr"}
]

def search_books(book_name):
    results = []
    progress_bar = st.progress(0)
    total = len(libraries)

    for i, lib in enumerate(libraries):
        progress_bar.progress((i + 1) / total)
        try:
            if lib["name"] == "강남구 전자도서관":
                encoded = quote(book_name.encode('euc-kr'))
                search_url = f"{lib['url']}?{lib['key_param']}={encoded}&search=title"
            else:
                encoded = quote(book_name.encode('utf-8'))
                search_url = f"{lib['url']}?{lib['key_param']}={encoded}&schClst=ctts%2Cautr&schDvsn=001"

            resp = requests.get(search_url, timeout=5)
            if resp.status_code == 200:
                tree = html.fromstring(resp.content)
                texts = tree.xpath(lib["xpath"])
                if texts:
                    count_match = re.findall(r'\d+', texts[0].strip())
                    count = int(count_match[0]) if count_match else 0
                    result_display = f"[{count}권 발견]({search_url})" if count > 0 else "없음"
                else:
                    result_display = "검색실패"
            else:
                result_display = "접속불가"
        except:
            result_display = "에러발생"
        results.append({"도서관": lib['name'], "결과": result_display})
    progress_bar.empty()
    return results

# 화면 구성
st.title("📚 도서관 통합 검색기")
st.write("책 제목을 입력하고 **엔터**를 누르거나 **검색** 버튼을 클릭하세요.")

# [중요] 폼(Form)을 사용하면 엔터키가 자동으로 버튼 클릭으로 연결됩니다.
with st.form(key='search_form'):
    keyword = st.text_input("책 제목을 입력하세요", placeholder="예: 행복의 기원")
    submit_button = st.form_submit_button(label='검색 시작')

# 검색 버튼이 눌리거나 엔터가 입력되었을 때 실행
if submit_button and keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        res = search_books(keyword)
        
        col1, col2 = st.columns([2, 1])
        col1.write("**도서관 이름**")
        col2.write("**소장 현황 (클릭 시 이동)**")
        st.divider()

        for item in res:
            c1, c2 = st.columns([2, 1])
            c1.write(item["도서관"])
            c2.markdown(item["결과"])
elif submit_button and not keyword:
    st.warning("검색어를 입력해주세요.")
