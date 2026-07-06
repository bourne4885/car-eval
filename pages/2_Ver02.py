import streamlit as st
import math

class CarEvaluation:
    def __init__(self, origin, grade):
        self.origin = origin
        self.grade = grade
        self.point_value = 10000
        self.grade_coefficients = {
            '국산': {'특C': 2.2, '특B': 1.8, '특A': 1.5, 'I': 1.4, 'II': 1.2, 'III': 1.0, 'IV': 0.9, '경': 0.8},
            '수입': {'특C': 2.7, '특B': 2.5, '특A': 2.0, 'I': 1.7, 'II': 1.4, 'III': 1.2, 'IV': 1.1, '경': 1.0}
        }
        
    def get_grade_coef(self):
        return self.grade_coefficients[self.origin][self.grade]

    def calculate_use_period(self, reg_year, reg_month, eval_year, eval_month):
        use_years = eval_year - reg_year
        remaining_months = eval_month - reg_month
        use_months = (use_years * 12) + remaining_months
        return use_years, use_months

    def calculate_adjusted_price(self, base_price, eval_month):
        monthly_depreciation_rates = {
            2: 0.01, 3: 0.02, 5: 0.01, 6: 0.02,
            8: 0.01, 9: 0.02, 11: 0.01, 12: 0.02
        }
        month_rate = monthly_depreciation_rates.get(eval_month, 0.0)
        monthly_adjustment = base_price * month_rate
        adjusted_price = base_price - monthly_adjustment
        return math.ceil(adjusted_price)

    def calculate_prev_year_price(self, adjusted_price):
        return math.ceil(adjusted_price * 1.1)

    def evaluate_mileage(self, adjusted_price, prev_adjusted_price, use_months, real_mileage):
        std_mileage = use_months * 1.66 * 1000
        mileage_diff = std_mileage - real_mileage
        price_diff = prev_adjusted_price - adjusted_price
        
        # [수정] 등급별 계수(coef)를 가져와서 공식에 반영했습니다.
        coef = self.get_grade_coef()
        mileage_score = (price_diff * mileage_diff * 20 * coef) / 1000
        
        max_positive = adjusted_price * 0.15
        max_negative = -(adjusted_price * 0.30)
        
        if mileage_score > max_positive:
            mileage_score = max_positive
        elif mileage_score < max_negative:
            mileage_score = max_negative
            
        return math.ceil(mileage_score)


st.title("🚗 자동차 진단평가 기준 시스템")
st.caption("기준서의 연산 규칙(올림 처리 및 주행거리 가·감점 한도)이 반영된 정밀 계산기입니다.")

# 💡 [추가] 사용자가 언제든 펼쳐볼 수 있는 등급 분류 기준표 (도움말 상자)
with st.expander("📊 진단평가 등급 분류 기준표 보기"):
    st.markdown("""
    | 등급 | 대상 차종 (국산/수입 공통) | 대표 예시 차량 |
    | :---: | :--- | :--- |
    | **경** | 경형 자동차 (1,000cc 미만) | 모닝, 레이, 캐스퍼, 스파크 등 |
    | **IV** | 소형 자동차 | 엑센트, 프라이드 등 |
    | **III** | 준중형 자동차 | 아반떼, K3, SM3 등 |
    | **II** | 중형 자동차 | 쏘나타, K5, SM6 등 |
    | **I** | 준대형 자동차 | 그랜저, K8, K7 등 |
    | **특A** | 대형 자동차 및 일반 수입차 | 제네시스 G80, 팰리세이드, BMW 5시리즈, 벤츠 E클래스 등 |
    | **특B** | 고급 대형차 및 프리미엄 수입차 | 제네시스 G90, BMW 7시리즈, 벤츠 S클래스 등 |
    | **특C** | 최고급 대형차 및 고가 슈퍼카 | 롤스로이스, 벤틀리, 포르쉐, 레인지로버 등 |
    """)

with st.form("evaluation_form"):
    col1, col2 = st.columns(2)
    with col1:
        origin = st.selectbox("원산지 구분", ["국산", "수입"])
        base_price = st.number_input("기준 가격 (원)", value=20000000, step=100000)
    with col2:
        grade = st.selectbox("등급 선택", ["특C", "특B", "특A", "I", "II", "III", "IV", "경"])
        real_mileage = st.number_input("실주행거리 (km)", value=30000, step=1000)
        
    st.markdown("---")
    st.subheader("🗓️ 기간 설정")
    col3, col4 = st.columns(2)
    with col3:
        reg_year = st.number_input("최초 등록 연도", value=2024)
        reg_month = st.number_input("최초 등록 월", value=1, min_value=1, max_value=12)
    with col4:
        eval_year = st.number_input("가격 조사/평가 연도", value=2026)
        eval_month = st.number_input("가격 조사/평가 월", value=7, min_value=1, max_value=12)

    submit_button = st.form_submit_button("진단평가 계산하기")

if submit_button:
    evaluator = CarEvaluation(origin, grade)
    
    years, months = evaluator.calculate_use_period(reg_year, reg_month, eval_year, eval_month)
    adj_p = evaluator.calculate_adjusted_price(base_price, eval_month)
    prev_adj_p = evaluator.calculate_prev_year_price(adj_p)
    mileage_res = evaluator.evaluate_mileage(adj_p, prev_adj_p, months, real_mileage)
    
    final_price = adj_p + mileage_res
    
    st.success("🎯 계산이 완료되었습니다!")
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="최종 산정 가격", value=f"{final_price:,} 원")
        st.write(f"• **사용 기간:** {years}년 {months}개월 (총 {months}달)")
        st.write(f"• **적용된 등급 계수:** {evaluator.get_grade_coef()}")
    with res_col2:
        st.write(f"• **기본 보정 가격:** {adj_p:,} 원")
        st.write(f"• **주행거리 가·감점액:** {mileage_res:,} 원")