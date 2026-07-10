import streamlit as st

st.set_page_config(page_title="중고차 경매 입찰가 산출 시스템", page_icon="📈", layout="wide")

st.title("📈 실전 중고차 경매 최적 입찰가 산출기")
st.caption("자격증 시험용 공식이 아닌, 실제 소매 시세와 시장 감가를 반영한 매입용 계산기입니다.")

# 1. 목표 차량 시장 데이터 입력
st.header("📝 1. 목표 차량 시장 시세 및 목표 설정")
col1, col2, col3 = st.columns(3)

with col1:
    market_price = st.number_input("현재 시장 소매 시세 (만원)", min_value=0, value=3000, step=50, help="엔카/KB차차차 등에서 동일 연식/주행거리 무사고 차가 판매되는 평균 가격")
    target_margin = st.number_input("내가 남기고 싶은 최소 마진 (만원)", min_value=0, value=150, step=10)

with col2:
    auction_fee_rate = st.slider("경매장 수수료율 (%)", min_value=0.0, max_value=5.0, value=2.2, step=0.1)
    merchant_fee = st.number_input("기타 부대비용 총합 (만원)", min_value=0, value=60, help="성능비, 탁송료, 상품화 작업비(광택/도색) 등")

with col3:
    is_premium_car = st.checkbox("수입차 또는 대형 대형 프리미엄 차종인가요?", value=False, help="체크 시 사고 부위별 마켓 감가액이 1.5배 상향 적용됩니다.")

st.markdown("---")

# 2. 현실적인 시장 사고 감가 설정 (딜러 매입 감가 기준)
st.header("🚘 2. 차량 사고 수리 및 상품화 필요 부위 선택")
st.info("💡 실제 시장에서는 부위별로 차값에서 직접 정액 감가를 진행합니다.")

# 시장 감가 리스트 (무사고 시세 대비 깎이는 대략적인 금액)
market_depreciation_rules = {
    "후드(본네트) 교환": 40,
    "앞휀더 교환 (한쪽당)": 25,
    "도어 교환 (한쪽당)": 35,
    "트렁크 리드 교환": 40,
    "쿼터패널(뒤휀더) 잘라 붙임": 80,
    "루프 패널 교환": 150,
    "사이드멤버(주요골격) 손상/교환": 250,
    "휠하우스(주요골격) 손상/교환": 350,
    "인사이드패널(골격 미세) 수리": 70,
    "단순 도색/판금 필요 (판당 수리비 부수기)": 15
}

selected_damages = []
st.markdown("#### 🔍 감가 요인 체크리스트")

# 2열로 나누어 체크박스 배치
dmg_items = list(market_depreciation_rules.items())
col_d1, col_d2 = st.columns(2)

for idx, (label, cost) in enumerate(dmg_items):
    # 프리미엄/수입차 가중치 적용
    actual_cost = round(cost * 1.5) if is_premium_car else cost
    
    if idx % 2 == 0:
        with col_d1:
            if st.checkbox(f"{label} (-{actual_cost}만원)", key=f"dmg_{idx}"):
                selected_damages.append(actual_cost)
    else:
        with col_d2:
            if st.checkbox(f"{label} (-{actual_cost}만원)", key=f"dmg_{idx}"):
                selected_damages.append(actual_cost)

st.markdown("---")

# 3. 입찰가 산출 로직
if st.button("📊 경매 최고 입찰 마지노선 산출하기", type="primary", use_container_width=True):
    
    # 총 사고 감가액
    total_market_damage = sum(selected_damages)
    
    # 사고 감가가 반영된 이 차량의 '실제 매입 가치'
    damaged_car_value = market_price - total_market_damage
    
    # 경매장 수수료 계산 (낙찰가 기준 2.2% 역산 가제작)
    # 실제 낙찰가를 X라 하면, X + X*수수료율 + 부대비용 + 마진 = 차량가치
    # X * (1 + rate) = 차량가치 - 부대비용 - 마진
    fee_factor = 1 + (auction_fee_rate / 100)
    
    max_bid_price = (damaged_car_value - merchant_fee - target_margin) / fee_factor
    max_bid_price = round(max_bid_price)
    
    # 수수료 및 최종 지출 분석
    final_fee = round(max_bid_price * (auction_fee_rate / 100))
    total_invested = max_bid_price + final_fee + merchant_fee
    expected_profit = market_price - total_market_damage - total_invested

    # 결과 표출
    st.header("🎯 경매 입찰 전략 레포트")
    
    res_c1, res_c2 = st.columns(2)
    with res_c1:
        st.metric(label="🏁 경매장 최대로 적어낼 입찰가 (Max Bid)", value=f"{max_bid_price:,} 만원")
        st.caption(f"⚠️ 이 금액보다 비싸게 낙찰받으면 목표하신 {target_margin}만원 마진을 확보할 수 없습니다.")
        
    with res_c2:
        st.metric(label="💰 예상 총 투자 비용 (차값+수수료+부대비용)", value=f"{total_invested:,} 만원")
        st.text(f"• 차량 자체 감가액: -{total_market_damage} 만원")
        st.text(f"• 경매장 예상 수수료: {final_fee} 만원")

    st.markdown("---")
    if max_bid_price <= 0:
        st.error("🚨 감가액과 부대비용이 너무 커서 입찰 불가능한 차량입니다. 다른 매물을 찾아보세요!")
    else:
        st.success(f"💡 결론: 경매장에서 **[{max_bid_price:,}만 원]** 이하로 낙찰받으면, 무사고 시세 {market_price}만 원짜리 차량을 감가 및 비용 정산 후에도 안전하게 가져오실 수 있습니다.")