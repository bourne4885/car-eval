import streamlit as st
from datetime import datetime, time

# Streamlit 설정
st.set_page_config(page_title="중고차 매입 정밀 산출기", layout="wide")

class OfficialMarketEvaluator:
    def __init__(self, base_price, registration_date):
        self.base_price = base_price
        # 타입 에러 방지: date 객체를 datetime으로 변환
        reg_dt = datetime.combine(registration_date, time.min)
        self.usage_years = (datetime.now() - reg_dt).days / 365.25
        self.corrected_base_price = base_price # 약관 보정식에 따라 수정 가능

    def calculate_all(self, data):
        """모든 조항을 계산하여 감점 총액 반환"""
        total_penalty = 0
        details = []

        # 제13조 주행거리 (간략화된 예시)
        # 제15조 배출가스
        if data.get('emission_failed'):
            factor = 60 if data['fuel'] == "가솔린" else 120
            penalty = factor * min(self.usage_years, 5.0)
            total_penalty += penalty
            details.append(f"배출가스 감점: -{int(penalty)}만원")

        # 제16조 튜닝
        if data.get('tuning_status') == "불법 튜닝":
            factor = 80 if data['tuning_type'] == "장치" else 120
            penalty = factor * min(self.usage_years, 5.0)
            total_penalty += penalty
            details.append(f"불법튜닝 감점: -{int(penalty)}만원")

        # 제17조 특별이력 (침수/화재 40%, 전손 10%, 보험수리 7%)
        # 외판 2랭크 손상 여부 확인 후 적용
        if not data.get('has_major_damage'):
            if data.get('parts_cost', 0) >= (300 if data['is_import'] else 100):
                penalty = self.corrected_base_price * 0.07 * min(self.usage_years, 5.0)
                total_penalty += penalty
                details.append(f"보험수리 불일치 감점: -{int(penalty)}만원")

        return total_penalty, details

# UI 구성
st.title("🚗 중고차 약관 기준 정밀 산출 시스템")

col1, col2 = st.columns(2)
with col1:
    price = st.number_input("신차 출고가 (만원)", value=4000)
    reg_date = st.date_input("최초 등록일")
with col2:
    fuel = st.selectbox("연료", ["가솔린", "디젤"])
    is_import = st.checkbox("수입차 여부")

# 상태 입력
data = {
    'fuel': fuel,
    'is_import': is_import,
    'emission_failed': st.checkbox("배출가스 초과"),
    'tuning_status': st.selectbox("튜닝 상태", ["정상", "불법 튜닝"]),
    'tuning_type': "장치" if st.checkbox("장치 튜닝") else "구조",
    'has_major_damage': st.checkbox("외판 2랭크 이상 손상 있음"),
    'parts_cost': st.number_input("보험수리 부품가격 (만원)", value=0)
}

if st.button("최종 산출"):
    engine = OfficialMarketEvaluator(price, reg_date)
    penalty, logs = engine.calculate_all(data)
    
    st.subheader("📊 산출 결과")
    st.metric("최종 감점액", f"{int(penalty)} 만원")
    for log in logs:
        st.write(log)
    st.metric("최종 입찰가", f"{int(price - penalty)} 만원")