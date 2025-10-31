import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------
# 1. 데이터 로드 및 전처리 함수
# -----------------------------------------------------------

@st.cache_data
def load_data(file):
    """CSV 파일을 읽고 필요한 컬럼 이름을 정리하여 반환합니다."""
    # 인코딩 문제 발생 시 'cp949' 또는 'latin1' 등으로 변경해 보세요.
    df = pd.read_csv(file, encoding='utf-8')

    # 필요한 컬럼만 선택하고 이름 변경 (가독성 향상)
    df = df.rename(columns={
        '자치구_코드_명': '자치구명',
        '서비스_업종_코드_명': '업종명',
        '당월_매출_금액': '총_매출액',
        '당월_매출_건수': '총_매출건수',
        '연령대_10_매출_금액': '10대_매출',
        '연령대_20_매출_금액': '20대_매출',
        '연령대_30_매출_금액': '30대_매출',
        '연령대_40_매출_금액': '40대_매출',
        '연령대_50_매출_금액': '50대_매출',
        '연령대_60_이상_매출_금액': '60대_이상_매출'
    })
    return df

# -----------------------------------------------------------
# 2. 강남구 카페 데이터 추출 및 분석 함수
# -----------------------------------------------------------

def analyze_gangnam_cafe(df):
    """강남구의 '커피음료점' 데이터만 추출하여 분석합니다."""
    
    # 1. 강남구의 '커피음료점' 데이터 필터링
    df_gangnam_cafe = df[
        (df['자치구명'] == '강남구') & 
        (df['업종명'] == '커피-음료')
    ].copy()
    
    if df_gangnam_cafe.empty:
        st.error("❗ 오류: 파일에서 강남구의 커피-음료 데이터를 찾을 수 없습니다.")
        return None

    # 2. 연령대별 매출액 합산 (파일이 분기별 데이터라고 가정)
    age_cols = ['10대_매출', '20대_매출', '30대_매출', '40대_매출', '50대_매출', '60대_이상_매출']
    
    # 해당 연령대 컬럼의 데이터가 없는 경우 0으로 채우기 (안전한 처리를 위해)
    for col in age_cols:
        if col not in df_gangnam_cafe.columns:
            df_gangnam_cafe[col] = 0
            
    # 모든 분기의 합산 대신, 파일에 있는 데이터 (가장 최근 분기 데이터라고 가정)를 사용
    # 만약 파일에 여러 분기가 있다면 가장 최근 분기(가장 큰 '기준_년분기_코드')를 선택하거나 모두 합산해야 함.
    
    # 일단, 필터링된 데이터의 첫 번째 행을 대표 데이터로 사용합니다.
    data_row = df_gangnam_cafe.iloc[0]

    # 연령대별 매출 데이터를 시리즈로 변환
    age_sales = data_row[age_cols].sum()
    
    if age_sales == 0:
         st.warning("경고: 연령대별 매출액 합계가 0입니다. 데이터가 비어 있거나 누락되었을 수 있습니다.")
         return None

    # 연령대별 매출 비중 계산
    age_sales_df = pd.DataFrame({
        '연령대': [c.replace('_매출', '') for c in age_cols],
        '매출액': data_row[age_cols].values
    })
    
    # 총 매출 및 건수 (대표값)
    total_sales = data_row['총_매출액']
    total_count = data_row['총_매출건수']

    return age_sales_df, total_sales, total_count

# -----------------------------------------------------------
# 3. Streamlit 앱 메인 함수
# -----------------------------------------------------------

def main():
    st.set_page_config(layout="wide", page_title="강남구 카페 상권 분석", initial_sidebar_state="expanded")
    st.title("☕ 서울 강남구 '커피-음료' 상권 분석")
    st.markdown("---")

    # 1. 데이터 로드
    file_path = "서울시 상권분석서비스(추정매출-자치구).csv"
    try:
        df = load_data(file_path)
    except FileNotFoundError:
        st.error(f"❌ 오류: 파일을 찾을 수 없습니다. '{file_path}' 경로에 파일이 있는지 확인해 주세요.")
        st.stop()
    except Exception as e:
        st.error(f"❌ 데이터 로드 중 오류 발생: {e}")
        st.stop()

    # 2. 강남구 카페 데이터 분석
    analysis_result = analyze_gangnam_cafe(df)

    if analysis_result:
        age_sales_df, total_sales, total_count = analysis_result
        
        # 3. 핵심 지표 표시
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 분석 기준 분기", str(df['기준_년분기_코드'].iloc[0]))
        col2.metric("💰 총 추정 매출액 (원)", f"{total_sales:,.0f}원")
        col3.metric("🛒 총 매출 건수 (건)", f"{total_count:,.0f}건")
        st.markdown("---")
        
        # 4. 시각화 (Plotly 사용)
        st.header("📈 강남구 카페 연령대별 매출 비중 분석")
        
        # Plotly Pie Chart (원형 그래프)
        fig_pie = px.pie(
            age_sales_df, 
            values='매출액', 
            names='연령대', 
            title='연령대별 매출액 점유율 (파이 차트)',
            hole=0.3, # 도넛 모양
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
        
        # Plotly Bar Chart (막대 그래프)
        fig_bar = px.bar(
            age_sales_df.sort_values(by='매출액', ascending=False), 
            x='연령대', 
            y='매출액', 
            title='연령대별 매출액 (막대 차트)',
            color='연령대',
            color_discrete_sequence=px.colors.qualitative.Dark24,
            text='매출액' # 막대 위에 매출액 표시
        )
        fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_bar.update_layout(yaxis_title="매출액 (원)", xaxis_title="연령대")

        col_left, col_right = st.columns(2)
        with col_left:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_right:
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.markdown("---")
        st.subheader("💡 연령대별 매출 분석 시사점")
        
        # 매출액이 가장 높은 연령대 추출
        top_age = age_sales_df.loc[age_sales_df['매출액'].idxmax()]
        
        st.info(
            f"**가장 높은 매출액을 기록한 연령대:** {top_age['연령대']} ({top_age['매출액']:,.0f}원)\n\n"
            f"이는 강남구 카페 상권에서 해당 연령층을 **핵심 타겟**으로 설정하고, 그들의 소비 성향(고급화, 트렌디함, 편의성 등)에 맞는 전략을 수립해야 함을 시사합니다."
        )

# -----------------------------------------------------------
# 앱 실행
# -----------------------------------------------------------
if __name__ == "__main__":
    main()
