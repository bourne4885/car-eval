import streamlit as st
from datetime import datetime

# 🚨 Streamlit 설정은 무조건 코드 최상단에 딱 한 번만!
st.set_page_config(page_title="공식 감가율 기준 경매 매입 시스템", page_icon="🚗", layout="wide")

# ==========================================
# [데이터 고정] 보내주신 1~180 감가율 계수표 데이터 매핑
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
# 1. 약관 규정 기준 공식 연산 엔진
# ==========================================
class OfficialMarketEvaluator:
    def __init__(self, is_import: bool, car_type: str, reg_year: int, reg_month: int, base_price_manwon: int, eval_year: int, eval_month: int):
        self.is_import = is_import
        self.car_type = car_type  
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.base_price_manwon = base_price_manwon
        
        # 🌟 이제 고정값이 아니라 UI에서 입력받은 평가 시점을 대입합니다.
        self.current_year = eval_year
        self.current_month = eval_month

    def calculate_official_metrics(self):
        """제8조 및 제9조에 의거한 공식 사용년, 잔여월수, 계수, 잔가율 및 기준가격 산출"""
        # 1. 사용년 산출식 = 평가연도의 년 - 최초등록연도의 년
        usage_years = self.current_year - self.reg_year
        if usage_years < 0: usage_years = 0

        # 2. 잔여월수 산출식 = 평가연도의 월 - 최초등록연도의 월
        remaining_months = self.current_month - self.reg_month

        # 3. 감가율 계수 산출 = 11 + (사용년 × 12) + 평가월 수(잔여월수 대입)
        factor_score = 11 + (usage_years * 12) + remaining_months
        
        # 계수 값 안전 범위 보정
        lookup_key = factor_score
        if lookup_key < 1: lookup_key = 1
        if lookup_key > 180: lookup_key = 180

        # 4. 제공된 감가율표에서 해당 계수에 상응하는 감가율(%) 추출
        factor_depreciation_rate = DEPRECIATION_TABLE.get(lookup_key, 12.65)
        
        # 행정안전부 고시 제9조 기본 잔가율표 데이터 산출 (기존 정보 유지용)
        residual_rate = 0.0
        if self.car_type == "승용, 다목적형":
            if not self.is_import:
                if usage_years <= 3: residual_rate = 0.518
                elif usage_years == 4: residual_rate = 0.437
                elif usage_years == 5: residual_rate = 0.368
                elif usage_years == 6: residual_rate = 0.311
                else: residual_rate = 0.262
            else:
                if usage_years <= 3: residual_rate = 0.500
                elif usage_years == 4: residual_rate = 0.412
                elif usage_years == 5: residual_rate = 0.340
                elif usage_years == 6: residual_rate = 0.281
                else: residual_rate = 0.232
        else:
            if not self.is_import:
                if usage_years <= 3: residual_rate = 0.510
                elif usage_years == 4: residual_rate = 0.426
                elif usage_years == 5: residual_rate = 0.357
                elif usage_years == 6: residual_rate = 0.298
                else: residual_rate = 0.250
            else:
                if usage_years <= 3: residual_rate = 0.510
                elif usage_years == 4: residual_rate = 0.500
                elif usage_years == 5: residual_rate = 0.426
                elif usage_years == 6: residual_rate = 0.385
                else: residual_rate = 0.372

        # 5. 가. 기준가격 산출식 = 신차 출고 가격 × 감가율 계수의 감가율(%)
        base_evaluated_price = self.base_price_manwon * (factor_depreciation_rate / 100.0)

        return {
            "usage_years": usage_years,
            "remaining_months": remaining_months,
            "factor_score": factor_score,
            "factor_depreciation_rate": factor_depreciation_rate,
            "residual_rate": residual_rate,
            "base_evaluated_price": base_evaluated_price
        }

    def calculate_market_accident_penalty(self, selected_accident):
        """실전 시장 감가 테이블 (국산/수입 차별화 적용)"""
        if not selected_accident:
            return 0, {}

        market_price_table = {
            "국산": {"1랭크": 40, "2랭크": 100, "A랭크": 200, "B랭크": 350, "C랭크": 500},
            "수입": {"1랭크": 80, "2랭크": 180, "A랭크": 350, "B랭크": 600, "C랭크": 900}
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
            detail_logs[part] = f"{status} ──> 공식/시장 감가: -{current_penalty}만 원 ({rank} 기준)"
            
        return total_penalty, detail_logs


# ==========================================
# 2. Streamlit 웹 UI 화면 구성
# ==========================================
st.title("🚗 약관 규격 기준 중고차 경매 매입 산출기")
st.caption("제8조(사용연수와 사용월수) 및 제공해주신 1~180 정밀 감가율표 고시 산출식을 100% 적용하여 매입 마지노선을 연산합니다.")

# 🌟 시스템 오늘 날짜 가져오기
today = datetime.today()

# 상단에 평가 기준년월 가이드 및 선택창 배치
st.sidebar.header("📅 평가 시점 설정 (기준가격 산출용)")
eval_year = st.sidebar.number_input("평가 연도", min_value=2000, max_value=2100, value=today.year)
eval_month = st.sidebar.slider("평가 월", min_value=1, max_value=12, value=today.month)
st.sidebar.info(f"💡 현재 **[{eval_year}년 {eval_month}월]** 기준으로 감가 계수를 계산합니다. 필요시 사이드바에서 변경 가능합니다.")

all_car_parts = {
    "🔻 외판 단순 교환/판금 (1랭크)": {
        "후드": "1랭크", "프론트 펜더(좌)": "1랭크", "프론트 펜더(우)": "1랭크",
        "앞도어(좌)": "1랭크", "앞도어(우)": "1랭크", "뒷도어(좌)": "1랭크", "뒷도어(우)": "1랭크",
        "트렁크 리드": "1랭크"
    },
    "🔻 외판 주요 부위 (2랭크)": {
        "쿼터 패널(좌)": "2랭크", "쿼터 패널(우)": "2랭크", "루프 패널": "2랭크"
    },
    "🔺 주요 골격 경미 사고 (A랭크)": {
        "프론트 패널": "A랭크", "리어 패널": "A랭크", "트렁크 플로어 패널": "A랭크"
    },
    "🔺 주요 골격 중대 사고 (B/C랭크)": {
        "사이드 멤버(좌)": "B랭크", "사이드 멤버(우)": "B랭크", "휠 하우스(좌)": "B랭크", "휠 하우스(우)": "B랭크", "대쉬 패널": "C랭크"
    }
}

# 섹션 1: 차량 조건 설정
st.header("📝 1. 차량 기본 정보 및 약관 분류")
col1, col2, col3 = st.columns(3)

with col1:
    origin = st.selectbox("차량 구분", ["국산", "수입"])
    car_type = st.selectbox("행정 규격 차종 구분 (제9조)", ["승용, 다목적형", "화물"])
    base_price = st.number_input("신차 출고 가격 (부가세 포함 / 만원)", min_value=0, value=4000, step=100)

with col2:
    reg_year = st.number_input("최초등록년도", min_value=2000, max_value=eval_year, value=eval_year-4, step=1)
    reg_month = st.slider("최초등록월", min_value=1, max_value=12, value=1)
    target_margin = st.number_input("확보할 딜러 매입 마진 (만원)", min_value=0, value=150, step=10)

with col3:
    fixed_cost = st.number_input("상사 이전비 및 부대비용 (만원)", min_value=0, value=50)
    paint_unit_cost = st.number_input("🎨 판당 현장 도색 단가 (만원)", min_value=0, value=15 if origin == "국산" else 25, step=5)
    auction_fee_rate = st.slider("경매장 낙찰 수수료율 (%)", min_value=0.0, max_value=5.0, value=2.2, step=0.1)

st.markdown("---")

# 섹션 2: 사고 감가 선택
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

# 섹션 3: 외관 도색 선택
st.header("🎨 3. 현장 도색 필요 부위 (상품화 비용 추가 차감)")
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

# 섹션 4: 연산 실행 및 대시보드 출력
if st.button("📊 약관식 기준 최고 입찰가 산출", type="primary", use_container_width=True):
    is_imp = (origin == "수입")
    
    # 엔진 구동 (입력된 평가년월 전달)
    engine = OfficialMarketEvaluator(
        is_import=is_imp, 
        car_type=car_type, 
        reg_year=reg_year, 
        reg_month=reg_month, 
        base_price_manwon=base_price,
        eval_year=eval_year,
        eval_month=eval_month
    )
    
    # 공식 계수 연산 리포트 받아오기
    metrics = engine.calculate_official_metrics()
    
    # 사고 및 도색 감가 연산
    accident_penalty, logs = engine.calculate_market_accident_penalty(selected_accident)
    paint_count = len(selected_paint_parts)
    paint_penalty = paint_count * paint_unit_cost

    # 최종 감가율이 적용된 차량 가치 산출
    final_car_value = max(0, metrics["base_evaluated_price"] - accident_penalty - paint_penalty)

    # 역산 공식으로 최고 입찰 마지노선(Max Bid) 도출
    fee_factor = 1 + (auction_fee_rate / 100)
    max_bid_price = (final_car_value - fixed_cost - target_margin) / fee_factor
    max_bid_price = max(0, round(max_bid_price))

    # 결과 화면 대시보드 출력
    st.header(f"🎯 약관 규정 감가율 산출 리포트 ({eval_year}년 {eval_month}월 기준)")
    
    # 1단계 크리티컬 메트릭 박스
    col_res1, col_res2, col_res3 = st.columns(3)
    with col_res1:
        st.metric(label="📊 가. 산출 기준가격 (신차 × 계수별 감가율)", value=f"{round(metrics['base_evaluated_price'], 1):,} 만원")
    with col_res2:
        st.metric(label="📉 사고/상품화 총 감가액", value=f"-{accident_penalty + paint_penalty:,} 만원")
    with col_res3:
        st.metric(label="🏁 최종 추천 최고 입찰가 (Max Bid)", value=f"{max_bid_price:,} 만원", delta=f"마진 {target_margin}만 확보")

    # 2단계 상세 산출 근거 테이블 제공
    st.subheader("📋 약관 조항별 상세 산출 내역")
    
    metrics_data = {
        "산출 항목": [
            "제8조 1항 가. 사용년 산출", 
            "제8조 1항 나. 단서조항 잔여월수", 
            "감가율 계수 결과 값", 
            "★ 정밀 감가율표 연동 매칭 감가율(%)", 
            "제9조 고시 기본 잔가율 (%)"
        ],
        "적용 공식 및 값": [
            f"{metrics['usage_years']}년 경과 ({eval_year} - {reg_year})",
            f"{metrics['remaining_months']}개월 (평가월 {eval_month}월 - 등록월 {reg_month}월)",
            f"최종 계수: {metrics['factor_score']} (공식: 11 + {metrics['usage_years'] * 12} + {metrics['remaining_months']})",
            f"**{metrics['factor_depreciation_rate']}%** (제2항 감가율표 매칭 값)",
            f"{metrics['residual_rate'] * 100:.1f}% (연식 기준 참고용 고시)"
        ]
    }
    st.table(metrics_data)

    # 사고 발생 시 상세 로그 출력
    if logs:
        st.subheader("💥 선택된 감가 대상 수리 이력 명세")
        for p_name, log_txt in logs.items():
            st.warning(f"• {p_name} ── {log_txt}")

    st.markdown("---")
    st.info(f"💡 **최종 서머리 브리핑**: 본 차량은 {eval_year}년 {eval_month}월 기준 행정안전부 고시 계수 식에 의해 산출된 최종 계수 **[{metrics['factor_score']}]** 값에 매핑되어, 제공해주신 감가율표 기준 **{metrics['factor_depreciation_rate']}%**의 감가율이 반영되었습니다. 이에 따라 계산된 최초 기준 가격은 **{round(metrics['base_evaluated_price'], 1):,}만 원**이며, 사고 및 상품화 비용을 역산한 최종 낙찰 마지노선은 **[{max_bid_price:,}만 원]** 입니다.")