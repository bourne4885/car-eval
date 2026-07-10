import streamlit as st
import math

# ==========================================
# 1. 자동차 진단평가 가격 계산 엔진 (백엔드)
# ==========================================
class CarEvaluator:
    def __init__(self, is_import: bool, displacement: int, reg_year: int, reg_month: int, mileage: int, base_price_manwon: int):
        self.is_import = is_import
        self.displacement = displacement
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.mileage = mileage
        self.base_price_manwon = base_price_manwon
        
        self.current_year = 2026
        self.current_month = 6

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

# ==========================================
# 2. Streamlit 웹 UI 화면 구성 (프런트엔드)
# ==========================================
st.set_page_config(page_title="자동차진단평가 시스템", page_icon="🚗", layout="wide")

st.title("🚗 자동차진단평가 가치산출 시스템 (2026 검정용)")
st.caption("Streamlit Web Cloud Version")

# 랭크별 기본 감점 점수 (기준서 제22조 반영)
rank_base_points = {
    "외판1랭크": 15,
    "외판2랭크": 30,
    "주요골격A": 50,
    "주요골격B": 80,
    "주요골격C": 120
}

# 폼 구성: 차량 기본 데이터 입력
st.header("📝 1. 차량 기본 데이터 입력")
col1, col2, col3 = st.columns(3)

with col1:
    origin = st.selectbox("차량 구분", ["국산", "수입"])
    displacement = st.number_input("배기량 (cc)", min_value=100, max_value=10000, value=2000, step=100)

with col2:
    reg_year = st.number_input("최초등록년도 (연도)", min_value=2000, max_value=2026, value=2023)
    mileage = st.number_input("실제 주행거리 (km)", min_value=0, max_value=1000000, value=50000, step=1000)

with col3:
    base_price = st.number_input("기준가격 (만원)", min_value=0, max_value=100000, value=3000, step=50)

st.markdown("---")

# 폼 구성: 웹형 상태 표시도 입력란
st.header("🚘 2. 사고수리 및 수리필요 부위 선택")
st.info("💡 각 부위별로 발생한 사고 이력이나 수리 필요 상태를 선택해 주세요.")

# 평가 대상 부위 리스트 정의 (기준서 제25p 참고)
car_parts = {
    "후드": "외판1랭크",
    "프론트 펜더": "외판1랭크",
    "앞도어": "외판1랭크",
    "트렁크 리드": "외판1랭크",
    "쿼터 패널(리어펜더)": "외판2랭크",
    "사이드 멤버": "주요골격B",
    "휠 하우스": "주요골격B"
}

selected_damage = {}

# 웹 화면에 부위별 선택 라디오 버튼들을 깔끔하게 배치
part_cols = st.columns(len(car_parts))
for idx, (part_name, rank) in enumerate(car_parts.items()):
    with part_cols[idx]:
        st.subheader(part_name)
        st.caption(f"({rank})")
        status = st.radio(
            f"{part_name} 상태",
            ["정상", "교환(X)", "판금/용접(W)", "도장필요(P)"],
            key=f"status_{part_name}",
            label_visibility="collapsed"
        )
        if status != "정상":
            selected_damage[part_name] = {"rank": rank, "status": status}

st.markdown("---")

# 3. 계산하기 버튼 및 결과 도출
if st.button("💰 최종 진단평가가격 산출하기", type="primary", use_container_width=True):
    is_imp = True if origin == "수입" else False
    
    # 계산 엔진 가동
    engine = CarEvaluator(is_import=is_imp, displacement=displacement, reg_year=reg_year, reg_month=1, mileage=mileage, base_price_manwon=base_price)
    tier, tier_coef = engine.get_tier_and_coefficient()
    u_year, u_month, age_coef = engine.get_usage_period_and_coefficient()

    # 모색도 기반 감점 정산
    total_penalty_points = 0
    st.subheader("📋 선택된 실시간 이력 감점 내역")
    
    if not selected_damage:
        st.success("• 선택된 사고/수리 이력이 없습니다. (무사고 차량)")
    else:
        for part, data in selected_damage.items():
            rank = data["rank"]
            status = data["status"]
            base_pt = rank_base_points.get(rank, 0)
            
            # 수리 형태에 따른 기준서 보정식 적용
            if status == "판금/용접(W)":
                base_pt = math.ceil(base_pt * 0.5)
            elif status == "도장필요(P)":
                base_pt = 5 # 수리필요 항목 임시 배점
                
            total_penalty_points += base_pt
            st.warning(f"• **{part}** ({rank}) ──> 상태: [{status}] / **-{base_pt}점** 감점")

    # 주행거리 표준치 비교 연산
    std_mileage = int(u_month * 1.66 * 1000)
    mile_diff = std_mileage - mileage
    mile_points = int(mile_diff / 1000)
    
    if mile_points < 0:
        total_penalty_points += abs(mile_points)
        st.error(f"• **주행거리 과다**: 표준 대비 초과로 인해 **-{abs(mile_points)}점** 추가 감점")

    # 최종 가치 정산
    penalty_amount = total_penalty_points
    final_price = base_price - penalty_amount
    if final_price < 0: final_price = 0

    # 결과 리포트 대시보드 출력
    st.markdown("---")
    st.header("🎯 최종 진단평가 판정 레포트")
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="차량 등급 및 계수", value=f"{tier} 등급", delta=f"계수: {tier_coef}")
        st.metric(label="사용 연수 및 계수", value=f"{u_year}년차", delta=f"계수: {age_coef}")
        st.text(f"표준 주행거리: {std_mileage:,} km")
        st.text(f"실제 주행거리: {mileage:,} km")

    with res_col2:
        st.metric(label="종합 감점 금액", value=f"-{penalty_amount:,} 만원")
        st.headline = st.metric(label="🏁 최종 진단평가 가격", value=f"{final_price:,} 만원")