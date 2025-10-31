"""
Streamlit 앱: 주민등록 인구 및 세대현황(월간) 시각화 (Plotly 버전)

사용법:
1) 이 파일을 GitHub에 올리고, Streamlit에서 실행하세요.
   예: streamlit run streamlit_population_plotly_app.py
2) 기본적으로 업로드된 파일 경로를 사용합니다. (로컬에서 실행 시 경로를 수정할 수 있음)
3) 사이드바에서 업로드하거나 컬럼/기간/지역을 선택하여 그래프를 확인하세요.

작성자: Gemini (필터링 기능 추가)
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# 기본 CSV 경로 (업로드된 파일의 기본 위치)
# 주: 이 경로는 실행 환경에 따라 변경될 수 있습니다.
DEFAULT_CSV_PATH = "/mnt/data/202509_202509_주민등록인구및세대현황_월간.csv"

st.set_page_config(page_title="주민등록 인구/세대 현황 시각화", layout="wide")

st.title("📊 주민등록 인구 및 세대현황(월간) — Plotly 시각화 대시보드")
st.markdown("업로드된 CSV 파일을 분석/시각화합니다. 좌측 사이드바에서 파일 업로드, 컬럼 선택 등을 조정하세요.")

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    # 한국어 인코딩 문제를 고려하여 utf-8로 로드 시도
    try:
        return pd.read_csv(path, encoding="utf-8")
    except Exception:
        # utf-8 실패 시, euc-kr 또는 cp949 시도 (한국어 CSV에서 흔한 인코딩)
        return pd.read_csv(path, encoding="euc-kr")


# 사이드바: 파일 선택
st.sidebar.header("데이터 입력")
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드 (없으면 기본 파일 사용)", type=["csv"]) 

if uploaded_file is None:
    try:
        # 인코딩 문제 해결을 위해 load_csv 함수 사용
        df = load_csv(DEFAULT_CSV_PATH)
        st.sidebar.write("기본 내장 CSV가 로드되었습니다.")
    except Exception as e:
        st.sidebar.error("기본 CSV를 불러올 수 없습니다. 파일을 업로드해주세요.")
        st.stop()
else:
    try:
        # 업로드된 파일은 스트림릿이 알아서 인코딩을 처리할 수 있도록, 명시적 인코딩 제거 후 시도
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("업로드 완료: 파일을 읽었습니다.")
    except Exception as e:
        st.sidebar.error(f"파일을 읽는 중 오류: {e}")
        st.stop()

# 데이터 전처리
orig_columns = list(df.columns)
# 컬럼 이름 앞뒤 공백 제거
df.columns = [c.strip() for c in orig_columns]

# --- 데이터 필터링 기능 추가 ---
st.sidebar.header("데이터 필터링")
df_filtered = df.copy()

# 문자열(object) 타입의 컬럼만 필터링 대상으로 선택
filter_col_options = [col for col in df.columns if df[col].dtype == 'object' and len(df[col].unique()) < 50] # 고유값이 너무 많은 컬럼은 제외 (성능 이슈 방지)

if filter_col_options:
    # 필터링할 컬럼 선택
    filter_column = st.sidebar.selectbox(
        "필터링할 지역/범주 컬럼 선택", 
        options=[None] + filter_col_options,
        index=0 # 기본값은 'None'
    )
    
    if filter_column:
        unique_values = df[filter_column].unique().tolist()
        
        # 필터링 값 선택 (멀티셀렉트)
        selected_values = st.sidebar.multiselect(
            f"'{filter_column}' 값 선택",
            options=unique_values,
            default=unique_values # 기본적으로 모든 값 선택
        )
        
        # 필터 적용
        if selected_values and len(selected_values) < len(unique_values):
            # 일부 값만 선택했을 경우 필터링
            df_filtered = df[df[filter_column].isin(selected_values)].copy()
        elif not selected_values:
            # 아무것도 선택하지 않았을 경우 경고
            st.warning("선택된 필터 값이 없습니다. 전체 데이터를 사용합니다.")
            df_filtered = df.copy()
        else:
            # 전체를 선택했거나 필터 컬럼이 없으면 전체 데이터 사용
            df_filtered = df.copy()
else:
    st.sidebar.info("필터링 가능한 문자열 컬럼이 없거나 고유값 개수가 너무 많습니다.")
    df_filtered = df.copy()

# 데이터 확인 (필터링된 데이터)
st.subheader("데이터 미리보기")
with st.expander("원본 데이터(상위 10행) / 컬럼 목록 보기", expanded=False):
    st.dataframe(df_filtered.head(10))
    st.write("사용된 데이터 행 수:", len(df_filtered))
    st.write("컬럼 목록:", df_filtered.columns.tolist())

# 시각화 옵션
st.sidebar.header("시각화 설정")

if len(df_filtered.columns) >= 2:
    # 선택 옵션은 필터링 이전의 전체 컬럼 목록을 사용합니다.
    x_col = st.sidebar.selectbox("X축 컬럼 선택", options=df.columns)
    y_col = st.sidebar.selectbox("Y축 컬럼 선택", options=df.columns)

    chart_type = st.sidebar.radio("그래프 종류", ["라인 그래프", "막대 그래프", "산점도"])

    st.subheader("시각화 결과")

    try:
        if chart_type == "라인 그래프":
            # 필터링된 데이터 사용
            fig = px.line(df_filtered, x=x_col, y=y_col, title=f"{y_col} 변화 추이 ({x_col} 기준)")
        elif chart_type == "막대 그래프":
            # 필터링된 데이터 사용
            fig = px.bar(df_filtered, x=x_col, y=y_col, title=f"{y_col} 막대그래프 ({x_col} 기준)")
        else:
            # 필터링된 데이터 사용
            fig = px.scatter(df_filtered, x=x_col, y=y_col, title=f"{x_col} vs {y_col} 산점도")

        fig.update_layout(title_x=0.5, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"그래프를 그리는 중 오류 발생: {e}")
        st.warning("선택하신 컬럼이 숫자로 시각화 가능한지 확인해주세요.")
else:
    st.warning("CSV 파일에 2개 이상의 열이 있어야 시각화를 진행할 수 있습니다.")
