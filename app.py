import streamlit as st
import pandas as pd

# ==========================================
# 1. 한국자동차진단보증협회 표준 등급 산출 엔진
# ==========================================
class KautoStandardEvaluator:
    def __init__(self, vehicle_type, is_import, displacement=0, eco_size=None, cargo_ton=0.0, reg_year=2022, reg_month=1, mileage=60000, base_price_manwon=2500):
        self.vehicle_type = vehicle_type
        self.is_import = is_import
        self.displacement = displacement
        self.eco_size = eco_size
        self.cargo_ton = cargo_ton
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.mileage = mileage
        self.base_price_manwon = base_price_manwon
        self.current_year = 2026
        self.current_month = 7

    def determine_grade(self):
        if self.vehicle_type == "승용형":
            cc = self.displacement
            if cc >= 3600: return "특C"
            elif cc >= 2900: return "특B"
            elif cc >= 2400: return "특A"
            elif cc >= 2100: return "I"
            elif cc >= 1700: return "II"
            elif cc >= 1300: return "III"
            elif cc >= 1100: return "IV"
            else: return "경"
        elif self.vehicle_type == "다목적형":
            cc = self.displacement
            if cc >= 2400: return "특C"
            elif cc >= 2100: return "특B"
            elif cc >= 1700: return "특A"
            elif cc >= 1300: return "I"
            elif cc >= 1100: return "II"
            else: return "III"
        elif self.vehicle_type == "전기/수소":
            if self.eco_size == "대형": return "특B"
            elif self.eco_size == "중형": return "특A"
            elif self.eco_size == "소형": return "I"
            elif self.eco_size == "경형 일반형": return "III"
            elif self.eco_size == "경형 초소형": return "IV"
            else: return "I"
        elif self.vehicle_type == "화물차":
            t = self.cargo_ton
            if t >= 4.0: return "특C"
            elif t >= 1.5: return "특B"
            elif t >= 1.1: return "특A"
            elif t == 1.0: return "I"
            else: return "경"
        return "III"

    def get_grade_coefficient(self, grade):
        coeff_table = {
            "국산": {"특C": 2.2, "특B": 1.8, "특A": 1.5, "I": 1.4, "II": 1.2, "III": 1.0, "IV": 0.9, "경": 0.8},
            "수입": {"특C": 2.7, "특B": 2.5, "특A": 2.0, "I": 1.7, "II": 1.4, "III": 1.2, "IV": 1.1, "경": 1.0}
        }
        origin_key = "수입" if self.is_import else "국산"
        return coeff_table[origin_key].get(grade, 1.0)

    def calculate_mileage_penalty(self, usage_years):
        standard_mileage = max(1, usage_years) * 20000
        mileage_diff = self.mileage - standard_mileage
        unit_cost = 0.015 if self.is_import else 0.008
        return int(mileage_diff * unit_cost), standard_mileage

    def calculate_market_accident_penalty(self, selected_accident, coeff):
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
            repair_factor = 1.0 if status == "교환(X)" else 0.6
            current_penalty = int(base_penalty * repair_factor * coeff)
            total_penalty += current_penalty
            detail_logs[part] = f"{status} ──> 감가: -{current_penalty}만 원 ({rank})"
        return total_penalty, detail_logs

# ==========================================
# 2. UI 및 메인 로직
# ==========================================
st.set_page_config(page_title="협회 표준형 경매 매입 시스템", page_icon="🚗", layout="wide")
st.title("🚗 진단협회 표준 기준 연동 경매 입찰가 산출기")

# [추가] 등급별 차량 예시 참조 (접기/펴기 기능)
with st.expander("📌 진단협회 등급 분류 및 대표 차량 예시 (참고용)"):
    df_ref = pd.DataFrame({
        "등급": ["특C", "특B", "특A", "I", "II", "III", "IV", "경"],
        "승용(배기량)": ["3.6L 이상", "2.9 ~ 3.6 미만", "2.4 ~ 2.9 미만", "2.1 ~ 2.4 미만", "1.7 ~ 2.1 미만", "1.3 ~ 1.7 미만", "1.1 ~ 1.3 미만", "1.1 미만"],
        "대표 차량 예시": ["S-Class, G90, 7시리즈", "E-Class, 5시리즈, G80", "그랜저, K8, 캠리", "쏘나타, K5, 투싼", "아반떼, K3, 스포티지", "베뉴, 코나, 셀토스", "캐스퍼, 모닝(일부)", "스파크, 레이, 모닝"]
    })
    st.table(df_ref)
    st.caption("※ 위 예시는 일반적인 배기량 기준이며, 실제 차량 등록증상의 제원에 따라 등급이 달라질 수 있습니다.")

# 부위 정의
all_car_parts = {
    "🔻 외판 단순 (1랭크)": {"후드": "1랭크", "프론트 펜더(좌)": "1랭크", "프론트 펜더(우)": "1랭크", "앞도어(좌)": "1랭크", "앞도어(우)": "1랭크", "뒷도어(좌)": "1랭크", "뒷도어(우)": "1랭크", "트렁크 리드": "1랭크"},
    "🔻 외판 주요 (2랭크)": {"쿼터 패널(좌)": "2랭크", "쿼터 패널(우)": "2랭크", "루프 패널": "2랭크"},
    "🔺 골격 경미 (A랭크)": {"프론트 패널": "A랭크", "리어 패널": "A랭크", "트렁크 플로어": "A랭크"},
    "🔺 골격 중대 (B/C랭크)": {"사이드 멤버(좌)": "B랭크", "사이드 멤버(우)": "B랭크", "휠 하우스(좌)": "B랭크", "휠 하우스(우)": "B랭크", "대쉬 패널": "C랭크"}
}

# 입력 섹션
st.header("📝 1. 차량 조건 설정")
col1, col2, col3 = st.columns(3)
with col1:
    origin = st.selectbox("제조국", ["국산", "수입"])
    vehicle_type = st.selectbox("차종", ["승용형", "다목적형", "전기/수소", "화물차"])
    displacement = st.number_input("배기량(cc)", value=2000) if vehicle_type in ["승용형", "다목적형"] else 0
    eco_size = st.selectbox("전기/수소 등급", ["대형", "중형", "소형", "경형 일반형", "경형 초소형"]) if vehicle_type == "전기/수소" else None
    cargo_ton = st.number_input("화물 적재량(톤)", value=1.0) if vehicle_type == "화물차" else 0.0
with col2:
    base_price = st.number_input("무사고 시세(만원)", value=2500)
    reg_year = st.number_input("등록년도", value=2022)
    mileage = st.number_input("주행거리(km)", value=60000)
with col3:
    target_margin = st.number_input("목표 마진(만원)", value=150)
    fixed_cost = st.number_input("고정비(만원)", value=50)
    auction_fee = st.slider("수수료율(%)", 0.0, 5.0, 2.2)

# 엔진 초기화
engine = KautoStandardEvaluator(vehicle_type, (origin=="수입"), displacement, eco_size, cargo_ton, reg_year, 1, mileage, base_price)
assigned_grade = engine.determine_grade()
coeff = engine.get_grade_coefficient(assigned_grade)

# 사고/도색 입력
st.header("🛠️ 2. 사고 및 도색 상태")
selected_accident = {}
for sec, parts in all_car_parts.items():
    st.markdown(f"**{sec}**")
    cols = st.columns(4)
    for idx, (p, rank) in enumerate(parts.items()):
        status = cols[idx % 4].selectbox(p, ["정상", "교환(X)", "판금/용접(W)"], key=f"acc_{p}")
        if status != "정상": selected_accident[p] = {"rank": rank, "status": status}

# 연산
mileage_penalty, _ = engine.calculate_mileage_penalty(2026 - reg_year)
acc_penalty, logs = engine.calculate_market_accident_penalty(selected_accident, coeff)
total_reduction = mileage_penalty + acc_penalty
max_bid = (base_price - total_reduction - fixed_cost - target_margin) / (1 + auction_fee/100)

# 결과 출력
st.header("🎯 결과 리포트")
st.info(f"선택 차량 등급: **{assigned_grade}** (계수: {coeff})")
st.metric("최종 추천 입찰가", f"{int(max_bid):,} 만원")
if logs:
    st.write("감가 상세 내역:")
    for p, log in logs.items(): st.write(f"- {log}")