import streamlit as st
import math

# ==========================================
# 1. 기준서 기반 경매 평가 엔진 (제22조 공식 완벽 구현)
# ==========================================
class GuidelineAuctionEvaluator:
    def __init__(self, is_import: bool, displacement: int, reg_year: int, reg_month: int, mileage: int, base_price_manwon: int):
        self.is_import = is_import
        self.displacement = displacement
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.mileage = mileage
        self.base_price_manwon = base_price_manwon
        
        # 기준 시점 (2026년 7월)
        self.current_year = 2026
        self.current_month = 7

    def get_tier_and_coefficient(self):
        """[제7조] 승용형/다목적형 자동차 배기량 등급 및 등급계수(α)"""
        if self.displacement >= 3600: tier, coef = "특C", 2.2 if not self.is_import else 2.7
        elif self.displacement >= 2900: tier, coef = "특B", 1.8 if not self.is_import else 2.5
        elif self.displacement >= 2400: tier, coef = "특A", 1.5 if not self.is_import else 2.0
        elif self.displacement >= 2100: tier, coef = "I", 1.4 if not self.is_import else 1.7
        elif self.displacement >= 1700: tier, coef = "II", 1.2 if not self.is_import else 1.4
        elif self.displacement >= 1300: tier, coef = "III", 1.0 if not self.is_import else 1.2
        elif self.displacement >= 1100: tier, coef = "IV", 0.9 if not self.is_import else 1.1
        else: tier, coef = "경", 0.8 if not self.is_import else 1.0
        return tier, coef

    def get_usage_period_and_rate(self):
        """[제8조] 경과 연식에 따른 가치 잔존율 산출"""
        usage_years = self.current_year - self.reg_year
        remaining_months = self.current_month - self.reg_month
        usage_months = (usage_years * 12) + remaining_months
        if usage_months < 0: usage_months = 0
        
        # 국산/수입 차별화된 연식 감가율 가이드
        if not self.is_import:
            if usage_years <= 1: age_rate = 0.85
            elif usage_years == 2: age_rate = 0.75
            elif usage_years == 3: age_rate = 0.65
            elif usage_years == 4: age_rate = 0.55
            elif usage_years == 5: age_rate = 0.48
            else: age_rate = max(0.10, 0.45 - (usage_years - 6) * 0.05)
        else:
            if usage_years <= 1: age_rate = 0.80
            elif usage_years == 2: age_rate = 0.68
            elif usage_years == 3: age_rate = 0.58
            elif usage_years == 4: age_rate = 0.48
            elif usage_years == 5: age_rate = 0.40
            else: age_rate = max(0.05, 0.35 - (usage_years - 6) * 0.06)
            
        return usage_years, usage_months, round(age_rate, 2)

    def calculate_guideline_accident(self, selected_accident, rank_coef_table):
        """[제22조] 27~29p 사고수리이력 감가계수 정밀 연산"""
        if not selected_accident:
            return 0, 0, {}

        total_gamma_coef = 0.0
        max_rank_coef = 0.0
        detail_logs = {}

        for part, data in selected_accident.items():
            rank = data["rank"]
            status = data["status"]
            guideline_coef = data["coef"]  # 27~29페이지에 명시된 부위별 고유 계수
            
            # 교환(X)은 계수 100% 반영, 판금/용접(W)은 50% 반감 적용
            repair_factor = 1.0 if status == "교환(X)" else 0.5
            current_part_gamma = guideline_coef * repair_factor
            
            total_gamma_coef += current_part_gamma
            
            # 26페이지 4번 표에 따른 랭크별 적용계수 추출
            r_coef = rank_coef_table.get(rank, 1.0)
            if r_coef > max_rank_coef:
                max_rank_coef = r_coef
                
            detail_logs[part] = f"{status} ──> 적용 계수: {current_part_gamma:.2f} (기준 고유치: {guideline_coef})"

        # 예외 규칙: 1랭크 부위 딱 1곳만 단독 교환(X)된 경우 최종 감가계수합의 50% 경감
        if len(selected_accident) == 1:
            only_part = list(selected_accident.values())[0]
            if only_part["rank"] == "1랭크" and only_part["status"] == "교환(X)":
                total_gamma_coef *= 0.5
                detail_logs[list(selected_accident.keys())[0]] += " [★1랭크 단독교환 50% 감면 적용]"

        if total_gamma_coef == 0:
            return 0, 0, detail_logs

        # 제22조 공식: (√(차량가격 * 감가계수합) / 4.8) * 랭크별 적용계수
        inside_sqrt = self.base_price_manwon * total_gamma_coef
        final_penalty = (math.sqrt(inside_sqrt) / 4.8) * max_rank_coef
        
        return round(final_penalty, 2), total_gamma_coef, detail_logs

# ==========================================
# 2. Streamlit 웹 UI 및 데이터 세팅
# ==========================================
st.set_page_config(page_title="2026 자동차진단평가 기준서 시스템", page_icon="📝", layout="wide")

st.title("📝 2026 기준서 완벽 매칭 자동차 경매 산출기")
st.caption("기준서 26~29페이지에 수록된 승용·다목적형 랭크별 적용계수 및 부위별 사고수리이력 감가계수를 완벽히 공학적으로 역산합니다.")

# 26페이지 4번 표 (승용형, 다목적형 기준 국산/수입 동일)
rank_coef_table = {"1랭크": 1.0, "2랭크": 1.4, "A랭크": 1.6, "B랭크": 1.8, "C랭크": 2.0}

# 27~29페이지 사고수리이력 감가계수 마스터 테이블 (부위별 정확한 수치 세팅)
guideline_parts_master = {
    "🔻 외판 단순 수리 부위 (1랭크)": {
        "후드": {"rank": "1랭크", "coef": 0.15},
        "프론트 펜더": {"rank": "1랭크", "coef": 0.15},
        "도어(앞/뒤)": {"rank": "1랭크", "coef": 0.15},
        "트렁크 리드": {"rank": "1랭크", "coef": 0.15},
        "라디에이터 서포트(볼트조립)": {"rank": "1랭크", "coef": 0.10}
    },
    "🔻 외판 용접 결합 부위 (2랭크)": {
        "쿼터 패널(뒤휀더)": {"rank": "2랭크", "coef": 0.30},
        "루프 패널": {"rank": "2랭크", "coef": 0.30},
        "사이드 실 패널": {"rank": "2랭크", "coef": 0.30}
    },
    "🔺 주요 골격 경미 부위 (A랭크)": {
        "프론트 패널": {"rank": "A랭크", "coef": 0.50},
        "리어 패널": {"rank": "A랭크", "coef": 0.50},
        "트렁크 플로어 패널": {"rank": "A랭크", "coef": 0.50}
    },
    "🔺 주요 골격 핵심 부위 (B/C랭크)": {
        "사이드 멤버": {"rank": "B랭크", "coef": 0.80},
        "휠 하우스": {"rank": "B랭크", "coef": 0.80},
        "필러 패널(A/B/C)": {"rank": "B랭크", "coef": 0.80},
        "대쉬 패널": {"rank": "C랭크", "coef": 1.20},
        "플로어 패널": {"rank": "C랭크", "coef": 1.20}
    }
}

# --------------------------------------------------
# 섹션 1: 차량 기본 스펙 세팅
# --------------------------------------------------
st.header("📝 1. 평가 차량 정보 세팅")
col1, col2, col3 = st.columns(3)

with col1:
    origin = st.selectbox("차량 제조국 구분", ["국산", "수입"])
    displacement = st.number_input("배기량 (cc)", min_value=100, max_value=10000, value=2500, step=100)
    base_price = st.number_input("기준 가격 (신차가격) (만원)", min_value=0, value=4500, step=100)

with col2:
    reg_year = st.number_input("최초 등록 연도", min_value=2000, max_value=2026, value=2023, step=1)
    reg_month = st.slider("최초 등록 월", min_value=1, max_value=12, value=3)
    mileage = st.number_input("현재 주행거리 (km)", min_value=0, max_value=1000000, value=50000, step=1000)

with col3:
    target_margin = st.number_input("희망 매입 마진 (만원)", min_value=0, value=150, step=10)
    fixed_cost = st.number_input("상사 이전 및 부대 비용 (만원)", min_value=0, value=60)
    paint_unit_cost = st.number_input("🎨 판당 현장 도색 단가 (만원)", min_value=0, value=15, step=1)
    auction_fee_rate = st.slider("경매 수수료율 (%)", min_value=0.0, max_value=5.0, value=2.2, step=0.1)

st.markdown("---")

# --------------------------------------------------
# 섹션 2: 27~29p 사고수리 체크
# --------------------------------------------------
st.header("🛠️ 2. 기준서 27~29p 부위별 사고수리이력 입력")
st.caption("기준서의 부위별 고유 감가계수가 내부 연산식에 대입됩니다.")

selected_accident = {}
for section_title, parts in guideline_parts_master.items():
    st.markdown(f"##### {section_title}")
    part_items = list(parts.items())
    for i in range(0, len(part_items), 4):
        chunk = part_items[i:i+4]
        cols = st.columns(4)
        for idx, (part_name, info) in enumerate(chunk):
            with cols[idx]:
                status = st.selectbox(f"{part_name}", ["정상", "교환(X)", "판금/용접(W)"], key=f"acc_{part_name}")
                if status != "정상":
                    selected_accident[part_name] = {
                        "rank": info["rank"],
                        "status": status,
                        "coef": info["coef"]
                    }

st.markdown("---")

# --------------------------------------------------
# 섹션 3: 상품화 도색 체크
# --------------------------------------------------
st.header("🎨 3. 외관 도색/칠 스크래치 필요 판수 입력")
selected_paint_parts = []
for section_title, parts in guideline_parts_master.items():
    if "골격" in section_title: continue
    st.markdown(f"##### {section_title}")
    part_items = list(parts.items())
    for i in range(0, len(part_items), 4):
        chunk = part_items[i:i+4]
        cols = st.columns(4)
        for idx, (part_name, info) in enumerate(chunk):
            with cols[idx]:
                if st.checkbox(f"{part_name} 도색", key=f"paint_{part_name}"):
                    selected_paint_parts.append(part_name)

st.markdown("---")

# --------------------------------------------------
# 섹션 4: 원클릭 연산 결과 출력
# --------------------------------------------------
if st.button("📊 기준서 공식 기반 최종 경매가 산출", type="primary", use_container_width=True):
    is_imp = (origin == "수입")
    
    # 클래스 객체 생성
    evaluator = GuidelineAuctionEvaluator(is_import=is_imp, displacement=displacement, reg_year=reg_year, reg_month=reg_month, mileage=mileage, base_price_manwon=base_price)
    
    tier_name, tier_alpha = evaluator.get_tier_and_coefficient()
    u_year, u_month, age_rate = evaluator.get_usage_period_and_rate()

    # 1. 연식 경과 기본 다운금액 계산
    age_based_value = base_price * age_rate
    age_penalty = base_price - age_based_value

    # 2. 27~29p 마스터 테이블 적용 사고 감가 계산
    accident_penalty, sum_coef, logs = evaluator.calculate_guideline_accident(selected_accident, rank_coef_table)
    
    # 3. 상품화 도색 판수 계산
    paint_count = len(selected_paint_parts)
    paint_penalty = paint_count * paint_unit_cost

    # 4. 종합 평가 가치 및 최종 입찰 마지노선 수립
    total_reduction = age_penalty + accident_penalty + paint_penalty
    final_evaluated_value = max(0, base_price - total_reduction)

    fee_factor = 1 + (auction_fee_rate / 100)
    max_bid_price = (final_evaluated_value - fixed_cost - target_margin) / fee_factor
    max_bid_price = max(0, round(max_bid_price))

    # 결과 대시보드 시각화
    st.header("🎯 자동차진단평가 기준서 분석 보고서")
    
    st.subheader("📅 차량 기본 가치 감정 상태")
    st.info(f"• **{origin}차** {displacement}cc ──> **{tier_name}급** 적용 (체급 계수 α: {tier_alpha})\n"
            f"• 등록일 기준 **{u_year}년 {u_month%12}개월** 경과 ──> 기준 잔존율 **{int(age_rate*100)}%** 배정")

    if logs:
        st.subheader("📋 기준서 27~29p 수리이력 감가 산출 로그")
        for part_title, log_msg in logs.items():
            st.text(f"  • {part_title} : {log_msg}")
        st.caption(f"📝 최종 합산 감가계수(Σ): {sum_coef:.2f} / 최고 랭크 적용계수: {max(rank_coef_table.values()) if not selected_accident else rank_coef_table[max(selected_accident.values(), key=lambda x: x['rank'])['rank']]}")

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric(label="🏁 경매장 낙찰 마지노선 (최대 입찰가)", value=f"{max_bid_price:,} 만원")
        st.success(f"📉 경과 연식 반영 자동 다운 금액: -{round(age_penalty):,} 만원")

    with res_col2 if 'res_col2' in locals() else col_res2:
        st.metric(label="📉 종합 감가액 (연식+사고+도색)", value=f"-{round(total_reduction):,} 만원")
        st.text(f"  • 연식 경과 기본 감가액: {round(age_penalty):,} 만원")
        st.text(f"  • 기준서 제22조 사고 감가액: {accident_penalty:,} 만원")
        st.text(f"  • 상품화 도색 비용 ({paint_count}판): {paint_penalty:,} 만원")

    st.markdown("---")
    st.warning(f"💡 **평가 종합 의견**: 본 차량은 기준서 공식에 입각하여 연식 감가 및 27~29p 사고 이력 감가, 도색비를 최종 제했을 때 **{final_evaluated_value:,}만 원**의 가치를 가집니다. 설정하신 마진과 이전 비용을 고려할 때 경매장 패들은 최대 **[{max_bid_price:,}만 원]**까지만 응찰하는 것이 안전합니다.")