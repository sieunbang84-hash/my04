import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# -----------------------------------------------------------
# 파일명 정의 (사용자가 업로드한 파일 기준)
# -----------------------------------------------------------
FILE_NAME = "서울시 상권분석서비스(추정매출-자치구).csv"

st.set_page_config(page_title="서울 상권 매출 동적 시각화 대시보드", layout="wide")

st.title("📊 서울 상권 매출 데이터 동적 시각화")
st.markdown("업로드된 '서울시 상권분석서비스' 데이터를 기반으로 지역/업종을 필터링하여 원하는 지표를 Plotly로 시각화합니다.")

# -----------------------------------------------------------
# 1. 데이터 로드 및 전처리 함수
# -----------------------------------------------------------
@st.cache_data
def load_and_preprocess_data(file_name: str) -> pd.DataFrame:
    """CSV 파일을 읽고 컬럼 이름을 한국어로 정리합니다."""
    try:
        df = pd.read_csv(file_name, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_name, encoding='cp949')
        except Exception as e:
            st.error(f"파일 인코딩 오류: {e}")
            return pd.DataFrame() # 빈 DataFrame 반환

    # 컬럼 이름을 사용자 친화적인 한국어로 변경
    rename_mapping = {
        '기준_년분기_코드': '기준_분기',
        '자치구_코드_명': '자치구명',
        '서비스_업종_코드_명': '업종명',
        '당월_매출_금액': '총_매출액',
        '당월_매출_건수': '총_매출건수',
        # 요일별 매출
        '주중_매출_금액': '주중_매출', '주말_매출_금액': '주말_매출',
        '월요일_매출_금액': '월요일_매출', '화요일_매출_금액': '화요일_매출', '수요일_매출_금액': '수요일_매출',
        '목요일_매출_금액': '목요일_매출', '금요일_매출_금액': '금요일_매출', '토요일_매출_금액': '토요일_매출', '일요일_매출_금액': '일요일_매출',
        # 시간대별 매출
        '시간대_00~06_매출_금액': '새벽_00~06시_매출', '시간대_06~11_매출_금액': '오전_06~11시_매출',
        '시간대_11~14_매출_금액': '점심_11~14시_매출', '시간대_14~17_매출_금액': '오후_14~17시_매출',
        '시간대_17~21_매출_금액': '저녁_17~21시_매출', '시간대_21~24_매출_금액': '심야_21~24시_매출',
        # 성별 매출
        '남성_매출_금액': '남성_매출', '여성_매출_금액': '여성_매출',
        # 연령대별 매출
        '연령대_10_매출_금액': '10대_매출', '연령대_20_매출_금액': '20대_매출', '연령대_30_매출_금액': '30대_매출',
        '연령대_40_매출_금액': '40대_매출', '연령대_50_매출_금액': '50대_매출', '연령대_60_이상_매출_금액': '60대_이상_매출',
        # 참고: 건수 컬럼은 분석 편의를 위해 일단 제외함. 필요시 추가 가능.
    }
    df = df.rename(columns=rename_mapping)
    
    # 숫자형 컬럼에 대해 쉼표 제거 및 숫자 변환
    numeric_cols = [col for col in df.columns if '매출' in col or '건수' in col or '총' in col]
    for col in numeric_cols:
        # 오류 발생을 대비해 try-except로 감싸고, 실패 시 해당 컬럼은 무시
        try:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        except:
            continue
            
    # NaN 값 0으로 채우기 (매출 데이터이므로)
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    return df

# 데이터 로드
try:
    df_raw = load_and_preprocess_data(FILE_NAME)
    if df_raw.empty:
        st.stop()
except FileNotFoundError:
    st.error(f"❌ 오류: 파일을 찾을 수 없습니다. '{FILE_NAME}' 경로에 파일이 있는지 확인해 주세요.")
    st.stop()
except Exception as e:
    st.error(f"❌ 데이터 로드 및 전처리 중 예상치 못한 오류 발생: {e}")
    st.stop()


# -----------------------------------------------------------
# 2. 데이터 필터링 (사이드바)
# -----------------------------------------------------------

st.sidebar.header("📍 데이터 필터링")

# 자치구 선택
unique_districts = ['전체'] + sorted(df_raw['자치구명'].unique().tolist())
selected_district = st.sidebar.selectbox("자치구 선택:", unique_districts, index=0)

# 업종 선택
# 자치구 선택에 따라 업종 목록이 달라질 수 있음
if selected_district != '전체':
    df_filtered_district = df_raw[df_raw['자치구명'] == selected_district]
else:
    df_filtered_district = df_raw.copy()

unique_sectors = ['전체'] + sorted(df_filtered_district['업종명'].unique().tolist())
selected_sector = st.sidebar.selectbox("업종 선택:", unique_sectors, index=0)

# 최종 필터링 적용
df_filtered = df_filtered_district.copy()
if selected_sector != '전체':
    df_filtered = df_filtered[df_filtered['업종명'] == selected_sector]

# -----------------------------------------------------------
# 3. 데이터 통합 및 시각화 준비
# -----------------------------------------------------------

# 필터링된 데이터가 없으면 경고 후 종료
if df_filtered.empty:
    st.warning("선택된 필터 조건에 해당하는 데이터가 없습니다. 다른 지역/업종을 선택해 주세요.")
    st.stop()

# 시각화할 컬럼 옵션 정리
# 문자열(카테고리) 및 숫자형 컬럼 분리
categorical_cols = ['기준_분기', '자치구명', '업종명']
numeric_cols = [col for col in df_filtered.columns if df_filtered[col].dtype in (np.number, 'int64', 'float64') and col not in ['자치구_코드']]

# 시각화 옵션
st.sidebar.header("📈 시각화 설정")

# X, Y축 선택 옵션
x_options = categorical_cols + numeric_cols
y_options = numeric_cols

# X, Y축 컬럼 선택 (기본값 설정)
if '기준_분기' in x_options:
    x_default_index = x_options.index('기준_분기')
else:
    x_default_index = 0

if '총_매출액' in y_options:
    y_default_index = y_options.index('총_매출액')
else:
    y_default_index = 0

x_col = st.sidebar.selectbox("X축 컬럼 선택 (카테고리 또는 기간)", options=x_options, index=x_default_index)
y_col = st.sidebar.selectbox("Y축 컬럼 선택 (숫자형 지표)", options=y_options, index=y_default_index)

chart_type = st.sidebar.radio("그래프 종류", ["라인 그래프", "막대 그래프", "산점도"])

# Plotly 차트 생성 시 데이터프레임 집계 (필요한 경우)
if x_col in ['자치구명', '업종명'] and x_col != y_col:
    # X축이 범주형(지역/업종)이고 Y축이 매출액인 경우, X축 기준으로 Y축을 합산하여 그룹화
    df_plot = df_filtered.groupby(x_col, as_index=False)[y_col].sum()
    y_label = f"총 {y_col} (합산)"
    title_suffix = f"({x_col} 기준 합산)"
else:
    df_plot = df_filtered.copy()
    y_label = y_col
    title_suffix = ""

# -----------------------------------------------------------
# 4. 결과 출력
# -----------------------------------------------------------

st.subheader(f"✅ 시각화 결과: {selected_district} - {selected_sector} 데이터")

# 데이터 미리보기
with st.expander("📌 필터링된 데이터 미리보기 (상위 5행)", expanded=False):
    st.dataframe(df_filtered.head())
    
try:
    title = f"{y_col} 변화 추이 ({x_col} 기준) {title_suffix}"
    
    if chart_type == "라인 그래프":
        fig = px.line(df_plot, x=x_col, y=y_col, title=title, 
                      labels={y_col: y_label, x_col: x_col}, 
                      color='업종명' if '업종명' in df_plot.columns else None)
    elif chart_type == "막대 그래프":
        fig = px.bar(df_plot, x=x_col, y=y_col, title=title, 
                      labels={y_col: y_label, x_col: x_col}, 
                      color=x_col if len(df_plot[x_col].unique()) < 20 else None)
    else: # 산점도
        fig = px.scatter(df_plot, x=x_col, y=y_col, title=title,
                          labels={y_col: y_label, x_col: x_col},
                          color='자치구명' if '자치구명' in df_plot.columns else None)

    # 차트 레이아웃 설정
    fig.update_layout(title_x=0.5, template="plotly_white", 
                      font=dict(family="Noto Sans KR, sans-serif"))
    
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"그래프를 그리는 중 오류 발생 (선택된 X/Y축을 확인하세요): {e}")

# -----------------------------------------------------------
# 5. 분석 정보
# -----------------------------------------------------------
st.markdown("---")
st.subheader("💡 분석 정보 요약")
st.info(f"총 {len(df_raw)}개의 원본 데이터에서 {len(df_filtered)}개의 행을 필터링하여 시각화했습니다. \n\n"
        f"- **선택 지역:** {selected_district}\n"
        f"- **선택 업종:** {selected_sector}\n"
        f"- **데이터 기간:** {df_raw['기준_분기'].min()} ~ {df_raw['기준_분기'].max()} 분기"
)
