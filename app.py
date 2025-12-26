if keyword:
    with st.spinner(f"'{keyword}' 검색 중..."):
        data = search_libraries(keyword)
        
        html_code = f"""
        <div style="font-family: sans-serif;">
            <table style="width:100%; border-collapse: collapse; table-layout: fixed;">
                <thead>
                    <tr style="border-bottom: 2px solid #ddd; background-color: #f8f9fa;">
                        <th style="text-align:left; padding: 10px; width: 60%; font-size: 14px;">도서관 이름</th>
                        <th style="text-align:right; padding: 10px; width: 40%; font-size: 14px;">소장 현황</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i, item in enumerate(data):
            # 강남구(인덱스 5) 다음에 구분선 추가
            # 직접 확인 도서관 리스트가 시작되기 직전에 삽입됩니다.
            if item['name'] == "서울도서관":
                html_code += """
                    <tr style="background-color: #f1f3f5;">
                        <td colspan="2" style="padding: 8px 10px; font-size: 12px; color: #666; font-weight: bold; border-top: 2px solid #dee2e6;">
                            ▼ 아래 도서관은 링크를 통해 직접 확인이 필요합니다
                        </td>
                    </tr>
                """
            
            html_code += f"""
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 10px; font-weight: bold; color: #333; font-size: 15px;">{item['name']}</td>
                    <td style="padding: 10px; text-align: right;">
                        <a href="{item['link']}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold; font-size: 15px;">{item['status']}</a>
                    </td>
                </tr>
            """
            
        html_code += "</tbody></table></div>"
        
        # 구분선이 추가되었으므로 높이를 조금 더 여유있게(60 -> 100) 조절합니다.
        st.components.v1.html(html_code, height=len(data) * 45 + 100, scrolling=False)
