import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote

# 페이지 설정
st.set_page_config(page_title="도서관 통합 검색", page_icon="📚")

# 일반 도서관 설정
libraries = [
    {"name": "성남시 전자도서관", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "경기대학교", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "용인시 전자책도서관", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "수원시 전자도서관", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "고양시 도서관센터", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "ink"},
    {"name": "강남구 전자도서관", "url": "https://ebook.gangnam.go.kr/elibbook/book_info.asp", "key_param": "strSearch", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"},
]

def search_all_libraries(book_name):
    results = []
    progress_bar = st.progress(0)
    
    # 1. 일반 도서관 검색
    for i, lib in enumerate(libraries):
        progress_bar.progress((i + 1) / (len(libraries) + 1))
        try:
            encoded_query = quote(book_name.encode(lib["encoding"]))
            if lib["name"] == "강남구 전자도서관":
                search_url = f"{lib['url']}?{lib['key_param']}={encoded_query}&search=title"
            else:
                search_url = f"{lib['url']}?{lib['key_param']}={encoded_query}&schClst=ctts%2Cautr&schDvsn=001"

            resp = requests.get(search_url, timeout=7)
            tree = html.fromstring(resp.content)
            nodes = tree.xpath(lib["xpath"])
            count = 0
            if nodes:
                count_match = re.findall(r'\d+', "".join(nodes))
                count = int(count_match[0]) if count_match else 0
            
            display = f"[{count}권 발견]({search_url})" if count > 0 else "없음"
            results.append({"도서관": lib['name'], "결과": display})
        except:
            results.append({"도서관": lib['name'], "결과": "에러"})

    # 2. 서초구 전자도서관 특수 검색 (API 직접 호출 방식)
    try:
        # 서초구는 웹페이지가 아닌 데이터 서버에 직접 물어봅니다.
        api_url = f"https://e-book.seocholib.or.kr/api/contents/search?keyword={quote(book_name)}&size=1"
        api_resp = requests.get(api_url, timeout=7).json()
        
        # 소장형(EB)과 구독형(SB) 데이터 추출
        eb_count = api_resp.get('data', {}).get('totalCount', 0)
        
        # 구독형 데이터는 별도 파라미터로 확인
        sub_api_url = f"https://e-book.seocholib.or.kr/api/contents/search?keyword={quote(book_name)}&size=1&contentType=SUBS"
        sub_resp = requests.get(sub_api_url, timeout=7).json()
        sub_count = sub_resp.get('data', {}).get('totalCount', 0)

        link = f"https://e-book.seocholib.or.kr/search?keyword={quote(book_name)}"
        results.append({"도서관": "서초구 도서관(전자책)", "결과": f"[{eb_count}권 발견]({link})" if eb_count > 0 else "없음"})
        results.append({"도서관": "서초구 도서관(구독형)", "결과": f"[{sub_count}권 발견]({link}&contentType=SUBS)" if sub_count > 0 else "없음"})
    except:
        results.append({"도서관": "서초구 도서관", "결과": "검색 실패"})

    progress_bar.empty()
    return results

# 화면 구성
st.title("📚 도서관 통합 검색기")
st.write("책 제목을 입력하고 **엔터(Enter)**를 누르세요.")
st.markdown("---")

keyword = st.text_input("책 제목을 입력하세요", placeholder="예: 행복의 기원", key="search_input")

if keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        res = search_all_libraries(keyword)
        
        col1, col2 = st.columns([2, 1])
        col1.write("**도서관 이름**")
        col2.write("**소장 현황 (클릭 시 이동)**")
        st.divider()

        for item in res:
            c1, c2 = st.columns([2, 1])
            c1.write(item["도서관"])
            c2.markdown(item["결과"])
