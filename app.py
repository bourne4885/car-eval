import streamlit as st
import pandas as pd
import datetime  # 날짜 자동 호출을 위해 추가

# ==========================================
# 0. 감가율 테이블 (1~180 계수)
# ==========================================
RATE_TABLE = {
    1: 100, 2: 98.96, 3: 97.92, 4: 96.88, 5: 95.85, 6: 94.81, 7: 93.77, 8: 92.74, 9: 91.7, 10: 90.66,
    11: 89.62, 12: 88.59, 13: 87.55, 14: 86.65, 15: 85.75, 16: 84.85, 17: 83.95, 18: 83.05, 19: 82.15, 20: 81.25,
    21: 80.36, 22: 79.46, 23: 78.56, 24: 77.66, 25: 76.76, 26: 75.97, 27: 75.18, 28: 74.4, 29: 73.61, 30: 72.82,
    31: 72.04, 32: 71.25, 33: 70.46, 34: 69.68, 35: 68.89, 36: 68.11, 37: 67.32, 38: 66.65, 39: 65.99, 40: 65.32,
    41: 64.66, 42: 63.99, 43: 63.33, 44: 62.66, 45: 62, 46: 61.33, 47: 60.67, 48: 60, 49: 59.34, 50: 58.75,
    51: 58.16, 52: 57.57, 53: 56.98, 54: 56.39, 55: 55.8, 56: 55.21, 57: 54.62, 58: 54.04, 59: 53.45, 60: 52.86,
    61: 52.27, 62: 51.74, 63: 51.21, 64: 50.68, 65: 50.16, 66: 49.63, 67: 49.1, 68: 48.57, 69: 48.05, 70: 47.52,
    71: 46.99, 72: 46.47, 73: 45.94, 74: 45.49, 75: 45.04, 76: 44.59, 77: 44.15, 78: 43.7, 79: 43.25, 80: 42.8,
    81: 42.36, 82: 41.91, 83: 41.46, 84: 41.01, 85: 40.57, 86: 40.16, 87: 39.75, 88: 39.35, 89: 38.94, 90: 38.53,
    91: 38.13, 92: 37.72, 93: 37.31, 94: 36.91, 95: 36.5, 96: 36.09, 97: 35.69, 98: 35.31, 99: 34.94, 100: 34.57,
    101: 34.2, 102: 33.82, 103: 33.45, 104: 33.08, 105: 32.71, 106: 32.33, 107: 31.96, 108: 31.59, 109: 31.22, 110: 30.9,
    111: 30.58, 112: 30.26, 113: 29.94, 114: 29.62, 115: 29.3, 116: 28.98, 117: 28.66, 118: 28.34, 119: 28.02, 120: 27.7,
    121: 27.38, 122: 27.08, 123: 26.78, 124: 26.48, 125: 26.19, 126: 25.89, 127: 25.59, 128: 25.29, 129: 25, 130: 24.7,
    131: 24.4, 132: 24.1, 133: 23.81, 134: 23.53, 135: 23.25, 136: 22.97, 137: 22.69, 138: 22.41, 139: 22.13, 140: 21.85,
    141: 21.57, 142: 21.29, 143: 21.01, 144: 20.74, 145: 20.46, 146: 20.22, 147: 19.99, 148: 19.75, 149: 19.52, 150: 19.29,
    151: 19.05, 152: 18.82, 153: 18.58, 154: 18.35, 155: 18.11, 156: 17.88, 157: 17.65, 158: 17.42, 159: 17.2, 160: 16.98,
    161: 16.76, 162: 16.53, 163: 16.31, 164: 16.09, 165: 15.87, 166: 15.64, 167: 15.42, 168: 15.2, 169: 14.98, 170: 14.76,
    171: 14.55, 172: 14.34, 173: 14.13, 174: 13.92, 175: 13.71, 176: 13.49, 177: 13.28, 178: 13.07, 179: 12.86, 180: 12.65
}

# ==========================================
# 1. 한국자동차진단보증협회 표준 엔진
# ==========================================
class KautoStandardEvaluator:
    def __init__(self, vehicle_type, is_import, displacement=0, eco_size=None, cargo_ton=0.0, 
                 reg_year=2022, reg_month=1, eval_year=2026, eval_month=7):
        self.vehicle_type = vehicle_type
        self.is_import = is_import
        self.displacement = displacement
        self.eco_size = eco_size
        self.cargo_ton = cargo_ton
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.eval_year = eval_year
        self.eval_month = eval_month

    def determine_grade(self):
        # (이전 로직과 동일)
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
        return coeff_table["수입" if self.is_import else "국산"].get(grade, 1.0)

    def get_age_depreciation_rate(self):
        """연식 감가율 산출: (사용년*12) + (평가월 - 등록월)"""
        usage_years = self.eval_year - self.reg_year
        total_months = (usage_years * 12) + (self.eval_month - self.reg_month)
        coeff = max(1, min(180, total_months))
        return total_months, RATE_TABLE.get(coeff, 12.65)

    def calculate_accident_penalty(self, selected_accident, coeff):
        market_price_table = {
            "국산": {"1랭크": 40, "2랭크": 100, "A랭크": 180, "B랭크": 300, "C랭크": 450},
            "수입": {"1랭크": 70, "2랭크": 150, "A랭크": 300, "B랭크": 550, "C랭크": 800}
        }
        active_table = market_price_table["수입" if self.is_import else "국산"]
        total_penalty = 0
        logs = {}
        for part, data in selected_accident.items():
            rank, status = data["rank"], data["status"]
            base = active_table.get(rank, 0)
            penalty = int(base * (1.0 if status == "교환(X)" else 0.6) * coeff)
            total_penalty += penalty
            logs[part] = f"{status} (-{penalty}만원)"
        return total_penalty, logs

# ==========================================
# 2. UI 구성
# ==========================================
st.set_page_config(page_title="차량 매입가 시스템", layout="wide")
st.title("🚗 진단협회 표준 경매 매입 시스템")

# [입력 섹션]
col1, col2 = st.columns(2)
with col1:
    st.subheader("🗓️ 평가 기준일 (산출일)")
    # 오늘 날짜를 자동으로 가져옴
    today = datetime.date.today()
    eval_c1, eval_c2 = st.columns(2)
    eval_year = eval_c1.number_input("평가 연도", value=today.year)
    eval_month = eval_c2.number_input("평가 월", 1, 12, value=today.month)
    
    st.subheader("📋 차량 정보")
    origin = st.selectbox("제조국", ["국산", "수입"])
    v_type = st.selectbox("차종", ["승용형", "다목적형", "전기/수소", "화물차"])
    
    if v_type in ["승용형", "다목적형"]:
        displacement = st.number_input("배기량(cc)", value=2000, step=100)
        eco_size, cargo_ton = None, 0.0
    elif v_type == "전기/수소":
        displacement, eco_size, cargo_ton = 0, st.selectbox("차종 크기", ["대형", "중형", "소형", "경형 일반형", "경형 초소형"]), 0.0
    else:
        displacement, eco_size, cargo_ton = 0, None, st.number_input("최대 적재용량(톤)", value=1.0)
        
    reg_year = st.number_input("등록년도", value=2022)
    reg_month = st.slider("등록월", 1, 12, 1)

with col2:
    st.subheader("💰 시세 및 설정")
    base_price = st.number_input("무사고 정상 시세(만원)", value=2500, step=50)
    margin = st.number_input("희망 마진(만원)", value=150, step=10)
    fixed_cost = st.number_input("고정비(만원)", value=50, step=10)
    auction_fee = st.slider("수수료율(%)", 0.0, 5.0, 2.2)

# 엔진 생성
engine = KautoStandardEvaluator(v_type, (origin=="수입"), displacement, eco_size, cargo_ton, reg_year, reg_month, eval_year, eval_month)
grade = engine.determine_grade()
coeff = engine.get_grade_coefficient(grade)
months, rate = engine.get_age_depreciation_rate()

st.success(f"📋 산출 결과: 등급 [{grade}] (계수: {coeff}) | 사용월: {months}개월 (잔가율: {rate}%)")

# [사고 입력]
st.header("🛠️ 사고/도색 상태 입력")
all_car_parts = {
    "외판": {"후드":"1랭크", "프론트 펜더(좌)":"1랭크", "프론트 펜더(우)":"1랭크", "앞도어(좌)":"1랭크", "앞도어(우)":"1랭크", "뒷도어(좌)":"1랭크", "뒷도어(우)":"1랭크", "트렁크 리드":"1랭크", "쿼터 패널(좌)":"2랭크", "쿼터 패널(우)":"2랭크", "루프 패널":"2랭크"},
    "골격": {"프론트 패널":"A랭크", "리어 패널":"A랭크", "트렁크 플로어":"A랭크", "사이드 멤버(좌)":"B랭크", "사이드 멤버(우)":"B랭크", "휠 하우스(좌)":"B랭크", "휠 하우스(우)":"B랭크", "대쉬 패널":"C랭크"}
}

selected_accident = {}
for category, parts in all_car_parts.items():
    with st.expander(f"🔻 {category} 사고 상태"):
        cols = st.columns(4)
        for idx, (p, rank) in enumerate(parts.items()):
            status = cols[idx % 4].selectbox(p, ["정상", "교환(X)", "판금/용접(W)"], key=f"acc_{p}")
            if status != "정상": selected_accident[p] = {"rank": rank, "status": status}

# [최종 결과]
st.divider()
st.header("🎯 최종 분석 리포트")

# 연산
acc_penalty, acc_logs = engine.calculate_accident_penalty(selected_accident, coeff)
std_price = base_price * (rate / 100)
final_bid = (std_price - acc_penalty - fixed_cost - margin) / (1 + auction_fee/100)

col_r1, col_r2 = st.columns(2)
with col_r1:
    st.metric("추정 매입가 (연식 감가 반영)", f"{int(std_price):,} 만원")
    st.metric("최종 최고 입찰가 (Max Bid)", f"{int(max(0, final_bid)):,} 만원")

with col_r2:
    st.write("### 감가 상세 내역")
    if acc_logs:
        for p, log in acc_logs.items(): st.write(f"- {p}: {log}")
    else:
        st.write("사고 이력이 없습니다.")
    st.info(f"계산 근거: {base_price}만원 * {rate}% = {int(std_price)}만원 (사고 감가 {acc_penalty}만원 차감)")