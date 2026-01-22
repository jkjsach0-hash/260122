import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="서울 기온 역사 비교기", layout="wide")

# 데이터 로드 함수
@st.cache_data
def load_data(file):
    # 상단 7행의 메타데이터 제외하고 로드
    df = pd.read_csv(file, encoding='cp949', skiprows=7)
    # 컬럼명 정리 (공백 및 탭 제거)
    df.columns = [col.strip() for col in df.columns]
    # 날짜 컬럼 전처리 (탭 제거 및 날짜형 변환)
    df['날짜'] = pd.to_datetime(df['날짜'].str.strip())
    # 월-일 정보 추출
    df['월일'] = df['날짜'].dt.strftime('%m-%d')
    df['연도'] = df['날짜'].dt.year
    return df

st.title("🌡️ 서울 기온 역사 비교기")
st.markdown("특정 날짜의 기온이 역대 같은 날에 비해 얼마나 더웠는지 혹은 추웠는지 비교합니다.")

# 1. 파일 업로드 로직
uploaded_file = st.file_uploader("추가 기온 데이터 파일을 업로드하세요 (CSV)", type=['csv'])

# 파일 선택 (업로드 파일 우선, 없으면 기본 파일 사용)
if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.success("새로운 데이터를 성공적으로 불러왔습니다!")
else:
    # 기본 파일 (사용자가 업로드했던 파일명)
    try:
        df = load_data("ta_20260122174530.csv")
        st.info("기본 탑재된 서울 기온 데이터를 사용 중입니다.")
    except:
        st.error("데이터 파일을 찾을 수 없습니다. CSV 파일을 업로드해주세요.")
        st.stop()

# 2. 날짜 선택 및 비교 로직
st.sidebar.header("🔍 분석 설정")
max_date = df['날짜'].max()
min_date = df['날짜'].min()

target_date = st.sidebar.date_input(
    "비교하고 싶은 날짜를 선택하세요",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

# 선택한 날짜의 데이터 추출
target_day_data = df[df['날짜'] == pd.Timestamp(target_date)]

if not target_day_data.empty:
    selected_temp = target_day_data.iloc[0]['평균기온(℃)']
    target_md = target_date.strftime('%m-%d')
    
    # 역대 같은 날짜(월-일) 데이터 필터링
    historical_same_day = df[df['월일'] == target_md]
    avg_historical_temp = historical_same_day['평균기온(℃)'].mean()
    diff = selected_temp - avg_historical_temp
    
    # 메트릭 표시
    col1, col2, col3 = st.columns(3)
    col1.metric("선택한 날 기온", f"{selected_temp}°C")
    col2.metric("역대 평균 ({})".format(target_md), f"{avg_historical_temp:.1f}°C")
    col3.metric("평균 대비 차이", f"{diff:.1f}°C", delta=diff)

    # 3. Plotly 시각화 (인터랙티브 그래프)
    st.subheader(f"📊 {target_md}의 역대 기온 변화 추이")
    
    fig = px.line(historical_same_day, x='연도', y='평균기온(℃)', 
                  title=f"역대 {target_md}의 평균 기온 기록",
                  markers=True,
                  labels={'평균기온(℃)': '기온(°C)', '연도': '연도'})
    
    # 기준선(역대 평균) 추가
    fig.add_hline(y=avg_historical_temp, line_dash="dash", line_color="red", 
                  annotation_text="역대 평균")
    
    # 선택한 날짜 강조
    fig.add_trace(go.Scatter(x=[target_date.year], y=[selected_temp],
                             mode='markers', marker=dict(color='orange', size=12),
                             name='선택한 날짜'))

    st.plotly_chart(fig, use_container_width=True)

    # 상세 데이터 테이블
    with st.expander("역대 같은 날짜 데이터 상세보기"):
        st.write(historical_same_day[['날짜', '평균기온(℃)', '최저기온(℃)', '최고기온(℃)']].sort_values(by='날짜', ascending=False))
else:
    st.warning("선택한 날짜에 대한 관측 데이터가 없습니다.")
