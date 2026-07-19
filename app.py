import streamlit as st

# 🚨 Streamlit 설정은 무조건 코드 최상단에 딱 한 번만!
st.set_page_config(page_title="공식 감가율 기준 경매 매입 시스템", page_icon="🚗", layout="wide")

# ==========================================
# 1. 약관 규정 기준 공식 연산 엔진
# ==========================================
class OfficialMarketEvaluator:
    def __init__(self, is_import: bool, car_type: str, reg_year: int, reg_month: int, base_price_manwon: int):
        self.is_import = is_import
        self.car_type = car_type  # "승용, 다목적형" 또는 "화물"
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.base_price_manwon = base_price_manwon
        
        # 기준 시점 (2026년 7월 고정)
        self.current_year = 2026
        self.current_month = 7

    def calculate_official_metrics(self):
        """제8조 및 제9조에 의거한 공식 사용년, 사용월, 계수, 잔가율 산출"""
        # 가. 사용년 산출식 = 평가연도의 년 - 최초등록연도의 년
        usage_years = self.current_year - self.reg_year
        if usage_years < 0: usage_years = 0

        # 나. 사용월 산출식 = (사용년 × 12) + 잔여월수 (평가월 - 등록월)
        remaining_months = self.current_month - self.reg_month
        usage_months = (usage_years * 12) + remaining_months
        if usage_months < 0: usage_months = 0

        # 감가율 계수 산출 = 11 + (사용년 × 12) + 평가월 수
        factor_score = 11 + (usage_years * 12) + usage_months

        # 2. 사용년 계수 적용 (제8조 2항)
        if not self.is_import:  # 국산차
            if usage_years <= 2: usage_year_factor = 1.0
            elif usage_years == 3: usage_year_factor = 0.9
            elif usage_years == 4: usage_year_factor = 0.8
            else: usage_year_factor = 0.7
        else:  # 수입차
            if usage_years <= 2: usage_year_factor = 1.0
            elif usage_years in [3, 4]: usage_year_factor = 0.9
            elif usage_years in [5, 6]: usage_year_factor = 0.8
            else: usage_year_factor = 0.7

        # 3. 행정안전부 잔가율표 적용 (제9조)
        residual_rate = 0.0
        if self.car_type == "승용, 다목적형":
            if not self.is_import:  # 국산 승용
                if usage_years <= 3: residual_rate = 0.518
                elif usage_years == 4: residual_rate = 0.437
                elif usage_years == 5: residual_rate = 0.368
                elif usage_years == 6: residual_rate = 0.311
                else: residual_rate = 0.262
            else:  # 수입 승용
                if usage_years <= 3: residual_rate = 0.500
                elif usage_years == 4: residual_rate = 0.412
                elif usage_years == 5: residual_rate = 0.340
                elif usage_years == 6: residual_rate = 0.281
                else: residual_rate = 0.232
        else:  # 화물
            if not self.is_import:  # 국산 화물
                if usage_years <= 3: residual_rate = 0.510
                elif usage_years == 4: residual_rate = 0.426
                elif usage_years == 5: residual_rate = 0.357
                elif usage_years == 6: residual_rate = 0.298
                else: residual_rate = 0.250
            else:  # 수입 화물
                if usage_years <= 3: residual_rate = 0.510
                elif usage_years == 4: residual_rate = 0.500
                elif usage_years == 5: residual_rate = 0.426
                elif usage_years == 6: residual_rate = 0.385
                else: residual_rate = 0.372

        # 가. 기준가격 산출식 = 신차 출고 가격 × 잔가율
        base_evaluated_price = self.base_price_manwon * residual_rate

        return {
            "usage_years": usage_years,
            "usage_months": usage_months,
            "factor_score": factor_score,
            "usage_year_factor": usage_year_factor,
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
st.caption("제8조(사용연수와 사용월수) 및 제9조(잔가율표) 행정안전부 고시 공식 산출식을 100% 적용하여 매입 마지노선을 연산합니다.")

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
    reg_year = st.number_input("최초등록년도", min_value=2000, max_value=2026, value=2022, step=1)
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
    
    # 엔진 구동
    engine = OfficialMarketEvaluator(
        is_import=is_imp, 
        car_type=car_type, 
        reg_year=reg_year, 
        reg_month=reg_month, 
        base_price_manwon=base_price
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
    st.header("🎯 약관 규정 감가율 산출 리포트 (2026년 7월 기준)")
    
    # 1단계 크리티컬 메트릭 박스
    col_res1, col_res2, col_res3 = st.columns(3)
    with col_res1:
        st.metric(label="📊 가. 산출 기준가격 (신차 × 잔가율)", value=f"{round(metrics['base_evaluated_price'], 1):,} 만원")
    with col_res2:
        st.metric(label="📉 사고/상품화 총 감가액", value=f"-{accident_penalty + paint_penalty:,} 만원")
    with col_res3:
        st.metric(label="🏁 최종 추천 최고 입찰가 (Max Bid)", value=f"{max_bid_price:,} 만원", delta=f"마진 {target_margin}만 확보")

    # 2단계 상세 산출 근거 테이블 제공
    st.subheader("📋 약관 조항별 상세 산출 내역")
    
    metrics_data = {
        "산출 항목": [
            "제8조 1항 가. 사용년 산출", 
            "제8조 1항 나. 사용월(잔여월 반영) 산출", 
            "제8조 1항 나. 감가율 계수 산출 식", 
            "제8조 2항. 사용년 계수", 
            "제9조 잔가율표 고시 잔가율 (%)"
        ],
        "적용 공식 및 값": [
            f"{metrics['usage_years']}년 경과 (2026 - {reg_year})",
            f"{metrics['usage_months']}개월 ({metrics['usage_years']}년 × 12 + 잔여 {7 - reg_month}개월)",
            f"계수: {metrics['factor_score']} (11 + {metrics['usage_years'] * 12} + {metrics['usage_months']})",
            f"{metrics['usage_year_factor']} 적용",
            f"**{metrics['residual_rate'] * 100:.1f}%** ({origin} / {car_type} / {metrics['usage_years']}년 규격)"
        ]
    }
    st.table(metrics_data)

    # 사고 발생 시 상세 로그 출력
    if logs:
        st.subheader("💥 선택된 감가 대상 수리 이력 명세")
        for p_name, log_txt in logs.items():
            st.warning(f"• {p_name} ── {log_txt}")

    st.markdown("---")
    st.info(f"💡 **최종 서머리 브리핑**: 본 차량은 행정안전부 고시 기준에 의해 **{metrics['residual_rate'] * 100:.1f}%**의 잔가율이 확보되어 **{round(metrics['base_evaluated_price'], 1):?}만 원**이 최초 기준 가격으로 설정되었습니다. 이후 사고 감가 및 부대비용을 역산한 최종 낙찰 마지노선은 **[{max_bid_price:,}만 원]** 입니다.")