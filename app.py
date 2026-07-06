import streamlit as st

# =======================================================
# [무조건 최상단 필수 설정] 앱 전체 기본 설정 (딱 한 번만 호출)
# =======================================================
st.set_page_config(page_title="중고차 진단평가 시스템", page_icon="🚘", layout="wide")


# =======================================================
# [보안 설정] 나만 쓸 수 있는 비밀번호
# =======================================================
PRIVATE_PASSWORD = "car77"  # 기본 비밀번호는 car77 입니다.

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 로그인 안 된 경우 화면 차단
if not st.session_state.authenticated:
    st.title("🔒 중고차 진단평가 시스템")
    st.subheader("인증된 사용자만 접속 가능합니다.")
    
    input_pw = st.text_input("접속 비밀번호 입력", type="password")
    if st.button("시스템 접속"):
        if input_pw == PRIVATE_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸습니다.")
    st.stop()


# =======================================================
# [로그인 성공 시] 멀티 페이지를 위한 기본 안내 메시지
# =======================================================
st.title("🚘 중고차 진단평가 시스템 홈")
st.info("👈 왼쪽 사이드바 메뉴에서 원하시는 평가기 페이지를 선택해 주세요!")

st.markdown("""
### 🧭 이용 가능한 메뉴
1. **1_기존페이지**: 기존에 사용하시던 단순 감가 방식의 가치 평가기입니다.
2. **2_자동차진단평가**: 법정 자동차진단평가 기준(올림 연산, 주행거리 한도)을 반영한 정밀 계산기입니다.
""")
