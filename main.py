import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 페이지 설정
st.set_page_config(page_title="서울 기온 역사 비교기", layout="wide")

@st.cache_data
def load_data(file_path_or_buffer):
    try:
        # 1. 인코딩 시도 (CP949 -> UTF-8)
        try:
            df = pd.read_csv(file_path_or_buffer, encoding='cp949', skiprows=7)
        except:
            df = pd.read_csv(file_path_or_buffer, encoding='utf-8', skiprows=7)
            
        # 2. 컬럼명 정제
        df.columns = [col.strip() for col in df.columns]
        
        # 3. 데이터 정제 (탭 문자 제거 및 날짜 변환)
        # 문자열로 들어오는 경우를 대비해 strip() 적용
        df['날짜'] = df['날짜'].astype(str).str.strip()
        df['날짜'] = pd.to_datetime(df['날짜'])
        
        # 4. 분석용 파생 변수 생성
        df['월일'] = df['날짜'].dt.strftime('%m-%d')
        df['연도'] = df['날짜'].dt.year
        
        # 5. 수치 데이터 형변환 (결측치 처리 포함)
        for col in ['평균기온(℃)', '최저기온(℃)', '최고기온(℃)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"데이터를 읽는 중 오류가 발생했습니다: {e}")
        return None

st.title("🌡️ 서울 기온 역사 비교기")
st.markdown("특정 날짜의 기온이 과거와 비교해 얼마나 변화했는지 확인하세요.")

# 파일 처리 로직
DEFAULT_FILE = "ta_20260122174530.csv"
uploaded_file = st.file_uploader("새로운 CSV 파일을 업로드하여 데이터를 업데이트하세요", type=['csv'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.success("새 데이터를 불러왔습니다.")
elif os.path.exists(DEFAULT_FILE):
    df = load_data(DEFAULT_FILE)
    st.info("기본 데이터를 사용 중입니다.")
else:
    st.warning("데이터 파일이 없습니다. CSV 파일을 업로드해주세요.")
    df = None

if df is not None:
    # 사이드바 설정
    st.sidebar.header("🔍 날짜 선택")
    latest_date = df['날짜'].max()
    target_date = st.sidebar.date_input("비교할 날짜", 
                                       value=latest_date,
                                       min_value=df['날짜'].min(),
                                       max_value=latest_date)

    # 같은 월-일 데이터 필터링
    target_md = target_date.strftime('%m-%d')
    historical_data = df[df['월일'] == target_md].dropna(subset=['평균기온(℃)'])
    
    # 선택 날짜 데이터
    current_data = historical_data[historical_data['연도'] == target_date.year]
    
    if not current_data.empty:
        curr_temp = current_data.iloc[0]['평균기온(℃)']
        hist_avg = historical_data['평균기온(℃)'].mean()
        diff = curr_temp - hist_avg
        
        # 상단 지표
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{target_date.year}년 기온", f"{curr_temp}°C")
        c2.metric(f"역대 {target_md} 평균", f"{hist_avg:.1f}°C")
        c3.metric("평균 대비", f"{diff:.1f}°C", delta=round(diff, 1))

        # 시각화
        st.subheader(f"📊 역대 {target_md} 기온 변화 (Plotly 인터랙티브)")
        
        fig = px.scatter(historical_data, x='연도', y='평균기온(℃)',
                         trendline="lowess", # 추세선 추가
                         title=f"서울 {target_md} 평균 기온 추이",
                         labels={'평균기온(℃)': '기온(°C)'},
                         template="plotly_white")
        
        # 선택한 날짜 강조 표시
        fig.add_trace(go.Scatter(x=[target_date.year], y=[curr_temp],
                                 mode='markers+text',
                                 marker=dict(color='red', size=15, symbol='star'),
                                 name='선택한 날짜',
                                 text=[f"{target_date.year}년"],
                                 textposition="top center"))

        st.plotly_chart(fig, use_container_width=True)
