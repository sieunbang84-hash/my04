"""
Streamlit 앱: 주민등록 인구 및 세대현황(월간) 시각화 (Plotly 버전)

사용법:
1) 이 파일을 GitHub에 올리고, Streamlit에서 실행하세요.
   예: streamlit run streamlit_population_plotly_app.py
2) 기본적으로 업로드된 파일 경로를 사용합니다. (로컬에서 실행 시 경로를 수정할 수 있음)
3) 사이드바에서 업로드하거나 컬럼/기간/지역을 선택하여 그래프를 확인하세요.

작성자: ChatGPT
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# 기본 CSV 경로 (업로드된 파일의 기본 위치)
DEFAULT_CSV_PATH = "/mnt/data/202509_202509_주민등록인구및세대현황_월간.csv"

st.set_page_config(page_title="주민등록 인구/세대 현황 시각화", layout="wide")

st.title("📊 주민등록 인구 및 세대현황(월간) — Plotly 시각화 대시보드")
st.markdown("업로드된 CSV 파일을 분석/시각화합니다. 좌측 사이드바에서 파일 업로드, 컬럼 선택 등을 조정하세요.")

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8")

# 사이드바: 파일 선택
st.sidebar.header("데이터 입력")
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드 (없으면 기본 파일 사용)", type=["csv"]) 

if uploaded_file is None:
    try:
        df = load_csv(DEFAULT_CSV_PATH)
        st.sidebar.write("기본 내장 CSV가 로드되었습니다.")
    except Exception as e:
        st.sidebar.error("기본 CSV를 불러올 수 없습니다. 파일을 업로드해주세요.")
        st.stop()
else:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
        st.sidebar.success("업로드 완료: 파일을 읽었습니다.")
    except Exception as e:
        st.sidebar.error(f"파일을 읽는 중 오류: {e}")
        st.stop()

# 데이터 전처리
orig_columns = list(df.columns)
df.columns = [c.strip() for c in orig_columns]

# 데이터 확인
st.subheader("데이터 미리보기")
with st.expander("원본 데이터(상위 10행) / 컬럼 목록 보기", expanded=False):
    st.dataframe(df.head(10))
    st.write("컬럼 목록:", df.columns.tolist())

# 시각화 옵션
st.sidebar.header("시각화 설정")

if len(df.columns) >= 2:
    x_col = st.sidebar.selectbox("X축 컬럼 선택", options=df.columns)
    y_col = st.sidebar.selectbox("Y축 컬럼 선택", options=df.columns)

    chart_type = st.sidebar.radio("그래프 종류", ["라인 그래프", "막대 그래프", "산점도"])

    st.subheader("시각화 결과")

    try:
        if chart_type == "라인 그래프":
            fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} 변화 추이 ({x_col} 기준)")
        elif chart_type == "막대 그래프":
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} 막대그래프 ({x_col} 기준)")
        else:
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col} 산점도")

        fig.update_layout(title_x=0.5, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"그래프를 그리는 중 오류 발생: {e}")
else:
    st.warning("CSV 파일에 2개 이상의 열이 있어야 시각화를 진행할 수 있습니다.")
