# 🎯 산출 리포트 출력 파트 (오타 수정본)
    st.header(f"🎯 산출 리포트 (차량 경과 나이: {metrics['factor_score']}개월 차)")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    with col_res1:
        # :?로 되어 있던 오타를 :, (천단위 쉼표)로 수정했습니다.
        st.metric(label="📊 최종 보정가격 (제11조)", value=f"{round(metrics['corrected_base_price'], 1):,} 만원")
    with col_res2:
        st.metric(label="📈 제12조 전년도 보정가격", value=f"{metrics['prev_year_corrected_price']:,} 만원")
    with col_res3:
        st.metric(label="🏁 최종 최고 입찰가 (Max Bid)", value=f"{max_bid_price:,} 만원")

    st.subheader("📋 월별 보정 및 특성값 보정 매칭 내역")
    metrics_data = {
        "보정 항목": ["경과 개월수 기준 위치", "ⓐ 월별 보정액 차감", "ⓑ 특성값 보정액 차감", "최종 보정 결과"],
        "적용 값 및 산출 근거": [
            f"{metrics['position_name']} (인덱스 {metrics['factor_score']})",
            # 이곳의 :? 오타도 :,로 수정 완료
            f"-{round(metrics['month_correction_val'], 1):,} 만원 (기준가액의 {metrics['month_loss_rate_percent']:.1f}% 감가)",
            f"-{round(metrics['feature_correction_val'], 1):,} 만원 (구간 감액 {metrics['promo_cut']}만 × 잔가율)",
            f"**{round(metrics['corrected_base_price'], 1):,} 만원**"
        ]
    }
    st.table(metrics_data)