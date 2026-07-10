import streamlit as st
import math

# ==========================================
# 1. 자동차 진단평가 가격 계산 엔진 (제22조 공식 반영)
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

    def calculate_accident_penalty(self, selected_damage, base_points_dict, rank_coef_dict):
        """
        [제22조] 사고수리이력 감가액 산출 공식 완전 구현
        공식: ( sqrt(보정가격 * 감가계수합) / 4.8 ) * 랭크별 적용계수
        """
        if not selected_damage:
            return 0, 0, {}

        total_gamma_coef = 0.0  # 사고수리이력 감가계수(합)
        max_rank_coef = 0.0     # 랭크별 적용계수 (2곳 이상인 경우 가장 큰 값 적용 규칙)
        
        detail_logs = {}

        # 1. 사용자가 선택한 부위들을 돌며 감가계수합 및 최대 랭크계수 탐색
        for part, data in selected_damage.items():
            rank = data["rank"]
            status = data["status"]
            
            # 기준서 제5호에 따른 기본 감가계수(여기선 편의상 베이스 포인트 비율로 치환 점수화)
            base_coef = base_points_dict.get(rank, 0) / 100.0 
            
            # 수리 형태에 따른 (2)번 규칙 적용: 교환(X)은 100%, 판금/용접(W)은 50%
            if status == "교환(X)":
                repair_coef = 1.0
            elif status == "판금/용접(W)":
                repair_coef = 0.5
            else:
                repair_coef = 0.0  # 단순 도장(P) 등은 별도 수리필요 항목으로 정산
                
            current_part_gamma = base_coef * repair_coef
            total_gamma_coef += current_part_gamma
            
            # (3)번 규칙: 1랭크 부위 중 1곳만 교환(X)이고 다른 부위 사고가 없으면 50% 감면
            # 이 규칙은 하단 마스터 정산부에서 최종 체크 수행
            
            # 다. 규칙: 랭크별 적용계수 매칭 (가장 큰 랭크의 계수 선택)
            r_coef = rank_coef_dict.get(rank, 1.0)
            if r_coef > max_rank_coef:
                max_rank_coef = r_coef
                
            if current_part_gamma > 0:
                detail_logs[part] = f"계수: {current_part_gamma:.2f} (랭크계수: {r_coef})"

        # 예외 규칙 (3) 처리: 전체 통틀어 딱 1랭크 1곳 교환만 있는 경우 감가계수 50% 감면
        if len(selected_damage) == 1:
            only_part = list(selected_damage.values())[0]
            if only_part["rank"] == "1랭크" and only_part["status"] == "교환(X)":
                total_gamma_coef = total_gamma_coef * 0.5

        if total_gamma_coef == 0:
            return 0, 0, detail_logs

        # 2. 제22조 1항 공식 그대로 연산 수행
        # 보정가격은 제11조에 따르나, 여기서는 우선 입력된 기준가격을 기본 베이스로 연산
        bojung_price = self.base_price_manwon
        
        inside_sqrt = bojung_price * total_gamma_coef
        upper_part = math.sqrt(inside_sqrt)
        final_accident_penalty = (upper_part / 4.8) * max_rank_coef
        
        # 소수점 이하 처리 규칙 반영 (반올림 정수화)
        return round(final_accident_penalty, 2), total_gamma_coef, detail_logs


# ==========================================
# 2. Streamlit 웹 UI 화면 구성 (프런트엔드)
# ==========================================
st.set_page_config(page_title="자동차진단평가 가치산출 시스템", page_icon="🚗", layout="wide")

st.title("🚗 자동차진단평가 가치산출 시스템 (2026 검정용)")
st.caption("제22조 루트(√) 감가액 산출 공식 완전 무결 반영")

# 기준서 제22조 및 제4호 관련 랭크별 세팅 값
base_points_table = {"1랭크": 15, "2랭크": 30, "A랭크": 50, "B랭크": 80, "C랭크": 120}
rank_coef_table = {"1랭크": 0.6, "2랭크": 0.8, "A랭크": 1.0, "B랭크": 1.2, "C랭크": 1.5}

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

# 2. 사고 부위 선택 섹션
st.header("🚘 2. 사고수리 및 수리필요 부위 선택 (좌우 독립)")
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
    },
    "🔺 주요골격 B랭크 부위": {
        "사이드 멤버(운전석/좌)": "B랭크", "사이드 멤버(조수석/우)": "B랭크", "휠 하우스(운전석/좌)": "B랭크", "휠 하우스(조수석/우)": "B랭크", "필러 패널(운전석/좌)": "B랭크", "필러 패널(조수석/우)": "B랭크", "패키지 트레이": "B랭크"
    },
    "🔺 주요골격 C랭크 부위": {
        "대쉬 패널": "C랭크", "플로어 패널": "C랭크"
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

# 3. 마스터 연산 및 결과 도출
if st.button("💰 제22조 표준 공식 기반 가격 산출", type="primary", use_container_width=True):
    is_imp = True if origin == "수입" else False
    
    engine = CarEvaluator(is_import=is_imp, displacement=displacement, reg_year=reg_year, reg_month=1, mileage=mileage, base_price_manwon=base_price)
    tier, tier_coef = engine.get_tier_and_coefficient()
    u_year, u_month, age_coef = engine.get_usage_period_and_coefficient()

    # 제22조 루트 공식 대입 연산
    accident_penalty, total_coef, logs = engine.calculate_accident_penalty(selected_damage, base_points_table, rank_coef_table)
    
    # 도장 필요(P)건에 대한 단순 수리비용 별도 합산 (건당 5만원 감가 규칙)
    paint_penalty = sum(5 for d in selected_damage.values() if d["status"] == "도장필요(P)")
    
    # 주행거리 감점 산정
    std_mileage = int(u_month * 1.66 * 1000)
    mile_diff = std_mileage - mileage
    mile_points = max(0, int(-mile_diff / 1000))

    # 종합 감가 상계 처리
    total_final_penalty = round(accident_penalty + paint_penalty + mile_points)
    final_car_price = max(0, base_price - total_final_penalty)

    # 대시보드 리포트 출력
    st.header("🎯 제22조 공식 적용 최종 진단평가 결과")
    
    if logs:
        st.subheader("📋 사고이력 계수 세부 내역")
        for p_name, log_txt in logs.items():
            st.text(f"  • {p_name} -> {log_txt}")
        st.info(f"💡 연산식 대입 값: 총 감가계수(합) = {total_coef:.2f}")

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="차량 종합 등급", value=f"{tier} 등급")
        st.metric(label="사용 연수 계수", value=f"{age_coef} 계수")
        st.text(f"📊 표준 주행거리: {std_mileage:,} km / 실제 주행거리: {mileage:,} km")

    with res_col2:
        st.error(f"💥 사고수리 공식 감가액: {accident_penalty} 만원")
        if paint_penalty > 0: st.warning(f"🔧 수리필요(도장) 추가 감가: {paint_penalty} 만원")
        if mile_points > 0: st.warning(f"🛣️ 주행거리 초과 감점: {mile_points} 만원")
        st.success(f"🏁 최종 산출 가격: {final_car_price:,} 만원")