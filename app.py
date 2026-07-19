import streamlit as st
import pandas as pd
import datetime

# ==========================================
# 0. 감가율 데이터 및 클래스 정의
# ==========================================
RATE_TABLE = {i: 100 - (i * 0.5) for i in range(1, 181)} # 예시용 데이터

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
        rate = RATE_TABLE.get(coeff, 12.65)
        return total_months, rate

    def calculate_accident_penalty(self, selected_accident, coeff):
        # 사고 감가 계산 로직
        total_penalty = 0
        details = []
        # (이전 사고 계산 로직 유지)
        return total_penalty, details

# ==========================================
# 1. UI 및 입력 영역
# ==========================================
st.set_page_config(page_title="차량 매입가 시스템", layout="wide")
st.title("🚗 진단협회 표준 경매 매입 시스템")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗓️ 평가 기준일")
    today = datetime.date.today()
    eval_year = st.number_input("평가 연도", value=today.year)
    eval_month = st.number_input("평가 월", 1, 12, value=today.month)
    
    st.subheader("📋 차량 정보")
    origin = st.selectbox("제조국", ["국산", "수입"])
    v_type = st.selectbox("차종", ["승용형", "다목적형", "전기/수소", "화물차"])
    
    # ... (기타 입력 필드 동일)
    reg_year = st.number_input("등록년도", value=2022)
    reg_month = st.slider("등록월", 1, 12, 1)

with col2:
    st.subheader("💰 시세 및 비용")
    base_price = st.number_input("무사고 정상 시세(만원)", value=2500)
    # ... (기타 비용 동일)

# ==========================================
# 2. 엔진 초기화 및 계산 (오류 방지)
# ==========================================
# 여기서 engine을 먼저 생성해야 아래에서 오류가 안 납니다!
engine = KautoStandardEvaluator(
    v_type, (origin=="수입"), 2000, None, 1.0, reg_year, reg_month, eval_year, eval_month
)

# 이제 엔진을 사용합니다
months, rate = engine.get_age_depreciation_rate()

# ==========================================
# 3. 결과 출력
# ==========================================
st.divider()
st.subheader("📊 결과 리포트")
st.write(f"평가 기준: {eval_year}년 {eval_month}월")
st.write(f"사용 기간: {months}개월")
st.write(f"적용 잔가율: {rate}%")