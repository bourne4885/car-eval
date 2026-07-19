import streamlit as st

# ==========================================
# 1. 실전 경매 매입 산출 엔진 (딜러형 시장 감가 고도화)
# ==========================================
class RealMarketEvaluator:
    def __init__(self, is_import: bool, displacement: int, reg_year: int, reg_month: int, mileage: int, base_price_manwon: int):
        self.is_import = is_import
        self.displacement = displacement
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.mileage = mileage
        self.base_price_manwon = base_price_manwon # 무사고 기준 정상 시세로 정의
        
        # 기준 시점 (2026년 7월)
        self.current_year = 2026
        self.current_month = 7

    def get_tier_info(self):
        """배기량에 따른 체급 분류"""
        if self.displacement >= 3000: return "대형"
        elif self.displacement >= 2000: return "중형"
        elif self.displacement >= 1600: return "준중형"
        else: return "소형/경형"

    def get_usage_period(self):
        """경과 연수 및 개월 수 계산"""
        usage_years = self.current_year - self.reg_year
        remaining_months = self.current_month - self.reg_month
        usage_months = (usage_years * 12) + remaining_months
        return usage_years, max(0, usage_months)

    def calculate_mileage_penalty(self, usage_years):
        """🔥 [추가] 주행거리 과다/과소에 따른 실전 감가 산출"""
        # 연간 표준 주행거리를 20,000 km로 가정
        standard_mileage = max(1, usage_years) * 20000
        mileage_diff = self.mileage - standard_mileage
        
        # km당 감가 단가 (국산: 1km당 80원 -> 1만km당 80만원 | 수입: 1km당 150원 -> 1만km당 150만원)
        unit_cost = 0.015 if self.is_import else 0.008
        
        # 주행거리가 짧으면 가산(+), 길면 감가(-)
        mileage_penalty = int(mileage_diff * unit_cost)
        return mileage_penalty, standard_mileage

    def calculate_market_accident_penalty(self, selected_accident):
        """딜러들이 쓰는 진짜 시장 사고 감가 테이블"""
        if not selected_accident:
            return 0, {}

        # 랭크별 실전 정액 감가 기준 (단위: 만원)
        market_price_table = {
            "국산": {"1랭크": 40, "2랭크": 100, "A랭크": 180, "B랭크": 300, "C랭크": 450},
            "수입": {"1랭크": 70, "2랭크": 150, "A랭크": 300, "B랭크": 550, "C랭크": 800}
        }
        
        origin_key = "수입" if self.is_import else "국산"
        active_table = market_price_table[origin_key]
        
        total_penalty = 0
        detail_logs = {}
        
        for part, data in selected_accident.items():
            rank = data["rank"]
            status = data["status"]
            
            base_penalty = active_table.get(rank, 0)
            
            # 교환 100%, 판금/용접 60% 적용
            repair_factor = 1.0 if status == "교환(X)" else 0.6
            current_penalty = int(base_penalty * repair_factor)
            
            total_penalty += current_penalty
            detail_logs[part] = f"{status} ──> 감가: -{current_penalty}만 원 ({rank})"
            
        return total_penalty, detail_logs

# ==========================================
# 2. Streamlit 웹 UI 화면 구성
# ==========================================
st.set_page_config(page_title="실전 딜러형 경매 매입 시스템", page_icon="🚗", layout="wide")

st.title("🚗 실전 딜러형 중고차 경매 입찰가 산출기")
st.caption("현업 매매단지 딜러들이 시세 산정 시 차감하는 '리얼 시장 정액 감가' 및 '주행거리 밸런스 연산'을 반영합니다.")

# 차량 부위 및 매칭 랭크 정의
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

# --------------------------------------------------
# 섹션 1: 차량 조건 설정
# --------------------------------------------------
st.header("📝 1. 차량 기본 정보 및 매입 목표")
col1, col2, col3 = st.columns(3)

with col1:
    origin = st.selectbox("차량 구분", ["국산", "수입"])
    displacement = st.number_input("배기량 (cc)", min_value=100, max_value=10000, value=2000, step=100)
    base_price = st.number_input("현재 무사고 정상 소매 시세 (만원)", min_value=0, value=2500, step=50)

with col2:
    reg_year = st.number_input("최초등록년도", min_value=2000, max_value=2026, value=2022, step=1)
    reg_month = st.slider("최초등록월", min_value=1, max_value=12, value=1)
    mileage = st.number_input("실제 주행거리 (km)", min_value=0, max_value=1000000, value=60000, step=5000)

with col3:
    target_margin = st.number_input("확보할 딜러 매입 마진 (만원)", min_value=0, value=150, step=10)
    fixed_cost = st.number_input("상사 이전비 및 상품화 부대비용 (만원)", min_value=0, value=50)
    paint_unit_cost = st.number_input("🎨 판당 도색 단가 (만원)", min_value=0, value=15 if origin == "국산" else 25, step=5)
    auction_fee_rate = st.slider("경매장 낙찰 수수료율 (%)", min_value=0.0, max_value=5.0, value=2.2, step=0.1)

st.markdown("---")

# --------------------------------------------------
# 섹션 2: 사고 감가 선택
# --------------------------------------------------
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

# --------------------------------------------------
# 섹션 3: 외관 도색 선택
# --------------------------------------------------
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

# --------------------------------------------------
# 섹션 4: 실시간 연산 및 대시보드 (버튼 제거하여 편의성 증대)
# --------------------------------------------------
is_imp = (origin == "수입")
engine = RealMarketEvaluator(is_import=is_imp, displacement=displacement, reg_year=reg_year, reg_month=reg_month, mileage=mileage, base_price_manwon=base_price)

tier_name = engine.get_tier_info()
u_year, u_month = engine.get_usage_period()

# 1. 🔥 [추가] 주행거리 감가 계산
mileage_penalty, std_mileage = engine.calculate_mileage_penalty(u_year)

# 2. 진짜 시장 사고 감가액 계산
accident_penalty, logs = engine.calculate_market_accident_penalty(selected_accident)

# 3. 도색비 계산
paint_count = len(selected_paint_parts)
paint_penalty = paint_count * paint_unit_cost

# 4. 종합 계산 (시세 기준 감가이므로 연식 자체 잔가율 곱은 생략하고 기준 시세에서 감가액들을 직접 차감)
total_reduction = mileage_penalty + accident_penalty + paint_penalty
evaluated_car_value = max(0, base_price - total_reduction)

fee_factor = 1 + (auction_fee_rate / 100)
max_bid_price = (evaluated_car_value - fixed_cost - target_margin) / fee_factor
max_bid_price = max(0, round(max_bid_price))

# 결과 리포트 대시보드
st.header("🎯 실전 경매 매입 분석 리포트")

if logs or mileage_penalty != 0:
    st.subheader("📋 감가 및 변동 상세 내역")
    if mileage_penalty > 0:
        st.error(f"• 주행거리 과다 ──> 표준({std_mileage:,}km) 대비 수리/피로도 감가: -{abs(mileage_penalty):,}만 원")
    elif mileage_penalty < 0:
        st.success(f"• 주행거리 짧음 ──> 표준({std_mileage:,}km) 대비 메리트 가산: +{abs(mileage_penalty):,}만 원")
        
    for p_name, log_txt in logs.items():
        st.warning(f"• {p_name} ── {log_txt}")

res_col1, res_col2 = st.columns(2)
with res_col1:
    st.metric(label="🏁 최종 추천 최고 입찰가 (Max Bid)", value=f"{max_bid_price:,} 만원")
    st.info(f"💡 {origin}차 {tier_name}급 / {u_year}년 {u_month%12}개월 경과 상태 반영")

with res_col2:
    status_symbol = "-" if total_reduction >= 0 else "+"
    st.metric(label="📉 차량 가치 변동 종합", value=f"{status_symbol}{abs(round(total_reduction)):,} 만원")
    st.text(f"  • 주행거리 정산 비용: {mileage_penalty:,} 만원")
    st.text(f"  • 🔥 실전 시장 사고 감가: {accident_penalty:,} 만원")
    st.text(f"  • 현장 도색 필요 비용 ({paint_count}판): {paint_penalty:,} 만원")

st.markdown("---")
st.error(f"⚠️ **딜러용 최종 브리핑**: 사고/실주행 정산 후 차량의 최종 매매시장 가치는 **{evaluated_car_value:,}만 원**입니다. 목표 상사 마진 {target_margin}만 원과 부대비용을 확보하려면 경매장 요율을 계산해 **[{max_bid_price:,}만 원]** 이하로 낙찰받아야 안전합니다.")