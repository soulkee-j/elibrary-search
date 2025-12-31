import streamlit as st
import requests
from urllib.parse import quote

# 발급받으신 인증키를 여기에 입력하세요
SEOUL_API_KEY = "4a696550776a756e373246546c6468"

def search_seoul_library(book_name):
    unique_books = set()  # 중복 제거용 집합
    book_details = []     # 검증을 위해 검색된 책 목록 저장
    
    # 검색 필드: 제목(TITLE)과 저자(AUTHOR)
    search_fields = ["TITLE", "AUTHOR"]
    
    encoded_query = quote(book_name.encode("utf-8"))
    
    for field in search_fields:
        # API 호출 (구독형 E02 / 최대 100건 조회)
        api_url = f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/json/SeoulLibraryBookSearchInfo/1/100/E02/{field}/{encoded_query}"
        
        try:
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                
                # 데이터가 정상적으로 존재하는지 확인
                if "SeoulLibraryBookSearchInfo" in data:
                    rows = data["SeoulLibraryBookSearchInfo"]["row"]
                    
                    for book in rows:
                        # 1. 자료유형코드가 "ze" (전자책)인 것만 필터링
                        is_ebook = book.get("BIB_TYPE_CODE") == "ze" or "전자책" in book.get("BIB_TYPE_NAME", "")
                        
                        if is_ebook:
                            # 2. 중복 제거를 위한 고유 ID (BOOK_MAST_NO가 가장 정확함)
                            book_id = book.get("BOOK_MAST_NO")
                            
                            if book_id not in unique_books:
                                unique_books.add(book_id)
                                # 검증용 리스트에 추가
                                book_details.append({
                                    "제목": book.get("TITLE"),
                                    "저자": book.get("AUTHOR"),
                                    "발행년": book.get("PUBLISH_YEAR"),
                                    "ID": book_id,
                                    "검색경로": field # 어떤 필드에서 검색되었는지 기록
                                })
        except Exception as e:
            st.error(f"{field} 검색 중 오류 발생: {e}")
            
    return book_details

# --- Streamlit UI ---
st.set_page_config(page_title="서울도서관 API 테스트", layout="wide")
st.title("📚 서울도서관 전자책 통합검색 검증")
st.info("제목과 저자에서 중복 없이 '전자책(ze)'만 추출합니다.")

keyword = st.text_input("검색어를 입력하세요 (예: 한강, 소년이 온다)", "")

if keyword:
    with st.spinner("서울도서관 API 호출 중..."):
        results = search_seoul_library(keyword)
        
        if results:
            st.success(f"중복 제거 후 총 **{len(results)}**권의 전자책이 검색되었습니다.")
            
            # 결과를 표로 보여줌
            st.table(results)
            
            # 실제 이동할 링크 안내
            web_link = f"https://elib.seoul.go.kr/contents/search/content?t=EB&k={quote(keyword.encode('utf-8'))}"
            st.markdown(f"🔗 [서울도서관 전자도서관에서 확인하기]({web_link})")
        else:
            st.warning("검색 결과가 없습니다. (전자책 유형 'ze'가 없을 수 있습니다.)")
