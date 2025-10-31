import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 사용할 CSV 파일명 (사용자 파일과 동일)
CSV_FILENAME = "서울시 상권분석서비스(추정매출-자치구).csv"

st.set_page_config(
    page_title="강남구 카페 매출 분석 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 데이터 로딩 및 분석 함수 ---

@st.cache_data
def load_and_analyze_data():
    """
    CSV 파일을 불러와 인코딩을 처리하고, 강남구 '커피-음료' 업종 데이터를 분석합니다.
    """
    df = None
    
    # 인코딩 순차 시도: utf-8 -> euc-kr -> cp949
    for encoding_type in ['utf-8', 'euc-kr', 'cp949']:
        try:
            df = pd.read_csv(CSV_FILENAME, encoding=encoding_type)
            st.sidebar.success(f"데이터 로드 성공! (인코딩: {encoding_type})")
            break
        except Exception:
            continue

    if df is None:
        st.error(f"데이터 파일을 로드하는 데 실패했습니다. 파일명 '{CSV_FILENAME}'이 같은 폴더에 있는지, 인코딩에 문제가 없는지 확인해 주세요.")
        st.stop()
        
    # 컬럼 이름의 공백 제거 및 전처리
    df.columns = [c.strip() for c in df.columns]

    # 숫자 컬럼을 숫자로 변환하고 결측치를 0으로 처리 (분석의 안정성 확보)
    sales_cols = [col for col in df.columns if '매출_금액' in col or '매출_건수' in col]
    for col in sales_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
             
    # --- 강남구 '커피-음료' 업종 데이터 필터링 ---
    df_filtered = df[
        (df['자치구_코드_명'] == '강남구') & 
        (df['서비스_업종_코드_명'] == '커피-음료')
    ].copy()
    
    if df_filtered.empty:
        st.warning("필터링 조건('강남구', '커피-음료')에 해당하는 데이터가 없습니다. CSV 파일을 확인해 주세요.")
        return None

    # --- 핵심 분석: 모든 행을 합산하여 정확한 전체 매출 계산 ---
    
    # 분석에 필요한 연령대 컬럼 목록
    age_cols = [col for col in df_filtered.columns if '연령대_' in col and '매출_금액' in col]
    
    # 연령대별 총 매출 합산
    age_sales_sum = df_filtered[age_cols].sum()
    
    # 주중/주말 총 매출 합산
    total_weekday_sales = df_filtered['주중_매출_금액'].sum()
    total_weekend_sales = df_filtered['주말_매출_금액'].sum()

    # 기준 분기 정보 추출 (데이터 범위 표시용)
    quarter_codes = df_filtered['기준_년분기_코드'].unique()
    quarter_range = f"{min(quarter_codes)} ~ {max(quarter_codes)}"
    
    
    # --- 차트 데이터 구조화 ---
    
    # 1. 연령대별 매출 데이터
    age_labels = ['10대', '20대', '30대', '40대', '50대', '60대 이상']
    age_data = pd.DataFrame({
        '연령대': age_labels,
        '총 매출액': [
            age_sales_sum['연령대_10_매출_금액'],
            age_sales_sum['연령대_20_매출_금액'],
            age_sales_sum['연령대_30_매출_금액'],
            age_sales_sum['연령대_40_매출_금액'],
            age_sales_sum['연령대_50_매출_금액'],
            age_sales_sum['연령대_60_이상_매출_금액'],
        ]
    })
    
    # 2. 주중/주말 매출 데이터
    day_sales_data = pd.DataFrame({
        '구분': ['주중 매출', '주말 매출'],
        '총 매출액': [total_weekday_sales, total_weekend_sales]
    })
    
    # 3. 전체 총 매출액 (메트릭 표시용)
    total_sales = df_filtered['당월_매출_금액'].sum()

    return {
        'age_data': age_data,
        'day_sales_data': day_sales_data,
        'total_sales': total_sales,
        'quarter_range': quarter_range
    }

# --- 차트 생성 함수 ---

def create_age_chart(df_age):
    """연령대별 매출 기여도 차트 (막대)"""
    fig = px.bar(
        df_age, 
        x='연령대', 
        y='총 매출액', 
        title='강남구 카페 연령대별 총 매출 기여도',
        color='연령대',
        color_discrete_sequence=px.colors.qualitative.Pastel,
        labels={'총 매출액': '총 매출액 (원)'}
    )
    fig.update_layout(
        title_x=0.5, 
        template="plotly_white",
        yaxis=dict(tickformat=',.0f'), # y축 콤마 포맷
    )
    return fig

def create_day_chart(df_day):
    """주중 vs 주말 소비 집중도 차트 (도넛)"""
    fig = go.Figure(data=[go.Pie(
        labels=df_day['구분'], 
        values=df_day['총 매출액'], 
        hole=.4,
        marker_colors=['#4c78a8', '#f58518'] # 파란색 계열, 주황색 계열
    )])
    
    fig.update_layout(
        title_text='주중 vs 주말 매출 비중 (도넛 차트)',
        title_x=0.5
    )
    
    fig.update_traces(
        hovertemplate='%{label}: %{value:,}원<br>점유율: %{percent}<extra></extra>',
        textinfo='percent+label'
    )

    return fig


# --- Streamlit 앱 메인 함수 ---

def main():
    st.title("☕ 강남구 '커피-음료' 업종 심층 분석")
    st.markdown("##### 서울시 상권 데이터를 기반으로 강남구 카페의 주요 소비 트렌드를 시각화합니다.")
    
    # 데이터 로드 및 분석
    data = load_and_analyze_data()
    
    if data is None:
        return # 분석 실패 시 중단

    age_data = data['age_data']
    day_sales_data = data['day_sales_data']
    total_sales = data['total_sales']
    quarter_range = data['quarter_range']
    
    # 1. 핵심 지표 (Metrics)
    st.subheader("🔑 핵심 지표 요약")
    
    col1, col2, col3 = st.columns(3)
    
    # 전체 매출액 (메트릭)
    col1.metric(
        label="강남구 카페 총 매출액 (데이터 범위: " + quarter_range + ")",
        value=f"{total_sales:,.0f} 원",
        help="분석 데이터에 포함된 강남구 '커피-음료' 업종의 모든 매출을 합산한 금액입니다."
    )
    
    # 20/30대 매출 기여도 계산
    sales_20s_30s = age_data[age_data['연령대'].isin(['20대', '30대'])]['총 매출액'].sum()
    pct_20s_30s = (sales_20s_30s / total_sales) * 100 if total_sales else 0
    
    col2.metric(
        label="20~30대 매출 기여율",
        value=f"{pct_20s_30s:.1f} %",
        help="강남구 카페 총 매출 중 20대와 30대가 차지하는 비중입니다."
    )
    
    # 주말 매출 기여도 계산
    weekend_sales = day_sales_data[day_sales_data['구분'] == '주말 매출']['총 매출액'].iloc[0]
    pct_weekend = (weekend_sales / total_sales) * 100 if total_sales else 0

    col3.metric(
        label="주말 매출 기여율",
        value=f"{pct_weekend:.1f} %",
        help="강남구 카페 총 매출 중 토/일요일 매출이 차지하는 비중입니다."
    )

    # 2. 시각화 섹션
    st.markdown("---")
    st.subheader("📊 상세 데이터 시각화")

    col_chart_age, col_chart_day = st.columns(2)
    
    with col_chart_age:
        st.plotly_chart(create_age_chart(age_data), use_container_width=True)
        st.info("💡 **인사이트:** 연령대별 기여도를 파악하여 주력 고객층을 명확히 할 수 있습니다.")
        
    with col_chart_day:
        st.plotly_chart(create_day_chart(day_sales_data), use_container_width=True)
        st.info("💡 **인사이트:** 주중/주말 매출 비중을 파악하여 인력 운용 및 마케팅 전략 수립에 활용할 수 있습니다.")

    st.markdown("---")
    st.caption("본 대시보드는 '서울시 상권분석서비스(추정매출-자치구)' 데이터를 기반으로 '강남구'의 '커피-음료' 업종을 분석한 결과입니다.")


if __name__ == "__main__":
    main()
