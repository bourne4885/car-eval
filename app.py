import streamlit as st
from datetime import datetime
import math

# 🚨 Streamlit 설정은 무조건 코드 최상단에 딱 한 번만 실행되어야 합니다.
st.set_page_config(page_title="공식 감가율 기준 경매 매입 시스템", page_icon="🚗", layout="wide")

# ==========================================
# [데이터 고정] 1~180 감가율 계수표 데이터 매핑
# ==========================================
DEPRECIATION_TABLE = {
    1: 100.0, 2: 98.96, 3: 97.92, 4: 96.88, 5: 95.85, 6: 94.81, 7: 93.77, 8: 92.74, 9: 91.7, 10: 90.66,
    11: 89.62, 12: 88.59, 13: 87.55, 14: 86.65, 15: 85.75, 16: 84.85, 17: 83.95, 18: 83.05, 19: 82.15, 20: 81.25,
    21: 80.36, 22: 79.46, 23: 78.56, 24: 77.66, 25: 77.66, 26: 75.97, 27: 75.18, 28: 74.4, 29: 73.61, 30: 72.82,
    31: 72.04, 32: 71.25, 33: 70.46, 34: 69.68, 35: 68.89, 36: 68.11, 37: 67.32, 38: 66.65, 39: 65.59, 40: 65.32,
    41: 64.66, 42: 63.99, 43: 63.33, 44: 62.66, 45: 62.0, 46: 61.33, 47: 60.67, 48: 60.0, 49: 59.34, 50: 58.75,
    51: 58.16, 52: 57.57, 53: 56.98, 54: 56.39, 55: 55.8, 56: 55.21, 57: 54.62, 58: 54.04, 59: 53.45, 60: 52.86,
    61: 52.27, 62: 51.74, 63: 51.21, 64: 50.68, 65: 50.16, 66: 49.63, 67: 49.1, 68: 48.57, 69: 48.05, 70: 47.52,
    71: 46.99, 72: 46.47, 73: 45.94, 74: 45.49, 75: 45.04, 76: 44.59, 77: 44.15, 78: 43.7, 79: 43.25, 80: 42.8,
    81: 42.36, 82: 41.91, 83: 41.46, 84: 41.01, 85: 40.57, 86: 40.16, 87: 39.75, 88: 39.35, 89: 38.94, 90: 38.53,
    91: 38.13, 92: 37.72, 93: 37.31, 94: 36.91, 95: 36.5, 96: 36.09, 97: 35.69, 98: 35.31, 99: 34.94, 100: 34.57,
    101: 34.2, 102: 33.82, 103: 33.45, 104: 33.08, 105: 32.71, 106: 32.33, 107: 31.96, 108: 31.59, 109: 31.22, 110: 30.9,
    111: 30.58, 112: 30.26, 113: 29.94, 114: 29.62, 115: 29.3, 116: 28.98, 117: 28.66, 118: 28.34, 119: 28.02, 120: 27.7,
    121: 27.38, 122: 27.08, 123: 26.78, 124: 26.48, 125: 26.19, 126: 25.89, 127: 25.59, 128: 25.29, 129: 25.0, 130: 24.7,
    131: 24.4, 132: 24.1, 133: 23.81, 134: 23.53, 135: 23.25, 136: 22.97, 137: 22.69, 138: 22.41, 139: 22.13, 140: 21.85,
    141: 21.57, 142: 21.29, 143: 21.01, 144: 20.74, 145: 20.46, 146: 20.22, 147: 19.99, 148: 19.75, 149: 19.52, 150: 19.29,
    151: 19.05, 152: 18.82, 153: 18.58, 154: 18.35, 155: 18.11, 156: 17.88, 157: 17.65, 158: 17.42, 159: 17.2, 160: 16.98,
    161: 16.76, 162: 16.53, 163: 16.31, 164: 16.09, 165: 15.87, 166: 15.64, 167: 15.42, 168: 15.2, 169: 14.98, 170: 14.76,
    171: 14.55, 172: 14.34, 173: 14.13, 174: 13.92, 175: 13.71, 176: 13.49, 177: 13.28, 178: 13.07, 179: 12.86, 180: 12.65
}

# ==========================================
# 1. 보정 공식 및 약관 반영 연산 엔진
# ==========================================
class OfficialMarketEvaluator:
    def __init__(self, is_import: bool, car_type: str, reg_year: int, reg_month: int, base_price_manwon: int, eval_year: int, eval_month: int, promotion_discount: int):
        self.is_import = is_import
        self.car_type = car_type  
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.base_price_manwon = base_price_manwon
        self.current_year = eval_year
        self.current_month = eval_month
        self.promotion_discount = promotion_discount

    def calculate_official_metrics(self):
        # 1. 사용년 및 잔여월수 산출 (제8조 1항)
        usage_years = self.current_year - self.reg_year
        if usage_years < 0: usage_years = 0
        remaining_months = self.current_month - self.reg_month

        # 2. 감가율 계수(총 경과개월 인덱스) 산출
        factor_score = 11 + (usage_years * 12) + remaining_months
        lookup_key = max(1, min(180, factor_score))

        # 3. 감가율표 기본 잔가율(%) 매칭
        residual_rate_percent = DEPRECIATION_TABLE.get(lookup_key, 12.65)
        raw_base_price = self.base_price_manwon * (residual_rate_percent / 100.0)

        # 4. [제11조] 월별 보정 계산 (실제 차량 경과개월의 분기 위치 파별)
        cycle_position = factor_score % 3
        month_loss_rate = 0.0
        position_name = "분기 첫 번째 월 (보정 없음)"
        
        if cycle_position == 2:
            month_loss_rate = 0.01
            position_name = "분기 두 번째 월 (1% 감가)"
        elif cycle_position == 0:
            month_loss_rate = 0.02
            position_name = "분기 세 번째 월 (2% 감가)"

        # ⓐ 월별 보정액 계산
        month_correction_val = raw_base_price * month_loss_rate

        # 5. [제11조] 특성값 보정 계산 (신차 프로모션 감액 구간 분류)
        promo_cut = 0
        if self.promotion_discount >= 800: promo_cut = 800
        elif self.promotion_discount >= 600: promo_cut = 600
        elif self.promotion_discount >= 400: promo_cut = 400
        elif self.promotion_discount >= 200: promo_cut = 200
        elif self.promotion_discount > 0: promo_cut = 100

        # ⓑ 특성값 보정액 = 프로모션 감액 × 잔가율(%)
        feature_correction_val = promo_cut * (residual_rate_percent / 100.0)

        # 6. 제11조 최종 보정가격 = 기준가액 - (월별보정 + 특성값보정)
        corrected_base_price = max(0.0, raw_base_price - (month_correction_val + feature_correction_val))

        # 7. 제12조 전년도 보정가격 계산 (최종 보정가의 10% 올림 가산)
        prev_year_corrected_price = math.ceil(corrected_base_price + (corrected_base_price * 0.10))

        return {
            "usage_years": usage_years,
            "remaining_months": remaining_months,
            "factor_score": factor_score,
            "factor_depreciation_rate": residual_rate_percent,
            "raw_base_price": raw_base_price,
            "position_name": position_name,
            "month_correction_val": month_correction_val,
            "month_loss_rate_percent": month_loss_rate * 100,
            "promo_cut": promo_cut,
            "feature_correction_val": feature_correction_val,
            "corrected_base_price": corrected_base_price,
            "prev_year_corrected_price": prev_year_corrected_price
        }

    def calculate_market_accident_penalty(self, selected_accident):
        if not selected_accident: return 0, {}
        market_price_table = {
            "국산": {"1랭크": 40, "2랭크": 100, "A랭크": 200, "B랭크": 350, "C랭크": 500},
            "수입": {"1랭크": 80, "2랭크": 180, "A랭크": 350, "B랭0": 600, "C랭크": 900}
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
            current_penalty = int(base_penalty * repair_factor)
            total_penalty += current_penalty
            detail_logs[part] = f"{status} ──> 실전 감가: -{current_penalty}만 원"
        return total_penalty, detail_logs

# ==========================================
# 2. Streamlit 웹 UI 화면 구성
# ==========================================
st.title("🚗 약관 규격 기준 중고차 경매 매입 산출기")
st.caption("제8조(사용년수), 제11조(기준가격 보정) 및 제12조(전년도 보정가격)를 완벽하게 통합 적용한 정밀 시스템입니다.")

# 오늘 날짜를 기준으로 시스템 자동 계산 설정 제공
today = datetime.today()
st.sidebar.header("📅 평가 시점 설정 (기본값: 오늘)")
eval_year = st.sidebar.number_input("평가 연도", min_value=2000, max_value=2100, value=today.year)
eval_month = st.sidebar.slider("평가 월", min_value=1, max_value=12, value=today.month)

all_car_parts = {
    "🔻 외판 단순 교환/판금 (1랭크)": {
        "후드": "1랭크", "프론트 펜더(좌)": "1랭크", "프론트 펜더(우)": "1랭크",
        "앞도어(좌)": "1랭크", "앞도어(우)": "1랭크", "뒷도어(좌)": "1랭크", "뒷도어(우)": "1랭크",
        "트렁크 리드": "1랭크"
    },
    "🔻 외판 주요 부위 (2랭크)": {
        "쿼터 패널(좌)": "2랭크", "쿼터 패널(우)": "2랭크", "루프 패널": "2랭크"
    },
    "🔺 주요 골격 사고 부위 (A/B/C랭크)": {
        "프론트 패널": "A랭크", "리어 패널": "A랭크", "트렁크 플로어 패널": "A랭크",
        "사이드 멤버(좌)": "B랭크", "사이드 멤버(우)": "B랭크", "휠 하우스(좌)": "B랭크", "휠 하우스(우)": "B랭크", "대쉬 패널": "C랭크"
    }
}

st.header("📝 1. 차량 기본 정보 및 특성값 보정 요소 입력")
col1, col2, col3 = st.columns(3)
with col1:
    origin = st.selectbox("차량 구분", ["국산", "수입"])
    car_type = st.selectbox("행정 규격 차종 구분", ["승용, 다목적형", "화물"])
    base_price = st.number_input("신차 출고 가격 (만원)", min_value=0, value=4000, step=100)
with col2:
    reg_year = st.number_input("최초등록년도", min_value=2000, max_value=eval_year, value=eval_year-3, step=1)
    reg_month = st.slider("최초등록월", min_value=1, max_value=12, value=1)
    promotion_discount = st.number_input("🎁 신차 프로모션 할인액 (만원)", min_value=0, value=300, step=50)
with col3:
    target_margin = st.number_input("확보할 딜러 마진 (만원)", min_value=0, value=150, step=10)
    fixed_cost = st.number_input("상사 부대비용 (만원)", min_value=0, value=50)
    paint_unit_cost = st.number_input("🎨 판당 도색 단가 (만원)", min_value=0, value=15 if origin == "국산" else 25, step=5)
    auction_fee_rate = st.slider("경매장 수수료율 (%)", min_value=0.0, max_value=5.0, value=2.2, step=0.1)

st.markdown("---")
st.header("🛠️ 2. 공식 사고 수리 이력 체크")
selected_accident = {}
for section_title, parts in all_car_parts.items():
    st.markdown(f"##### {section_title}")
    part_items = list(parts.items())
    for i in range(0, len(part_items), 4):
        chunk = part_items[i:i+4]
        cols = st.columns(4)
        for idx, (part_name, rank) in enumerate(chunk):
            with cols[idx]:
                status = st.selectbox(f"{part_name}", ["정상", "교환(X)", "판금/용접(W)"], key=f"acc_{part_name}")
                if status != "정상":
                    selected_accident[part_name] = {"rank": rank, "status": status}

st.markdown("---")
st.header("🎨 3. 현장 도색 필요 부위 (상품화 비용)")
selected_paint_parts = []
for section_title, parts in all_car_parts.items():
    if "골격" in section_title: continue
    st.markdown(f"##### {section_title}")
    part_items = list(parts.items())
    for i in range(0, len(part_items), 4):
        chunk = part_items[i:i+4]
        cols = st.columns(4)
        for idx, (part_name, rank) in enumerate(chunk):
            with cols[idx]:
                if st.checkbox(f"{part_name} 도색 필요", key=f"paint_{part_name}"):
                    selected_paint_parts.append(part_name)

st.markdown("---")

# 연산 및 리포트 대시보드 출력 파트 (들여쓰기 및 문자열 포맷팅 오류 완전 해결)
if st.button("📊 약관 보정식 기준 최고 입찰가 산출", type="primary", use_container_width=True):
    is_imp = (origin == "수입")
    engine = OfficialMarketEvaluator(
        is_import=is_imp, car_type=car_type, reg_year=reg_year, reg_month=reg_month,
        base_price_manwon=base_price, eval_year=eval_year, eval_month=eval_month,
        promotion_discount=promotion_discount
    )
    
    metrics = engine.calculate_official_metrics()
    accident_penalty, logs = engine.calculate_market_accident_penalty(selected_accident)
    paint_penalty = len(selected_paint_parts) * paint_unit_cost

    final_car_value = max(0, metrics["corrected_base_price"] - accident_penalty - paint_penalty)
    fee_factor = 1 + (auction_fee_rate / 100)
    max_bid_price = max(0, round((final_car_value - fixed_cost - target_margin) / fee_factor))

    # 🎯 산출 리포트 출력 파트
    st.header(f"🎯 산출 리포트 (차량 경과 나이: {metrics['factor_score']}개월 차)")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    with col_res1:
        st.metric(label="📊 최종 보정가격 (제11조 적용 완료)", value=f"{round(metrics['corrected_base_price'], 1):,} 만원")
    with col_res2:
        st.metric(label="📈 제12조 전년도 보정가격 (10% 가산)", value=f"{metrics['prev_year_corrected_price']:,} 만원")
    with col_res3:
        st.metric(label="🏁 최종 최고 입찰가 (Max Bid)", value=f"{max_bid_price:,} 만원")

    st.subheader("📋 제11조 약관 보정 및 감액 상세 내역")
    metrics_data = {
        "보정 항목 명세": [
            "원시 기준가액 (보정 전)", 
            "ⓐ 월별 보정액 차감 (나이 위치)", 
            "ⓑ 특성값 보정액 차감 (프로모션)", 
            "최종 보정 결과액"
        ],
        "적용 값 및 산출 근거": [
            f"{round(metrics['raw_base_price'], 1):,} 만원 (출고가 {base_price}만 × 잔가율 {metrics['factor_depreciation_rate']}%)",
            f"-{round(metrics['month_correction_val'], 1):,} 만원 ({metrics['position_name']} ➡️ 기준가의 {metrics['month_loss_rate_percent']:.1f}% 감가)",
            f"-{round(metrics['feature_correction_val'], 1):,} 만원 (구간 감액 {metrics['promo_cut']}만 × 잔가율)",
            f"**{round(metrics['corrected_base_price'], 1):,} 만원** (감가 후 최종 차량 베이스 가격)"
        ]
    }
    st.table(metrics_data)

    if logs:
        st.subheader("💥 선택된 사고 감가 내역")
        for p_name, log_txt in logs.items():
            st.warning(f"• {p_name} ── {log_txt}")