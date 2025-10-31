import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 사용할 CSV 파일명 (사용자 파일과 동일)
CSV_FILENAME = "서울시 상권분석서비스(추정매출-자치구).csv"

# 데이터 로딩 및 캐싱 (Streamlit의 성능 최적화 기능)
@st.cache_data
def load_and_analyze_data():
    """
    CSV 파일을 불러와 필요한 데이터를 분석합니다.
    """
    df = None
    
    # 1. 'utf-8' 인코딩 시도 (가장 보편적인 인코딩)
    try:
        df = pd.read_csv(CSV_FILENAME, encoding='utf-8')
    except UnicodeDecodeError:
        # 2. 'utf-8' 실패 시 'euc-kr' 또는 'cp949' 시도
        try:
            df = pd.read_csv(CSV_FILENAME, encoding='euc-kr')
        except Exception as e:
            st.error(f"데이터 파일을 로드하는 데 실패했습니다. 파일명 '{CSV_FILENAME}'과 인코딩을 확인해 주세요.")
            st.error(f"에러 상세: {e}")
            return None
    except Exception as e:
        # 기타 파일 로드 오류 처리 (예: 파일 경로 없음 등)
        st.error(f"데이터 파일을 로드하는 데 실패했습니다. 파일명 '{CSV_FILENAME}'과 경로를 확인해 주세요.")
        st.error(f"에러 상세: {e}")
        return None

    # 필요한 매출 컬럼을 숫자로 변환하고 결측치(NaN)를 0으로 처리
    sales_cols = [col for col in df.columns if '매출_금액' in col]
    for col in sales_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 1. 연령대별 매출 분석
    total_sales_20s = df['연령대_20_매출_금액'].sum()
    total_sales_30s = df['연령대_30_매출_금액'].sum()
    
    # 기타 연령대 합산 (10대, 40대, 50대, 60대 이상)
    other_ages_cols = [
        '연령대_10_매출_금액', '연령대_40_매출_금액', 
        '연령대_50_매출_금액', '연령대_60_이상_매출_금액'
    ]
    total_sales_others = df[other_ages_cols].sum().sum()

    age_sales_data = pd.DataFrame({
        '연령대': ['20대', '30대', '기타 연령대 (10대, 40대 이상)'],
        '총 매출액': [total_sales_20s, total_sales_30s, total_sales_others]
    })
    
    # 2. 주중 vs 주말 매출 분석
    total_weekday_sales = df['주중_매출_금액'].sum()
    total_weekend_sales = df['주말_매출_금액'].sum()

    day_sales_data = pd.DataFrame({
        '구분': ['주중 매출', '주말 매출'],
        '총 매출액': [total_weekday_sales, total_weekend_sales]
    })

    # 3. Top 5 서비스 업종 분석
    sector_sales = df.groupby('서비스_업종_코드_명')['당월_매출_금액'].sum().reset_index()
    top_sectors = sector_sales.sort_values(by='당월_매출_금액', ascending=False).head(5)
    top_sectors.columns = ['서비스 업종', '총 매출액']
    
    return age_sales_data, day_sales_data, top_sectors

# --- 차트 생성 함수 ---

def create_age_chart(df_age):
    """20·30세대 vs 기타 연령대 매출 기여도 차트 (가로 막대)"""
    fig = px.bar(
        df_age, 
        x='총 매출액', 
        y='연령대', 
        orientation='h',
        title='📈 20·30세대 vs 기타 연령대 매출 기여도',
        color='연령대',
        color_discrete_map={
            '20대': '#3b82f6',  # Blue
            '30대': '#10b981',  # Green
            '기타 연령대 (10대, 40대 이상)': '#f59e0b' # Yellow
        }
    )
    fig.update_layout(
        xaxis_title="총 매출액 (원)", 
        yaxis_title=None,
        # 큰 숫자에 콤마 추가
        xaxis=dict(tickformat=',.0f'),
    )
    return fig

def create_day_chart(df_day):
    """주중 vs 주말 소비 집중도 차트 (도넛 차트)"""
    fig = go.Figure(data=[go.Pie(
        labels=df_day['구분'], 
        values=df_day['총 매출액'], 
        hole=.3, # 도넛 모양을 만들기 위해 hole 설정
        marker_colors=['#6366f1', '#ef4444'] # Indigo, Red
    )])
    
    fig.update_layout(
        title_text='🗓️ 주중 vs 주말 소비 집중도 (도넛 차트)',
        annotations=[dict(text='총 매출', x=0.5, y=0.5, font_size=15, showarrow=False)]
    )
    
    # 툴팁에 콤마 추가
    fig.update_traces(hovertemplate='%{label}: %{value:,}원<br>점유율: %{percent}<extra></extra>')

    return fig

def create_top_sector_chart(df_sector):
    """매출액 기준 Top 5 서비스 업종 차트 (세로 막대)"""
    fig = px.bar(
        df_sector, 
        x='서비스 업종', 
        y='총 매출액', 
        title='🥇 매출액 기준 Top 5 서비스 업종',
        color='서비스 업종',
        color_discrete_sequence=['#0ea5e9'] * len(df_sector) # Sky Blue 계열
    )
    fig.update_layout(
        yaxis_title="총 매출액 (원)", 
        xaxis_title=None,
        # 큰 숫자에 콤마 추가
        yaxis=dict(tickformat=',.0f'),
    )
    return fig


# --- Streamlit 앱 메인 함수 ---

def main():
    st.set_page_config(
        page_title="서울 상권 데이터 대시보드",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.title("🏙️ 서울 상권 데이터 분석 대시보드")
    st.markdown("##### 유망 업종 예측의 근거가 된 핵심 소비 트렌드 시각화")

    # 데이터 로드 및 분석
    data = load_and_analyze_data()
    
    if data is None:
        # 데이터 로드 실패 시 에러 메시지는 load_and_analyze_data 함수에서 처리됨
        return

    df_age, df_day, df_sector = data

    # 1. 연령대별 차트
    st.subheader("1. 📈 연령대별 매출 기여도")
    st.plotly_chart(create_age_chart(df_age), use_container_width=True)
    st.info("💡 **분석 인사이트:** 20대와 30대가 서울 상권 매출의 주요 소비층임을 보여줍니다.")

    # 2. 주중/주말 차트
    st.subheader("2. 🗓️ 주중 vs 주말 소비 집중도")
    st.plotly_chart(create_day_chart(df_day), use_container_width=True)
    st.info("💡 **분석 인사이트:** 주중과 주말 매출 비중을 통해 주말 여가/경험 관련 업종의 중요성을 파악할 수 있습니다.")

    # 3. Top 5 업종 차트
    st.subheader("3. 🥇 매출액 기준 Top 5 서비스 업종")
    st.plotly_chart(create_top_sector_chart(df_sector), use_container_width=True)
    st.info("💡 **분석 인사이트:** 서울시 전체 상권에서 매출 규모가 가장 큰 업종을 확인하고, 해당 업종이 유망 업종 분석의 근거가 되었는지 비교해 볼 수 있습니다.")

if __name__ == "__main__":
    main()

