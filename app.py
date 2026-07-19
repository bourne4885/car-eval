import hashlib
import streamlit as st

# 🚨 Streamlit 설정은 무조건 코드 최상단에 딱 한 번만 실행되어야 합니다.
st.set_page_config(page_title="실전 딜러형 경매 매입 시스템", page_icon="🚗", layout="wide")

# ==========================================
# 0. 보안 인증 엔진 (인코딩 및 세션 꼬임 해결)
# ==========================================
# 'car77'의 완벽한 오리지널 SHA-256 해시값 (소스코드 내 비밀번호 노출 완벽 차단)
CORRECT_HASH = "6543b59df5c4a5c93a027376c9b4e5781a8b94fde185e493e88849764516ba7d"

def check_password():
    """로그인 세션 상태를 관리하고 입력값의 오류를 잡아내는 함수"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # 이미 인증을 성공했다면 아래 메인 프로그램을 즉시 노출
    if st.session_state["authenticated"]:
        return True

    # 화면 중앙 정렬을 위한 레이아웃 구성
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🔒 시스템 보안 인증")
        st.caption("본 프로그램은 승인된 딜러 전용 시스템입니다. 접근 권한이 필요합니다.")
        
        # 💡 세션 버그를 유발하는 st.form을 제거하고 단독 입력창으로 즉시 검증합니다.
        password_input = st.text_input("접근 비밀번호를 입력하세요", type="password", key="pwd_input")
        
        if password_input:
            # 문자열에 숨겨진 공백이나 줄바꿈을 완벽하게 청소 (.strip())
            clean_password = password_input.strip()
            
            # UTF-8 규격으로 정확하게 바이트 변환 후 SHA-256 해시 생성
            input_hash = hashlib.sha256(clean_password.encode('utf-8')).hexdigest()
            
            if input_hash == CORRECT_HASH:
                st.session_state["authenticated"] = True
                st.success("🔓 인증 성공! 시스템을 로드합니다.")
                st.rerun()  # 화면을 새로고침하여 즉시 아래 본문을 실행
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다. 다시 시도해 주세요.")
                    
    return False

# --------------------------------------------------
# [보안 필터] 위의 인증 기능이 True를 반환해야만 메인 프로그램이 작동합니다.
# --------------------------------------------------
if check_password():

    # ==========================================
    # 1. 실전 경매 매입 산출 엔진 (딜러형 시장 감가)
    # ==========================================
    class RealMarketEvaluator:
        def __init__(self, is_import: bool, displacement: int, reg_year: int, reg_month: int, mileage: int, base_price_manwon: int):
            self.is_import = is_import
            self.displacement = displacement
            self.reg_year = reg_year
            self.reg_month = reg_month
            self.mileage = mileage
            self.base_price_manwon = base_price_manwon
            
            # 기준 시점 (2026년 7월)
            self.current_year = 2026
            self.current_month = 7

        def get_tier_info(self):
            """배기량에 따른 체급 분류 (참고용)"""
            if self.displacement >= 3000: return "대형"
            elif self.displacement >= 2000: return "중형"
            elif self.displacement >= 1600: return "준중형"
            else: return "소형/경형"

        def get_usage_period_and_rate(self):
            """연식 경과에 따른 시장 잔가율 산출 (수입차 감가 폭 확대)"""
            usage_years = self.current_year - self.reg_year
            remaining_months = self.current_month - self.reg_month
            usage_months = (usage_years * 12) + remaining_months
            if usage_months < 0: usage_months = 0
            
            if not self.is_import:
                if usage_years <= 1: age_rate = 0.85
                elif usage_years == 2: age_rate = 0.75
                elif usage_years == 3: age_rate = 0.65
                elif usage_years == 4: age_rate = 0.55
                elif usage_years == 5: age_rate = 0.48
                else: age_rate = max(0.10, 0.45 - (usage_years - 6) * 0.05)
            else:
                if usage_years <= 1: age_rate = 0.80
                elif usage_years == 2: age_rate = 0.68
                elif usage_years == 3: age_rate = 0.58
                elif usage_years == 4: age_rate = 0.48
                elif usage_years == 5: age_rate = 0.40
                else: age_rate = max(0.05, 0.35 - (usage_years - 6) * 0.06)
                
            return usage_years, usage_months, round(age_rate, 2)

        def calculate_market_accident_penalty(self, selected_accident):
            """🔥 딜러들이 쓰는 진짜 시장 감가 테이블 (국산/수입 차별화 적용)"""
            if not selected_accident:
                return 0, {}

            market_price_table = {
                "국산": {"1랭크": 40, "2랭크": 100, "A랭크": 200, "B랭크": 350, "C랭크": 500},
                "수입": {"1랭크": 80, "2랭크": 180, "A랭크": 350, "B랭크": 600, "C랭크": 900}
            }
            
            origin_key = "수입" if self.is_import else "국산"
            active_table = market_price_table[origin_key]
            
            total_penalty = 0
            detail_logs = {}
            
            for part, data in selected_accident.items():
                rank = data["rank"]
                status = data["status"]
                
                base_penalty = active_table.get(rank, 0)
                repair_factor = 1.0 if status == "교환(X)" else 0.6
                current_penalty = int(base_penalty * repair_factor)
                
                total_penalty += current_penalty
                detail_logs[part] = f"{status} ──> 실전 시장 감가: -{current_penalty}만 원 ({rank} 기준)"
                
            return total_penalty, detail_logs

    # ==========================================
    # 2. Streamlit 웹 UI 화면 구성 (본문)
    # ==========================================
    st.title("🚗 실전 딜러형 중고차 경매 입찰가 산출기")
    st.caption("자격검정 시험용 루트 공식을 제거하고, 매매단지 딜러들이 시세 산정 시 차감하는 '리얼 시장 정액 감가'를 반영합니다.")

    all_car_parts = {
        "🔻 외판 단순 교환/판금 (1랭크)": {
            "후드": "1랭크", "프론트 펜더(좌)": "1랭크", "프론트 펜더(우)": "1랭크",
            "앞도어(좌)": "1랭크", "앞도어(우)": "1랭크", "뒷도어(좌)": "1랭크", "뒷도어(우)": "1랭크",
            "트렁크 리드": "1랭크"
        },
        "🔻 외판 주요 부위 (2랭크)": {
            "쿼터 패널(좌)": "2랭크", "쿼터 패널(우)": "2랭크", "루프 패널": "2랭크"
        },
        "🔺 주요 골격 경미 사고 (A랭크)": {
            "프론트 패널": "A랭크", "리어 패널": "A랭크", "트렁크 플로어 패널": "A랭크"
        },
        "🔺 주요 골격 중대 사고 (B/C랭크)": {
            "사이드 멤버(좌)": "B랭크", "사이드 멤버(우)": "B랭크", "휠 하우스(좌)": "B랭크", "휠 하우스(우)": "B랭크", "대쉬 패널": "C랭크"
        }
    }

    # 섹션 1: 차량 조건 설정
    st.header("📝 1. 차량 기본 정보 및 매입 목표")
    col1, col2, col3 = st.columns(3)

    with col1:
        origin = st.selectbox("차량 구분", ["국산", "수입"])
        displacement = st.number_input("배기량 (cc)", min_value=100, max_value=10000, value=2000, step=100)
        base_price = st.number_input("신차 가격 또는 정상 시세 (만원)", min_value=0, value=4000, step=100)

    with col2:
        reg_year = st.number_input("최초등록년도", min_value=2000, max_value=2026, value=2022, step=1)
        reg_month = st.slider("최초등록월", min_value=1, max_value=12, value=1)
        mileage = st.number_input("실제 주행거리 (km)", min_value=0, max_value=1000000, value=60000, step=1000)

    with col3:
        target_margin = st.number_input("확보할 딜러 매입 마진 (만원)", min_value=0, value=150, step=10)
        fixed_cost = st.number_input("상사 이전비 및 상품화 부대비용 (만원)", min_value=0, value=50)
        paint_unit_cost = st.number_input("🎨 판당 도색 단가 (만원)", min_value=0, value=15 if origin == "국산" else 25, step=5)
        auction_fee_rate = st.slider("경매장 낙찰 수수료율 (%)", min_value=0.0, max_value=5.0, value=2.2, step=0.1)

    st.markdown("---")

    # 섹션 2: 사고 감가 선택
    st.header("🛠️ 2. 실전 사고 수리 이력 체크")
    selected_accident = {}
    for section_title, parts in all_car_parts.items():
        st.markdown(f"##### {section_title}")
        part_items = list(parts.items())
        for i in range(0, len(part_items), 4):
            chunk = part_items[i:i+4]
            cols = st.columns(4)
            for idx, (part_name, rank) in enumerate(chunk):
                with cols[idx]:
                    status = st.selectbox(f"{part_name}", ["정상", "교환(X)", "판금/용접(W)"], key=f"acc_{part_name}")
                    if status != "정상":
                        selected_accident[part_name] = {"rank": rank, "status": status}

    st.markdown("---")

    # 섹션 3: 외관 도색 선택
    st.header("🎨 3. 현장 도색/판금 필요 부위 (상품화 비용)")
    selected_paint_parts = []
    for section_title, parts in all_car_parts.items():
        if "골격" in section_title: continue
        st.markdown(f"##### {section_title}")
        part_items = list(parts.items())
        for i in range(0, len(part_items), 4):
            chunk = part_items[i:i+4]
            cols = st.columns(4)
            for idx, (part_name, rank) in enumerate(chunk):
                with cols[idx]:
                    if st.checkbox(f"{part_name} 도색 필요", key=f"paint_{part_name}"):
                        selected_paint_parts.append(part_name)

    st.markdown("---")

    # 섹션 4: 연산 실행 및 대시보드
    if st.button("📊 실전 경매 입찰 마지노선 산출", type="primary", use_container_width=True):
        is_imp = (origin == "수입")
        
        engine = RealMarketEvaluator(is_import=is_imp, displacement=displacement, reg_year=reg_year, reg_month=reg_month, mileage=mileage, base_price_manwon=base_price)
        tier_name = engine.get_tier_info()
        u_year, u_month, age_rate = engine.get_usage_period_and_rate()

        age_price = base_price * age_rate
        age_penalty = base_price - age_price
        accident_penalty, logs = engine.calculate_market_accident_penalty(selected_accident)
        
        paint_count = len(selected_paint_parts)
        paint_penalty = paint_count * paint_unit_cost

        total_reduction = age_penalty + accident_penalty + paint_penalty
        evaluated_car_value = max(0, base_price - total_reduction)

        fee_factor = 1 + (auction_fee_rate / 100)
        max_bid_price = (evaluated_car_value - fixed_cost - target_margin) / fee_factor
        max_bid_price = max(0, round(max_bid_price))

        st.header("🎯 실전 경매 매입 분석 리포트")
        
        if logs:
            st.subheader("📋 실전 시장 사고 감가 내역")
            for p_name, log_txt in logs.items():
                st.warning(f"• {p_name} ── {log_txt}")

        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.metric(label="🏁 최종 추천 최고 입찰가 (Max Bid)", value=f"{max_bid_price:,} 만원")
            st.info(f"💡 {origin}차 {tier_name}급 / {u_year}년 경과 잔존율 {int(age_rate*100)}% 적용")

        with res_col2:
            st.metric(label="📉 차값에서 빠진 종합 금액", value=f"-{round(total_reduction):,} 만원")
            st.text(f"   • 기본 경과 연식 감가: {round(age_penalty):,} 만원")
            st.text(f"   • 🔥 실전 시장 사고 감가: {accident_penalty:,} 만원")
            st.text(f"   • 현장 도색 필요 비용 ({paint_count}판): {paint_penalty:,} 만원")

        st.markdown("---")
        st.error(f"⚠️ **딜러용 최종 브리핑**: 사고 및 연식 조율 후 차량의 리얼 가치는 **{evaluated_car_value:,}만 원**입니다. 상사 마진 {target_margin}만 원을 깨지 않으려면 경매 낙찰 수수료를 포함해 **[{max_bid_price:,}만 원]** 밑으로 무조건 잡으셔야 합니다.")