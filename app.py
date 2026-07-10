import streamlit as st
import math

# ==========================================
# 1. 통합 가격 산출 엔진 (제22조 공식 + 도장 판수 정산)
# ==========================================
class AuctionEvaluator:
    def __init__(self, is_import: bool, displacement: int, reg_year: int, reg_month: int, mileage: int, base_price_manwon: int):
        self.is_import = is_import
        self.displacement = displacement
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.mileage = mileage
        self.base_price_manwon = base_price_manwon
        
        self.current_year = 2026
        self.current_month = 7

    def get_tier_and_coefficient(self):
        """[제7조] 승용형 자동차 등급 및 등급계수 산출"""
        if self.displacement >= 3600: tier = "특C"
        elif self.displacement >= 2900: tier = "특B"
        elif self.displacement >= 2400: tier = "특A"
        elif self.displacement >= 2100: tier = "I"
        elif self.displacement >= 1700: tier = "II"
        elif self.displacement >= 1300: tier = "III"
        elif self.displacement >= 1100: tier = "IV"
        else: tier = "경"

        coefficients = {
            "국산": {"특C": 2.2, "특B": 1.8, "특A": 1.5, "I": 1.4, "II": 1.2, "III": 1.0, "IV": 0.9, "경": 0.8},
            "수입": {"특C": 2.7, "특B": 2.5, "특A": 2.0, "I": 1.7, "II": 1.4, "III": 1.2, "IV": 1.1, "경": 1.0}
        }
        return tier, coefficients["수입" if self.is_import else "국산"][tier]

    def get_usage_period_and_coefficient(self):
        """[제8조] 사용년 계수 산출"""
        usage_years = self.current_year - self.reg_year
        remaining_months = self.current_month - self.reg_month
        usage_months = (usage_years * 12) + remaining_months
        
        if not self.is_import:
            age_coef = 1.0 if usage_years <= 2 else (0.9 if usage_years == 3 else (0.8 if usage_years == 4 else 0.7))
        else:
            age_coef = 1.0 if usage_years <= 2 else (0.9 if usage_years in [3, 4] else (0.8 if usage_years in [5, 6] else 0.7))
        return usage_years, usage_months, age_coef

    def calculate_accident_penalty(self, selected_damage, base_points_dict, rank_coef_dict):
        """[제22조] 사고수리이력 루트(√) 공식 기반 감가액 연산"""
        if not selected_damage:
            return 0, 0, {}

        total_gamma_coef = 0.0
        max_rank_coef = 0.0
        detail_logs = {}

        for part, data in selected_damage.items():
            rank = data["rank"]
            status = data["status"]
            
            # 사고이력(교환/판금)인 경우에만 계수 산정
            if status in ["교환(X)", "판금/용접(W)"]:
                base_coef = base_points_dict.get(rank, 0) / 100.0 
                repair_coef = 1.0 if status == "교환(X)" else 0.5
                
                current_part_gamma = base_coef * repair_coef
                total_gamma_coef += current_part_gamma
                
                r_coef = rank_coef_dict.get(rank, 1.0)
                if r_coef > max_rank_coef:
                    max_rank_coef = r_coef
                    
                detail_logs[part] = f"사고 감가계수: {current_part_gamma:.3f} (랭크적용계수: {r_coef})"

        # 예외 규칙: 1랭크 딱 1곳 교환만 단독 존재할 때 50% 감면
        if len([d for d in selected_damage.values() if d["status"] in ["교환(X)", "판금/용접(W)"]]) == 1:
            only_part = [d for d in selected_damage.values() if d["status"] in ["교환(X)", "판금/용접(W)"]][0]
            if only_part["rank"] == "1랭크" and only_part["status"] == "교환(X)":
                total_gamma_coef = total_gamma_coef * 0.5

        if total_gamma_coef == 0:
            return 0, 0, detail_logs

        inside_sqrt = self.base_price_manwon * total_gamma_coef
        final_accident_penalty = (math.sqrt(inside_sqrt) / 4.8) * max_rank_coef
        
        return round(final_accident_penalty, 2), total_gamma_coef, detail_logs

# ==========================================
# 2. Streamlit 웹 UI 화면 구성
# ==========================================
st.set_page_config(page_title="기준서 기반 경매 입찰산출 시스템", page_icon="⚖️", layout="wide")

st.title("⚖️ 기준서 연산 기반 중고차 경매 입찰가 산출기 (2026)")
st.caption("사고 수리는 기준서 공식으로, 도색(P)이 필요한 부위는 판수를 자동 계산하여 경매가에 반영합니다.")

# 계수 테이블 선언
base_points_table = {"1랭크": 15, "2랭크": 30, "A랭크": 50, "B랭크": 80, "C랭크": 120}
rank_coef_table = {"1랭크": 1.0, "2랭크": 1.4, "A랭크": 1.6, "B랭크": 1.8, "C랭크": 2.0}

# 섹션 1: 차량 조건 및 경매 목표 설정
st.header("📝 1. 차량 기본 정보 및 입찰 목표 세팅")
col1, col2, col3 = st.columns(3)

with col1:
    origin = st.selectbox("차량 구분", ["국산", "수입"])
    displacement = st.number_input("배기량 (cc)", min_value=100, max_value=10000, value=3500, step=100)
    base_price = st.number_input("무사고 소매 기준가격 (만원)", min_value=0, value=3000, step=50)

with col2:
    reg_year = st.number_input("최초등록년도 (연도)", min_value=2000, max_value=2026, value=2023)
    mileage = st.number_input("실제 주행거리 (km)", min_value=0, max_value=1000000, value=50000, step=1000)

with col3:
    target_margin = st.number_input("확보하고 싶은 경매 매입 마진 (만원)", min_value=0, value=150, step=10)
    fixed_cost = st.number_input("기타 부대비용 (상사이전/탁송료 등) (만원)", min_value=0, value=60)
    # 🌟 판당 도색 비용을 유연하게 조절할 수 있는 슬라이더/입력칸 배치
    paint_unit_cost = st.number_input("🎨 판당 도색/상품화 단가 (만원)", min_value=0, value=15, step=1, help="경매 차량을 가져와서 도색 한 판 할 때 들어가는 단가")
    auction_fee_rate = st.slider("경매장 낙찰 수수료율 (%)", min_value=0.0, max_value=5.0, value=2.2, step=0.1)

st.markdown("---")

# 섹션 2: 사고수리 및 수리필요 평가
st.header("🚘 2. 진단 대상 차량 사고수리 및 도색 필요 부위 체크")
categorized_parts = {
    "🔻 외판 1랭크 부위": {
        "후드": "1랭크", "프론트 펜더(운전석/좌)": "1랭크", "프론트 펜더(조수석/우)": "1랭크",
        "앞도어(운전석/좌)": "1랭크", "앞도어(조수석/우)": "1랭크", "뒷도어(운전석/좌)": "1랭크", "뒷도어(조수석/우)": "1랭크",
        "트렁크 리드": "1랭크", "라디에이터 서포트(볼트체결)": "1랭크"
    },
    "🔻 외판 2랭크 부위": {
        "쿼터 패널(운전석/좌)": "2랭크", "쿼터 패널(조수석/우)": "2랭크", "루프 패널": "2랭크", 
        "사이드 실 패널(운전석/좌)": "2랭크", "사이드 실 패널(조수석/우)": "2랭크"
    },
    "🔺 주요골격 A랭크 부위": {
        "프론트 패널": "A랭크", "크로스 멤버(용접부품)": "A랭크", "인사이드 패널(운전석/좌)": "A랭크", "인사이드 패널(조수석/우)": "A랭크", "트렁크 플로어 패널": "A랭크", "리어 패널": "A랭크"
    }
}

selected_damage = {}
for section_title, parts in categorized_parts.items():
    st.markdown(f"#### {section_title}")
    part_items = list(parts.items())
    for i in range(0, len(part_items), 4):
        chunk = part_items[i:i+4]
        cols = st.columns(4)
        for idx, (part_name, rank) in enumerate(chunk):
            with cols[idx]:
                status = st.selectbox(part_name, ["정상", "교환(X)", "판금/용접(W)", "도장필요(P)"], key=f"status_{part_name}")
                if status != "정상":
                    selected_damage[part_name] = {"rank": rank, "status": status}

st.markdown("---")

# 섹션 3: 최종 연산 프로세스
if st.button("📊 경매 입찰가 최종 산출하기", type="primary", use_container_width=True):
    is_imp = True if origin == "수입" else False
    
    engine = AuctionEvaluator(is_import=is_imp, displacement=displacement, reg_year=reg_year, reg_month=1, mileage=mileage, base_price_manwon=base_price)
    tier, tier_coef = engine.get_tier_and_coefficient()
    u_year, u_month, age_coef = engine.get_usage_period_and_coefficient()

    # 1. 기준서 제22조 사고 감가액 도출
    accident_penalty, total_coef, logs = engine.calculate_accident_penalty(selected_damage, base_points_table, rank_coef_table)
    
    # 2. 🌟 도장필요(P)로 선택된 총 판수 및 부위 자동 계산
    paint_parts = [part for part, d in selected_damage.items() if d["status"] == "도장필요(P)"]
    paint_count = len(paint_parts)
    paint_penalty = paint_count * paint_unit_cost  # [자동 판수 계산된 수] * [화면 입력 단가]
    
    # 3. 주행거리 초과 건 정산
    std_mileage = int(u_month * 1.66 * 1000)
    mile_diff = std_mileage - mileage
    mile_penalty = max(0, int(-mile_diff / 1000) * 2) 

    # 4. 차량의 총 평가 가치 및 최고 입찰 마지노선 산출
    total_reduction = accident_penalty + paint_penalty + mile_penalty
    evaluated_car_value = max(0, base_price - total_reduction)

    fee_factor = 1 + (auction_fee_rate / 100)
    max_bid_price = (evaluated_car_value - fixed_cost - target_margin) / fee_factor
    max_bid_price = max(0, round(max_bid_price))
    
    estimated_fee = round(max_bid_price * (auction_fee_rate / 100))

    # 결과 리포트 대시보드
    st.header("🎯 실전 경매 입찰 전략 분석 보고서")
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🏁 경매장 최고 입찰 마지노선 (Max Bid)", value=f"{max_bid_price:,} 만원")
        st.info(f"🎨 선택한 도색 필요 부위: 총 {paint_count}판")
        if paint_count > 0:
            st.caption(f"📍 도색 부위: {', '.join(paint_parts)}")

    with res_col2:
        st.metric(label="📉 종합 감가 및 상품화비 총합", value=f"-{round(total_reduction):,} 만원")
        st.text(f"  • 기준서 공식 사고 감가: {accident_penalty:,} 만원")
        st.text(f"  • 🎨 자동 계산 도색비 ({paint_count}판 × {paint_unit_cost}만): {paint_penalty:,} 만원")
        st.text(f"  • 주행거리 초과 페널티: {mile_penalty:,} 만원")
        st.text(f"  • 경매장 예상 낙찰 수수료: {estimated_fee:,} 만원")

    st.markdown("---")
    st.warning(f"💡 **최종 가이드**: 도색비 {paint_penalty}만 원을 포함해 총 상품화 및 감가가 적용된 차량 가치는 **{evaluated_car_value:,}만 원**입니다. 목표 마진을 챙기기 위해 경매장 패들은 **[{max_bid_price:,}만 원]** 까지만 당기셔야 합니다!")