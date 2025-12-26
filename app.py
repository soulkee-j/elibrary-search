import streamlit as st
import requests
from lxml import html
import re
from urllib.parse import quote

st.set_page_config(page_title="통합 전자도서관 검색", page_icon="📚")

# 기본 도서관 (성남, 경기대, 용인, 수원, 고양, 강남)
libraries = [
    {"name": "성남시 전자도서관", "url": "https://vodbook.snlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "standard"},
    {"name": "경기대학교", "url": "https://ebook.kyonggi.ac.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "standard"},
    {"name": "용인시 전자책도서관", "url": "https://ebook.yongin.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "standard"},
    {"name": "수원시 전자도서관", "url": "https://ebook.suwonlib.go.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "standard"},
    {"name": "고양시 도서관센터", "url": "https://ebook.goyanglib.or.kr/elibrary-front/search/searchList.ink", "key_param": "schTxt", "xpath": '//*[@id="container"]/div/div[4]/p/strong[2]/text()', "encoding": "utf-8", "type": "standard"},
    {"name": "강남구 전자도서관", "url": "https://ebook.gangnam.go.kr/elibbook/book_info.asp", "key_param": "strSearch", "xpath": '//*[@id="container"]/div[1]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div/strong/text()', "encoding": "euc-kr", "type": "gangnam"}
]

def search_libraries(book_name):
    results = []
    progress_bar = st.progress(0)
    
    # 브라우저처럼 보이기 위한 헤더 설정 (중요!)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    # 1. 일반 도서관 검색
    for i, lib in enumerate(libraries):
        progress_bar.progress((i + 1) / (len(libraries) + 4))
        try:
            query = quote(book_name.encode(lib["encoding"]))
            search_url = f"{lib['url']}?{lib['key_param']}={query}"
            if lib["type"] == "standard": search_url += "&schClst=ctts%2Cautr&schDvsn=001"
            elif lib["type"] == "gangnam": search_url += "&search=title"

            resp = requests.get(search_url, headers=headers, timeout=5)
            tree = html.fromstring(resp.content)
            nodes = tree.xpath(lib["xpath"])
            count = int(re.findall(r'\d+', "".join(nodes))[0]) if nodes and re.findall(r'\d+', "".join(nodes)) else 0
            results.append({"도서관": lib['name'], "결과": f"[{count}권 발견]({search_url})" if count > 0 else "없음"})
        except:
            results.append({"도서관": lib['name'], "결과": "확인불가"})

    # 2. 서울도서관 (API 방식)
    try:
        seoul_api = f"https://elib.seoul.go.kr/api/contents/search?keyword={quote(book_name)}&t=EB"
        seoul_resp = requests.get(seoul_api, headers=headers, timeout=5).json()
        s_count = seoul_resp.get('data', {}).get('totalCount', 0)
        s_link = f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={quote(book_name)}"
        results.append({"도서관": "서울도서관", "결과": f"[{s_count}권 발견]({s_link})" if s_count > 0 else "없음"})
    except:
        results.append({"도서관": "서울도서관", "결과": "확인불가"})

    # 3. 서초구 (API 방식)
    try:
        sc_api = f"https://e-book.seocholib.or.kr/api/contents/search?keyword={quote(book_name)}"
        sc_resp = requests.get(sc_api, headers=headers, timeout=5).json()
        eb_count = sc_resp.get('data', {}).get('totalCount', 0)
        
        sub_api = f"{sc_api}&contentType=SUBS"
        sub_resp = requests.get(sub_api, headers=headers, timeout=5).json()
        sub_count = sub_resp.get('data', {}).get('totalCount', 0)
        
        sc_link = f"https://e-book.seocholib.or.kr/search?keyword={quote(book_name)}"
        results.append({"도서관": "서초구(전자책)", "결과": f"[{eb_count}권 발견]({sc_link})" if eb_count > 0 else "없음"})
        results.append({"도서관": "서초구(구독형)", "결과": f"[{sub_count}권 발견]({sc_link}&contentType=SUBS)" if sub_count > 0 else "없음"})
    except:
        results.append({"도서관": "서초구 도서관", "결과": "확인불가"})

    # 4. 부천시 (보안 포트 대응)
    try:
        bc_url = f"https://ebook.bcl.go.kr:444/elibrary-front/search/searchList.ink?schTxt={quote(book_name)}&schClst=ctts%2Cautr&schDvsn=001"
        bc_resp = requests.get(bc_url, headers=headers, timeout=5, verify=False) # SSL 검증 무시
        tree = html.fromstring(bc_resp.content)
        bc_nodes = tree.xpath('//*[@id="container"]/div/div[4]/p/strong[2]/text()')
        bc_count = int(re.findall(r'\d+', "".join(bc_nodes))[0]) if bc_nodes else 0
        results.append({"도서관": "부천시립도서관", "결과": f"[{bc_count}권 발견]({bc_url})" if bc_count > 0 else "없음"})
    except:
        results.append({"도서관": "부천시립도서관", "결과": "확인불가"})

    progress_bar.empty()
    return results

# 화면 구성 (Alfred 연동 포함)
st.title("📚 통합 전자도서관 검색")
st.markdown("---")

query_params = st.query_params
url_keyword = query_params.get("search", "")

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
