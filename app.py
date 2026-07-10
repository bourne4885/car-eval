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

    def calculate_accident_penalty(self, selected_accident, base_points_dict, rank_coef_dict):
        """[제22조] 사고수리이력 루트(√) 공식 기반 감가액 연산"""
        if not selected_accident:
            return 0, 0, {}

        total_gamma_coef = 0.0
        max_rank_coef = 0.0
        detail_logs = {}

        for part, data in selected_accident.items():
            rank = data["rank"]
            status = data["status"]
            
            base_coef = base_points_dict.get(rank, 0) / 100.0 
            repair_coef = 1.0 if status == "교환(X)" else 0.5
            
            current_part_gamma = base_coef * repair_coef
            total_gamma_coef += current_part_gamma
            
            r_coef = rank_coef_dict.get(rank, 1.0)
            if r_coef > max_rank_coef:
                max_rank_coef = r_coef
                
            detail_logs[part] = f"사고 감가계수: {current_part_gamma:.3f} (랭크적용계수: {r_coef})"

        # 예외 규칙: 1랭크 딱 1곳 교환만 단독 존재할 때 50% 감면
        if len(selected_accident) == 1:
            only_part = list(selected_accident.values())[0]
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
st.caption("사고 수리는 기준서 공식으로 엄격하게 계산하고, 도색이 필요한 부위는 별도로 판수를 세어 감가합니다.")

# 계수 테이블 선언
base_points_table = {"1랭크": 15, "2랭크": 30, "A랭크": 50, "B랭크": 80, "C랭크": 120}
rank_coef_table = {"1랭크": 1.0, "2랭크": 1.4, "A랭크": 1.6, "B랭크": 1.8, "C랭크": 2.0}

# 전체 차량 부위 정의
all_car_parts = {
    "🔻 외판 1랭크 부위": {
        "후드": "1랭크", "프론트 펜더(좌)": "1랭크", "프론트 펜더(우)": "1랭크",
        "앞도어(좌)": "1랭크", "앞도어(우)": "1랭크", "뒷도어(좌)": "1랭크", "뒷도어(우)": "1랭크",
        "트렁크 리드": "1랭크", "라디에이터 서포트": "1랭크"
    },
    "🔻 외판 2랭크 부위": {
        "쿼터 패널(좌)": "2랭크", "쿼터 패널(우)": "2랭크", "루프 패널": "2랭크", 
        "사이드 실 패널(좌)": "2랭크", "사이드 실 패널(우)": "2랭크"
    },
    "🔺 주요골격 A랭크 부위": {
        "프론트 패널": "A랭크", "크로스 멤버": "A랭크", "인사이드 패널(좌)": "A랭크", "인사이드 패널(우)": "A랭크", "트렁크 플로어 패널": "A랭크", "리어 패널": "A랭크"
    },
    "🔺 주요골격 B랭크 부위": {
        "사이드 멤버(좌)": "B랭크", "사이드 멤버(우)": "B랭크", "휠 하우스(좌)": "B랭크", "휠 하우스(우)": "B랭크", "필러 패널(좌)": "B랭크", "필러 패널(우)": "B랭크"
    }
}

# --------------------------------------------------
# 섹션 1: 차량 조건 및 경매 목표 설정
# --------------------------------------------------
st.header("📝 1. 차량 기본 정보 및 입찰 목표 세팅")
col1, col2, col3 = st.columns(3)

with col1:
    origin = st.selectbox("차량 구분", ["국산", "수입"])
    displacement = st.number_input("배기량 (cc)", min_value=100, max_value=10000, value=3500, step=100)
    base_price = st.number_input("무사고 소매 가액 (만원)", min_value=0, value=3000, step=50)

with col2:
    reg_year = st.number_input("최초등록년도 (연도)", min_value=2000, max_value=2026, value=2023)
    mileage = st.number_input("실제 주행거리 (km)", min_value=0, max_value=1000000, value=50000, step=1000)

with col3:
    target_margin = st.number_input("확보하고 싶은 경매 매입 마진 (만원)", min_value=0, value=150, step=10)
    fixed_cost = st.number_input("기타 부대비용 (상사이전/탁송료 등) (만원)", min_value=0, value=60)
    paint_unit_cost = st.number_input("🎨 판당 도색/상품화 단가 (만원)", min_value=0, value=15, step=1)
    auction_fee_rate = st.slider("경매장 낙찰 수수료율 (%)", min_value=0.0, max_value=5.0, value=2.2, step=0.1)

st.markdown("---")

# --------------------------------------------------
# 섹션 2: 사고수리 체크 항목 (교환 / 판금)
# --------------------------------------------------
st.header("🛠️ 2. 사고수리 체크 항목 (기준서 공식 감가 대상)")
st.caption("교환(X) 또는 판금/용접(W) 이력이 있는 부위만 체크해 주세요. (중복 선택 가능)")

selected_accident = {}
for section_title, parts in all_car_parts.items():
    st.markdown(f"##### {section_title}")
    part_items = list(parts.items())
    for i in range(0, len(part_items), 4):
        chunk = part_items[i:i+4]
        cols = st.columns(4)
        for idx, (part_name, rank) in enumerate(chunk):
            with cols[idx]:
                accident_status = st.selectbox(f"{part_name} 수리", ["정상", "교환(X)", "판금/용접(W)"], key=f"acc_{part_name}")
                if accident_status != "정상":
                    selected_accident[part_name] = {"rank": rank, "status": accident_status}

st.markdown("---")

# --------------------------------------------------
# 섹션 3: 도색 필요부위 체크 항목 (판수 자동 계산)
# --------------------------------------------------
st.header("🎨 3. 도색 필요부위 체크 항목 (실전 상품화비 대상)")
st.caption("외관상 스크래치, 칠 까짐, 재도색이 필요하여 현장에서 도색 비용을 차감해야 하는 부위들을 체크해 주세요.")

selected_paint_parts = []
for section_title, parts in all_car_parts.items():
    # 주요골격 내부 부위는 도색에서 제외하고 외판 1,2랭크만 노출시킴
    if "골격" in section_title:
        continue
        
    st.markdown(f"##### {section_title}")
    part_items = list(parts.items())
    for i in range(0, len(part_items), 4):
        chunk = part_items[i:i+4]
        cols = st.columns(4)
        for idx, (part_name, rank) in enumerate(chunk):
            with cols[idx]:
                need_paint = st.checkbox(f"{part_name} 도색 필요", key=f"paint_{part_name}")
                if need_paint:
                    selected_paint_parts.append(part_name)

st.markdown("---")

# --------------------------------------------------
# 섹션 4: 최종 연산 및 마지노선 도출
# --------------------------------------------------
if st.button("📊 경매 입찰가 최종 산출하기", type="primary", use_container_width=True):
    is_imp = True if origin == "수입" else False
    
    engine = AuctionEvaluator(is_import=is_imp, displacement=displacement, reg_year=reg_year, reg_month=1, mileage=mileage, base_price_manwon=base_price)
    tier, tier_coef = engine.get_tier_and_coefficient()
    u_year, u_month, age_coef = engine.get_usage_period_and_coefficient()

    # 1. 2번 섹션 데이터 -> 기준서 제22조 사고 감가액 연산
    accident_penalty, total_coef, logs = engine.calculate_accident_penalty(selected_accident, base_points_table, rank_coef_table)
    
    # 2. 3번 섹션 데이터 -> 도장 판수 기반 비용 연산
    paint_count = len(selected_paint_parts)
    paint_penalty = paint_count * paint_unit_cost
    
    # 3. 주행거리 초과 정산
    std_mileage = int(u_month * 1.66 * 1000)
    mile_diff = std_mileage - mileage
    mile_penalty = max(0, int(-mile_diff / 1000) * 2) 

    # 4. 차량의 최종 가치 및 최대 입찰가 도출
    total_reduction = accident_penalty + paint_penalty + mile_penalty
    evaluated_car_value = max(0, base_price - total_reduction)

    fee_factor = 1 + (auction_fee_rate / 100)
    max_bid_price = (evaluated_car_value - fixed_cost - target_margin) / fee_factor
    max_bid_price = max(0, round(max_bid_price))
    
    estimated_fee = round(max_bid_price * (auction_fee_rate / 100))

    # 결과 리포트 대시보드
    st.header("🎯 실전 경매 입찰 전략 분석 보고서")
    
    if logs:
        st.subheader("📋 [2번 항목] 기준서 사고이력 연산 로그")
        for p_name, log_txt in logs.items():
            st.text(f"  • {p_name} ──> {log_txt}")
        st.info(f"💡 공식 대입 정보: 총 사고감가계수합 = {total_coef:.3f}")

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="🏁 경매장 최고 입찰 마지노선 (Max Bid)", value=f"{max_bid_price:,} 만원")
        st.info(f"🎨 [3번 항목] 선택한 도색 필요 부위: 총 {paint_count}판")
        if paint_count > 0:
            st.caption(f"📍 도색 대상: {', '.join(selected_paint_parts)}")

    with res_col2:
        st.metric(label="📉 종합 감가 및 상품화비 총합", value=f"-{round(total_reduction):,} 만원")
        st.text(f"  • 2번 섹션 기준서 사고 감가: {accident_penalty:,} 만원")
        st.text(f"  • 3번 섹션 자동 도색비 ({paint_count}판 × {paint_unit_cost}만): {paint_penalty:,} 만원")
        st.text(f"  • 주행거리 초과 페널티: {mile_penalty:,} 만원")
        st.text(f"  • 경매장 예상 낙찰 수수료: {estimated_fee:,} 만원")

    st.markdown("---")
    st.warning(f"💡 **최종 가이드**: 도색 {paint_count}판 비용({paint_penalty}만 원)과 기준서 사고 감가액이 모두 털린 차량의 순수 잔존 가치는 **{evaluated_car_value:,}만 원**입니다. 경매 입찰 시 **[{max_bid_price:,}만 원]**을 넘기지 않아야 손해를 보지 않습니다.")