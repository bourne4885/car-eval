import streamlit as st

# =======================================================
# [보안 설정] 나만 쓸 수 있는 비밀번호 (원하는 대로 바꾸세요)
# =======================================================
PRIVATE_PASSWORD = "car77"  # 기본 비밀번호는 car77 입니다.

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 로그인 안 된 경우 화면 차단
if not st.session_state.authenticated:
    st.set_page_config(page_title="로그인 필요", page_icon="🔒", layout="centered")
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
# [본 프로그램 시작] 로그인 성공 시 실행되는 구간
# =======================================================
st.set_page_config(page_title="중고차 진단평가 산정기", page_icon="🚘", layout="wide")

st.title("🚘 나만의 중고차 진단평가 가격 산정기")
st.caption("성능점검지 기준 기반 가치 평가 매입/판매 산출 시스템")
st.markdown("---")

# 화면을 두 구역(좌측 입력창, 우측 결과창)으로 분할
left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.subheader("🛠️ 차량 기본 정보 및 성능지 체크")
    
    # 1. 차량 기본 정보
    car_name = st.text_input("차량명 (예: 그랜저 IG 2.4)", placeholder="메모용 차량명을 입력하세요")
    base_price = st.number_input("기준 가격 입력 (만원 단위)", min_value=0, value=2000, step=50, help="무사고, 상태 최상 기준의 시세")
    
    st.markdown("---")
    
    # 감가액 변수 누적 준비
    total_dep_amt = 0
    
    # 2. 외판 및 골격 교환/사고 이력 (성능지 주요 항목)
    st.markdown("### 1) 사고 / 교환 이력 (외판 및 골격)")
    
    # 외판 (볼트체결 부위 단순교환)
    st.write("**■ 외판 부위 단순 교환 (복수 선택 가능)**")
    outer_fender = st.checkbox("프론트 휀더 (건당 약 3% 감가)")
    outer_door = st.checkbox("도어 (앞/뒤 건당 약 4% 감가)")
    outer_bonnet = st.checkbox("후드 / 본네트 (약 5% 감가)")
    outer_trunk = st.checkbox("트렁크 리드 (약 5% 감가)")
    
    if outer_fender: total_dep_amt += base_price * 0.03
    if outer_door: total_dep_amt += base_price * 0.04
    if outer_bonnet: total_dep_amt += base_price * 0.05
    if outer_trunk: total_dep_amt += base_price * 0.05

    # 골격 (용접 및 주요 프레임 손상)
    st.write("**■ 주요 골격 부위 손상 (사고차 분류, 복수 선택 가능)**")
    frame_quarter = st.checkbox("쿼터 패널 / 리어 휀더 (약 7% 감가)")
    frame_inside = st.checkbox("인사이드 패널 / 사이드 멤버 (약 12% 감가)")
    frame_house = st.checkbox("휠 하우스 (약 20% 대형 감가)")
    
    if frame_quarter: total_dep_amt += base_price * 0.07
    if frame_inside: total_dep_amt += base_price * 0.12
    if frame_house: total_dep_amt += base_price * 0.20

    st.markdown("---")

    # 3. 원동기 / 변속기 상태 (누유)
    st.markdown("### 2) 엔진 및 변속기 상태")
    oil_leak = st.radio("누유 및 미세누유 여부", ["이상 없음 (미세누유 없음)", "미세누유 (오일 비침 - 건당 30만 원 감가)", "누유 (오일 흘러내림 - 건당 80만 원 감가)"])
    
    if oil_leak == "미세누유 (오일 비침 - 건당 30만 원 감가)":
        total_dep_amt += 30
    elif oil_leak == "누유 (오일 흘러내림 - 건당 80만 원 감가)":
        total_dep_amt += 80

    st.markdown("---")

    # 4. 주행거리 및 기타 특이사항
    st.markdown("### 3) 주행거리 및 용도 이력")
    mileage = st.radio("연식 대비 주행거리 상태", ["정상 수준 (연 1.5만~2만km 내외)", "주행거리 다소 많음 (시세의 5% 감가)", "주행거리 매우 많음 (시세의 12% 감가)"])
    rent_history = st.toggle("용도 변경 이력 있음 (렌트/영업용 이력 시 약 10% 감가)")
    
    if mileage == "주행거리 다소 많음 (시세의 5% 감가)":
        total_dep_amt += base_price * 0.05
    elif mileage == "주행거리 매우 많음 (시세의 12% 감가)":
        total_dep_amt += base_price * 0.12
        
    if rent_history:
        total_dep_amt += base_price * 0.10

with right_col:
    st.subheader("📊 진단평가 결과 산출 리포트")
    
    final_price = max(0.0, base_price - total_dep_amt)
    
    # 결과를 깔끔한 박스(컨테이너) 구조로 출력
    with st.container(border=True):
        if car_name:
            st.markdown(f"### 🚗 차량명: {car_name}")
        else:
            st.markdown("### 🚗 차량명: 미입력")
            
        st.write("---")
        
        # 메트릭 카드로 금액 표시
        c1, c2 = st.columns(2)
        c1.metric(label="최초 기준 시세", value=f"{base_price:.1f} 만원")
        c2.metric(label="총 차감 감가액", value=f"-{total_dep_amt:.1f} 만원", delta_color="inverse")
        
        st.write("---")
        
        # 최종 평가 금액 큰 글씨로 강조
        st.success(f"## 💰 최종 가치 평가액: {final_price:.1f} 만원")
        
    st.markdown(" ")
    st.info("💡 팁: 위 왼쪽 항목을 체크하는 즉시 오른쪽 최종 평가액이 실시간으로 계산됩니다.")
    
    # 네이버 카페 등에 기록하기 편하도록 텍스트 복사 기능 제공
    summary_text = f"▶ 차량명: {car_name if car_name else '미입력'}\n▶ 기준가: {base_price:.1f}만원\n▶ 총감가: {total_dep_amt:.1f}만원\n▶ 최종 진단평가액: {final_price:.1f}만원"