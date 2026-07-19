import streamlit as st
from datetime import datetime

# [연산 엔진 클래스]
class OfficialMarketEvaluator:
    def __init__(self, base_price, registration_date):
        self.base_price = base_price
        self.registration_date = registration_date
        self.usage_years = (datetime.now() - registration_date).days / 365.25
        self.corrected_base_price = self.base_price  # 로직에 따라 보정된 기준가격

    # 제13조 주행거리 가/감점 (한도: 가점 15%, 감점 30%)
    def calculate_mileage_penalty(self, real_mileage, standard_mileage):
        diff = standard_mileage - real_mileage
        rate = diff / standard_mileage
        penalty = self.corrected_base_price * rate
        
        if rate > 0: # 가점
            return min(penalty, self.corrected_base_price * 0.15), "가점"
        else: # 감점
            return max(penalty, -self.corrected_base_price * 0.30), "감점"

    # 제15조 배출가스 평가
    def calculate_emission_penalty(self, fuel_type, is_failed):
        if not is_failed: return 0
        factor = 60 if fuel_type == "가솔린" else 120
        return factor * min(self.usage_years, 5.0)

    # 제16조 튜닝 평가
    def calculate_tuning_adjustment(self, status, t_type, cost=0):
        if status == "불법 튜닝":
            factor = 80 if t_type == "장치" else 120
            return -(factor * min(self.usage_years, 5.0))
        elif status == "적법 튜닝(승인)":
            return cost * 0.5 * (min(self.usage_years, 5.0) / 5.0)
        return 0

    # 제17조 특별이력 (보험수리 등)
    def calculate_special_history(self, history_data, has_major_damage):
        penalties = 0
        # 침수/화재(40%), 전손(10%)
        for key, rate in history_data.items():
            if key in ["침수", "화재"]: penalties += self.corrected_base_price * 0.4 * min(self.usage_years, 5.0)
            elif key == "전손": penalties += self.corrected_base_price * 0.1 * min(self.usage_years, 5.0)
        
        # 보험수리이력(7%) - 외판 2랭크 이상 손상 시 적용 제외
        if not has_major_damage and history_data.get("보험수리", 0) > 0:
            penalties += self.corrected_base_price * 0.07 * min(self.usage_years, 5.0)
        return penalties

# [Streamlit UI 환경]
st.title("🚗 자동차 경매 매입가 정밀 산출 시스템")

# 1. 기본 정보 입력
col1, col2 = st.columns(2)
with col1:
    price = st.number_input("신차 출고가 (만원)", value=4000)
    reg_date = st.date_input("최초 등록일", value=datetime(2023, 3, 1))
with col2:
    fuel = st.selectbox("연료", ["가솔린", "디젤"])

# 2. 엔진 인스턴스 생성
engine = OfficialMarketEvaluator(price, reg_date)

# 3. 조항별 평가 입력창 (UI 생략: 위 로직을 호출하는 입력 요소들을 배치하세요)
st.subheader("💡 산출 상세")
if st.button("최종 입찰가 산출"):
    # 로직 호출 및 결과 출력
    st.success(f"기준 보정가: {engine.corrected_base_price}만원")
    # 결과 리포트 출력 로직...