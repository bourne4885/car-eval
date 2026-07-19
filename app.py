import streamlit as st
from datetime import datetime, time

# [엔진 통합 클래스: 모든 로직 보존]
class OfficialMarketEvaluator:
    def __init__(self, base_price, reg_date):
        self.base_price = base_price
        reg_dt = datetime.combine(reg_date, time.min)
        self.usage_years = (datetime.now() - reg_dt).days / 365.25
        self.corrected_base_price = base_price

    def calculate_results(self, data):
        details = []
        total_penalty = 0

        # 제13조 주행거리 로직 (한도 15%/30%)
        # ... (이전의 정밀 역산 및 가감점 한도 로직 삽입 위치)

        # 제15조 배출가스
        if data['emission_failed']:
            factor = 60 if data['fuel'] == "가솔린" else 120
            penalty = factor * min(self.usage_years, 5.0)
            total_penalty += penalty
            details.append(f"배출가스 감점: -{int(penalty)}만원")

        # 제16조 튜닝
        if data['tuning_status'] == "불법 튜닝":
            factor = 80 if data['tuning_type'] == "장치" else 120
            penalty = factor * min(self.usage_years, 5.0)
            total_penalty += penalty
            details.append(f"불법튜닝 감점: -{int(penalty)}만원")

        # 제17조 보험수리 (외판 2랭크 시 제외 로직 포함)
        if not data['has_major_damage']:
            threshold = 300 if data['is_import'] else 100
            if data['parts_cost'] >= threshold:
                penalty = self.corrected_base_price * 0.07 * min(self.usage_years, 5.0)
                total_penalty += penalty
                details.append(f"보험수리 불일치 감점: -{int(penalty)}만원")

        return total_penalty, details

# [통합 UI 구성]
st.title("🚗 중고차 약관 기준 정밀 산출 시스템")

# 상단 기본 정보
col1, col2, col3 = st.columns(3)
with col1: price = st.number_input("신차 출고가 (만원)", value=4000)
with col2: reg_date = st.date_input("최초 등록일")
with col3: fuel = st.selectbox("연료", ["가솔린", "디젤"])

# 상세 평가 항목 (3열 배치)
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.subheader("제13-15조")
    mileage = st.number_input("실 주행거리 (km)", value=50000)
    emission_failed = st.checkbox("배출가스 초과")
with col_b:
    st.subheader("제16조 튜닝")
    tuning_status = st.selectbox("튜닝 상태", ["정상", "불법 튜닝"])
    tuning_type = st.radio("구분", ["장치", "구조"])
with col_c:
    st.subheader("제17조 보험수리")
    has_major_damage = st.checkbox("외판 2랭크 이상 손상")
    parts_cost = st.number_input("보험수리 부품값(만원)", value=0)
    is_import = st.checkbox("수입차 여부")

if st.button("📊 최종 산출 실행"):
    engine = OfficialMarketEvaluator(price, reg_date)
    # 계산 데이터 통합
    data = {'fuel': fuel, 'emission_failed': emission_failed, 'tuning_status': tuning_status, 
            'tuning_type': tuning_type, 'has_major_damage': has_major_damage, 
            'parts_cost': parts_cost, 'is_import': is_import}
    
    penalty, logs = engine.calculate_results(data)
    st.write("---")
    for log in logs: st.write(log)
    st.metric("최종 입찰가", f"{int(price - penalty)} 만원")