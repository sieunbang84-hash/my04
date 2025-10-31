import streamlit as st
import pandas as pd
import plotly.express as px

# 사용할 CSV 파일명 (사용자 파일과 동일)
CSV_FILENAME = "서울시 상권분석서비스(추정매출-자치구).csv"
# 지역 필터링에 사용할 컬럼 이름
REGION_COL = '자치구_코드_명'

st.set_page_config(page_title="서울시 상권 분석 대시보드", layout="wide")

# 1. 제목 변경 및 설명
st.title("📊 서울시 상권 분석 대시보드 — Plotly 시각화")
st.markdown("업로드된 CSV 파일을 분석/시각화합니다. 좌측 사이드바에서 파일 업로드, **지역 선택**, 컬럼 선택 등을 조정하세요.")

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    """다중 인코딩 시도를 통해 한국어 CSV 파일을 안전하게 로드합니다."""
    df = None
    # 인코딩 순차 시도: utf-8 -> euc-kr -> cp949
    for encoding_type in ['utf-8', 'euc-kr', 'cp949']:
        try:
            df = pd.read_csv(path, encoding=encoding_type)
            return df
        except Exception:
            continue
    raise Exception("Failed to load CSV with multiple encoding attempts.")


# --- 데이터 로드 ---
st.sidebar.header("데이터 입력")
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드 (없으면 기본 파일 사용)", type=["csv"]) 

if uploaded_file is None:
    try:
        df = load_csv(CSV_FILENAME)
        st.sidebar.write("기본 내장 CSV가 로드되었습니다.")
    except Exception as e:
        st.sidebar.error("기본 CSV를 불러올 수 없습니다. 파일을 업로드하거나 파일명을 확인해주세요.")
        st.stop()
else:
    try:
        # Streamlit이 업로드 파일의 인코딩을 처리하도록 맡김
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("업로드 완료: 파일을 읽었습니다.")
    except Exception as e:
        st.sidebar.error(f"파일을 읽는 중 오류: {e}")
        st.stop()

# 데이터 전처리: 컬럼 이름 앞뒤 공백 제거
orig_columns = list(df.columns)
df.columns = [c.strip() for c in orig_columns]

# --- 지역별 필터링 기능 추가 (요청 사항) ---
df_filtered = df.copy()

st.sidebar.header("🗺️ 지역별 필터")

if REGION_COL in df.columns:
    # 모든 고유 지역명 추출
    all_regions = df[REGION_COL].unique().tolist()
    
    # 지역별 선택 기능 (멀티셀렉트)
    selected_regions = st.sidebar.multiselect(
        "시각화할 자치구 선택 (서울시만)",
        options=all_regions,
        default=all_regions # 기본값: 모든 자치구 선택 (즉, 서울시 전체)
    )
    
    if selected_regions:
        # 필터링 적용
        df_filtered = df[df[REGION_COL].isin(selected_regions)].copy()
        
        if df_filtered.empty:
            st.warning("선택하신 지역에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
            st.stop()
    else:
        st.warning("선택된 자치구가 없어 전체 데이터를 사용합니다.")
        df_filtered = df.copy()
else:
    st.sidebar.warning(f"데이터에 '{REGION_COL}' 컬럼이 없어 지역 필터링을 할 수 없습니다.")
    df_filtered = df.copy() # 필터링 없이 진행

# 데이터 확인 (필터링된 데이터)
st.subheader("데이터 미리보기")
with st.expander(f"필터링된 데이터 (총 {len(df_filtered)} 행)", expanded=False):
    st.dataframe(df_filtered.head(10))
    st.write("사용된 데이터 컬럼 목록:", df_filtered.columns.tolist())

# --- 시각화 옵션 ---
st.sidebar.header("시각화 설정")

if len(df_filtered.columns) >= 2 and not df_filtered.empty:
    
    # X/Y 컬럼 옵션은 필터링 이전의 전체 컬럼 목록을 사용합니다.
    x_col = st.sidebar.selectbox("X축 컬럼 선택", options=df.columns) 
    y_col = st.sidebar.selectbox("Y축 컬럼 선택", options=df.columns)

    chart_type = st.sidebar.radio("그래프 종류", ["라인 그래프", "막대 그래프", "산점도"])

    st.subheader(f"시각화 결과 (선택 지역: {', '.join(selected_regions) if 'selected_regions' in locals() and selected_regions else '전체'})")

    try:
        # 필터링된 데이터 (df_filtered)를 사용하여 시각화
        if chart_type == "라인 그래프":
            fig = px.line(df_filtered, x=x_col, y=y_col, title=f"{y_col} 변화 추이 ({x_col} 기준)")
        elif chart_type == "막대 그래프":
            fig = px.bar(df_filtered, x=x_col, y=y_col, title=f"{y_col} 막대그래프 ({x_col} 기준)")
        else:
            fig = px.scatter(df_filtered, x=x_col, y=y_col, title=f"{x_col} vs {y_col} 산점도")

        fig.update_layout(title_x=0.5, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"그래프를 그리는 중 오류 발생: {e}")
        st.warning("선택하신 컬럼이 숫자로 시각화 가능하거나, 범주형/시간 컬럼이 올바르게 선택되었는지 확인해주세요.")
else:
    st.warning("시각화할 데이터가 없거나, 컬럼 수가 부족합니다. 파일을 확인하거나 필터를 조정해주세요.")

