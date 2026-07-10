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

# ==========================================
# 2. Streamlit 웹 UI 화면 구성 (프런트엔드)
# ==========================================
st.set_page_config(page_title="자동차진단평가 가치산출 시스템", page_icon="🚗", layout="wide")

st.title("🚗 자동차진단평가 가치산출 시스템 (2026 검정용)")
st.caption("운전석(좌) / 조수석(우) 위치 구분 완벽 세분화 버전")

# 랭크별 기본 감점 점수 기준 정의
rank_base_points = {
    "1랭크": 15,
    "2랭크": 30,
    "A랭크": 50,
    "B랭크": 80,
    "C랭크": 120
}

# 1. 차량 기본 정보 입력 섹션
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

# 2. 사고수리 및 수리필요 평가 섹션 (운전석/조수석 세분화)
st.header("🚘 2. 사고수리 및 수리필요 부위 선택 (좌우 독립 분류)")
st.info("💡 랭크 분류표를 기반으로 운전석 측(좌)과 조수석 측(우)을 분리하여 정밀 진단이 가능하도록 확장했습니다.")

# 좌우 구분을 반영한 데이터 세팅
categorized_parts = {
    "🔻 외판 1랭크 부위": {
        "후드": "1랭크", 
        "프론트 펜더(운전석/좌)": "1랭크", "프론트 펜더(조수석/우)": "1랭크",
        "앞도어(운전석/좌)": "1랭크", "앞도어(조수석/우)": "1랭크",
        "뒷도어(운전석/좌)": "1랭크", "뒷도어(조수석/우)": "1랭크",
        "트렁크 리드": "1랭크", "라디에이터 서포트(볼트체결)": "1랭크"
    },
    "🔻 외판 2랭크 부위": {
        "쿼터 패널(운전석/좌)": "2랭크", "쿼터 패널(조수석/우)": "2랭크", 
        "루프 패널": "2랭크", 
        "사이드 실 패널(운전석/좌)": "2랭크", "사이드 실 패널(조수석/우)": "2랭크"
    },
    "🔺 주요골격 A랭크 부위": {
        "프론트 패널": "A랭크", "크로스 멤버(용접부품)": "A랭크", 
        "인사이드 패널(운전석/좌)": "A랭크", "인사이드 패널(조수석/우)": "A랭크", 
        "트렁크 플로어 패널": "A랭크", "리어 패널": "A랭크"
    },
    "🔺 주요골격 B랭크 부위": {
        "사이드 멤버(운전석/좌)": "B랭크", "사이드 멤버(조수석/우)": "B랭크", 
        "휠 하우스(운전석/좌)": "B랭크", "휠 하우스(조수석/우)": "B랭크", 
        "필러 패널(운전석/좌)": "B랭크", "필러 패널(조수석/우)": "B랭크", 
        "패키지 트레이": "B랭크"
    },
    "🔺 주요골격 C랭크 부위": {
        "대쉬 패널": "C랭크", "플로어 패널": "C랭크"
    }
}

selected_damage = {}

# 화면 레이아웃 스크롤 분산을 위해 각 섹션별 레이아웃 폼 구축
for section_title, parts in categorized_parts.items():
    st.markdown(f"#### {section_title}")
    
    # 항목이 많으므로 한 줄에 최대 4개씩 분할 배치
    part_items = list(parts.items())
    chunk_size = 4
    for i in range(0, len(part_items), chunk_size):
        chunk = part_items[i:i+chunk_size]
        cols = st.columns(4)
        for idx, (part_name, rank) in enumerate(chunk):
            with cols[idx]:
                status = st.selectbox(
                    part_name,
                    ["정상", "교환(X)", "판금/용접(W)", "도장필요(P)"],
                    key=f"status_{part_name}"
                )
                if status != "정상":
                    selected_damage[part_name] = {"rank": rank, "status": status}
    st.markdown(" ")

st.markdown("---")

# 3. 계산 및 결과 출력
if st.button("💰 최종 진단평가가격 산출하기", type="primary", use_container_width=True):
    is_imp = True if origin == "수입" else False
    
    # 계산 백엔드 엔진 가동
    engine = CarEvaluator(is_import=is_imp, displacement=displacement, reg_year=reg_year, reg_month=1, mileage=mileage, base_price_manwon=base_price)
    tier, tier_coef = engine.get_tier_and_coefficient()
    u_year, u_month, age_coef = engine.get_usage_period_and_coefficient()

    total_penalty_points = 0
    st.subheader("📋 실시간 진단점수 산정 내역")
    
    # 입력된 대시보드 상태값 기반 감점 정산
    if not selected_damage:
        st.success("• 감점 이력이 없습니다. (완전 무사고 차량)")
    else:
        for part, data in selected_damage.items():
            rank = data["rank"]
            status = data["status"]
            base_pt = rank_base_points.get(rank, 0)
            
            if status == "판금/용접(W)":
                base_pt = math.ceil(base_pt * 0.5)
            elif status == "도장필요(P)":
                base_pt = 5
                
            total_penalty_points += base_pt
            st.warning(f"• **{part}** ({rank}) ──> 상태: [{status}] / **-{base_pt}점** 감점")

    # 주행거리 과다 감점 연동
    std_mileage = int(u_month * 1.66 * 1000)
    mile_diff = std_mileage - mileage
    mile_points = int(mile_diff / 1000)
    
    if mile_points < 0:
        total_penalty_points += abs(mile_points)
        st.error(f"• **주행거리 초과**: 표준 대비 과다 주행으로 인해 **-{abs(mile_points)}점** 추가 감점")

    # 최종 금액 산출
    penalty_amount = total_penalty_points
    final_price = base_price - penalty_amount
    if final_price < 0: final_price = 0

    # 결과 리포트 대시보드 출력
    st.markdown("---")
    st.header("🎯 최종 진단평가 판정 레포트")
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="차량 종합 등급", value=f"{tier} 등급", delta=f"등급계수: {tier_coef}")
        st.metric(label="사용 연수 결과", value=f"{u_year}년차 적용", delta=f"사용년 계수: {age_coef}")
        st.text(f"📊 표준 기준 주행거리: {std_mileage:,} km")
        st.text(f"📊 차량 실제 주행거리: {mileage:,} km")

    with res_col2:
        st.metric(label="종합 감점 금액 합계", value=f"-{penalty_amount:,} 만원")
        st.metric(label="🏁 최종 산출 진단평가 가격", value=f"{final_price:,} 만원")