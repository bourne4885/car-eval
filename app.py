import streamlit as st
import pandas as pd
import datetime

# ==========================================
# 0. 감가율 테이블 및 로직 (이전과 동일)
# ==========================================
RATE_TABLE = {i: 100 - (i * 0.5) for i in range(1, 181)} # 예시를 위한 간략화, 실제 값으로 대체 가능

class KautoStandardEvaluator:
    def __init__(self, vehicle_type, is_import, displacement, eco_size, cargo_ton, reg_year, reg_month, eval_year, eval_month):
        self.vehicle_type = vehicle_type
        self.is_import = is_import
        self.displacement = displacement
        self.eco_size = eco_size
        self.cargo_ton = cargo_ton
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.eval_year = eval_year
        self.eval_month = eval_month

    def get_age_depreciation_rate(self):
        usage_years = self.eval_year - self.reg_year
        total_months = (usage_years * 12) + (self.eval_month - self.reg_month)
        coeff = max(1, min(180, total_months))
        # 여기에 실제 협회 잔가율 테이블 적용
        rate = 100 - (coeff * 0.4) # 예시 연산
        return total_months, rate

    def calculate_accident_penalty(self, selected_accident, grade_coeff):
        market_price_table = {
            "국산": {"1랭크": 40, "2랭크": 100, "A랭크": 180, "B랭크": 300, "C랭크": 450},
            "수입": {"1랭크": 70, "2랭크": 150, "A랭크": 300, "B랭크": 550, "C랭크": 800}
        }
        active_table = market_price_table["수입" if self.is_import else "국산"]
        total_penalty = 0
        details = []
        for part, data in selected_accident.items():
            rank, status = data["rank"], data["status"]
            base = active_table.get(rank, 0)
            penalty = int(base * (1.0 if status == "교환(X)" else 0.6) * grade_coeff)
            total_penalty += penalty
            details.append({"부위": part, "상태": status, "감가액": penalty})
        return total_penalty, details

# ==========================================
# 2. UI 구성
# ==========================================
st.set_page_config(page_title="차량 매입가 리포트", layout="wide")
st.title("🚗 차량 매입 분석 리포트")

# 입력 섹션 (간소화)
col1, col2 = st.columns(2)
with col1:
    st.subheader("🗓️ 기준 설정")
    today = datetime.date.today()
    eval_year = st.number_input("평가 연도", value=today.year)
    eval_month = st.number_input("평가 월", 1, 12, value=today.month)
    reg_year = st.number_input("등록년도", value=2022)
    reg_month = st.slider("등록월", 1, 12, 1)

with col2:
    st.subheader("💰 시세 및 비용")
    base_price = st.number_input("무사고 정상 시세(만원)", value=2500)
    margin = st.number_input("희망 마진(만원)", value=150)
    fixed_cost = st.number_input("고정비(만원)", value=50)

# (중략: 사고 입력 부분은 이전과 동일하게 유지)
# ... 사고 입력 로직 실행 후 ...

# [최종 결과 및 감가 상세 리포트]
st.divider()
st.subheader("📊 감가 상세 산출 내역")

# 1. 연식 감가
months, rate = engine.get_age_depreciation_rate()
age_depreciated_price = int(base_price * (rate / 100))
age_loss = base_price - age_depreciated_price

# 2. 사고 감가
acc_penalty, acc_details = engine.calculate_accident_penalty(selected_accident, 1.0) # 계수 예시

# 상세 리포트 출력
report_cols = st.columns(3)
report_cols[0].metric("정상 시세", f"{base_price:,}만원")
report_cols[1].metric("연식 감가 반영", f"{age_depreciated_price:,}만원", delta=f"-{age_loss:,}만원", delta_color="inverse")
report_cols[2].metric("사고 감가", f"-{acc_penalty:,}만원", delta_color="inverse")

# 상세 표
if acc_details:
    st.write("### 🛠️ 사고 감가 항목 상세")
    df_acc = pd.DataFrame(acc_details)
    st.table(df_acc)

st.write("### 🧮 최종 매입가 계산식")
st.latex(r'''
\text{최종가} = (\text{정상가} - \text{연식감가} - \text{사고감가} - \text{고정비}) - \text{마진}
''')

final_price = age_depreciated_price - acc_penalty - fixed_cost - margin
st.success(f"### 🎯 추천 매입가: {max(0, final_price):,} 만원")