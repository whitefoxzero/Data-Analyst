import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Olympic Analytics Dashboard",
    page_icon="🏅",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. State Management (ระบบจัดการหน้า สลับหน้าไปมา)
# -----------------------------------------------------------------------------
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'selected_athlete' not in st.session_state:
    st.session_state.selected_athlete = None

def go_to_athlete(athlete_name):
    st.session_state.selected_athlete = athlete_name
    st.session_state.current_page = 'athlete_profile'

def go_to_dashboard():
    st.session_state.selected_athlete = None
    st.session_state.current_page = 'dashboard'

# -----------------------------------------------------------------------------
# 3. UI/UX & Custom CSS
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    html, body, [class*="css"]  { color: #000000 !important; }
    .stApp { background-color: #FDFBF7; color: #000000 !important; }
    h1, h2, h3, h4, h5, h6 { color: #000000 !important; }
    .stMarkdown, .stText, p, span, label { color: #000000 !important; }
    
    div[data-testid="stMetric"] {
        background-color: #F5EFE6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.05);
        border: 1px solid #E6DCCD;
    }
    div[data-testid="stMetricLabel"], div[data-testid="stMetricValue"] {
        color: #000000 !important;
    }
    section[data-testid="stSidebar"] * { color: #000000 !important; }
    .stPlotlyChart * { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. Data Loading & Cleaning
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_clean_data():
    try:
        df = pd.read_csv("dataset2.csv")
        
        if 'notes' in df.columns: df = df.drop(columns=['notes'])
        if 'Name' in df.columns:
            df = df[df['Name'].str.match(r'^[^\W\d_]+(?:[ \.\-][^\W\d_]+)*$', na=False)]

        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        cat_cols = ['Sex', 'Season', 'Team', 'NOC', 'Sport', 'Event', 'City']
        existing_cat_cols = [col for col in cat_cols if col in df.columns]
        df[existing_cat_cols] = df[existing_cat_cols].astype('category')

        # จัดการ Medal ให้เป็นตัวพิมพ์เล็กทั้งหมด
        df['Medal'] = df['Medal'].astype(str).str.strip().str.lower()
        df['Medal'] = df['Medal'].replace({'no medal': np.nan, '-': np.nan , 'nan': np.nan})
        df['Medal'] = df['Medal'].fillna('no medal')
        df['Medal'] = df['Medal'].astype('category')

        if 'region' in df.columns: df['region'] = df['region'].fillna('Unknown')

        df.loc[(df['Age'] > 75) | (df['Age'] < 10), 'Age'] = np.nan 
        if 'Height' in df.columns: df.loc[(df['Height'] > 250) | (df['Height'] < 120), 'Height'] = np.nan
        if 'Weight' in df.columns: df.loc[(df['Weight'] > 200) | (df['Weight'] < 25), 'Weight'] = np.nan

        cols_to_impute = [col for col in ['Age', 'Height', 'Weight'] if col in df.columns]
        for col in cols_to_impute:
            df[col] = df.groupby(['Sex', 'Sport'])[col].transform(lambda x: x.fillna(x.median()))
            df[col] = df.groupby('Sex')[col].transform(lambda x: x.fillna(x.median()))
            df[col] = df[col].fillna(df[col].median())

        df.drop_duplicates(inplace=True)
        return df

    except FileNotFoundError:
        st.error("Error: 'dataset2.csv' not found.")
        return pd.DataFrame()

df = load_and_clean_data()
if df.empty: st.stop()

# Color mapping (อิงตามตัวพิมพ์เล็กที่ Clean มา)
color_map = {
    'gold': '#FFD700', 'silver': '#C0C0C0', 
    'bronze': '#CD7F32', 'no medal': '#E0E0E0'
}

# =============================================================================
# 5. ROUTING LOGIC (แยกว่าตอนนี้อยู่หน้าไหน)
# =============================================================================

if st.session_state.current_page == 'dashboard':
    # -------------------------------------------------------------------------
    # PAGE 1: MAIN DASHBOARD
    # -------------------------------------------------------------------------
    st.sidebar.header("🎯 Global Filters")
    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.sidebar.slider("Select Year Range:", min_year, max_year, (min_year, max_year))
    
    all_sports = sorted(df['Sport'].dropna().unique())
    selected_sports = st.sidebar.multiselect("Select Sport(s):", all_sports, default=all_sports[:5])
    if not selected_sports: selected_sports = all_sports
    
    medal_options = ['gold', 'silver', 'bronze', 'no medal']
    selected_medals = st.sidebar.multiselect("Select Medal Type(s):", medal_options, default=medal_options)

    df_filtered = df[
        (df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1]) &
        (df['Sport'].isin(selected_sports)) & (df['Medal'].isin(selected_medals))
    ]

    st.title("🏅 Olympic Analytics Dashboard")
    
    # --- ช่องค้นหานักกีฬา ---
    st.markdown("### 🔎 ค้นหาโปรไฟล์นักกีฬาเจาะลึก")
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        search_list = df['Name'].dropna().unique()
        selected_search = st.selectbox("พิมพ์หรือเลือกชื่อนักกีฬา:", options=["-- กรุณาเลือกนักกีฬา --"] + list(search_list))
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True) 
        if st.button("ดูโปรไฟล์แบบเต็ม 🚀", use_container_width=True):
            if selected_search != "-- กรุณาเลือกนักกีฬา --":
                go_to_athlete(selected_search)
                st.rerun()
            else:
                st.warning("โปรดเลือกชื่อนักกีฬาก่อน")

    st.markdown("---")
    
    # --- ภาพรวม ---
    st.subheader("📊 Global Medal Overview")
    t_gold = len(df_filtered[df_filtered['Medal'] == 'gold'])
    t_silver = len(df_filtered[df_filtered['Medal'] == 'silver'])
    t_bronze = len(df_filtered[df_filtered['Medal'] == 'bronze'])
    t_none = len(df_filtered[df_filtered['Medal'] == 'no medal'])
    t_athletes = df_filtered['Name'].nunique()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🥇 Total Gold", f"{t_gold:,}")
    m2.metric("🥈 Total Silver", f"{t_silver:,}")
    m3.metric("🥉 Total Bronze", f"{t_bronze:,}")
    m4.metric("🏃‍♂️ Participations", f"{t_none:,}")
    m5.metric("👥 Unique Athletes", f"{t_athletes:,}")

    c1, c2 = st.columns(2)
    with c1:
        count_by_year = df_filtered.groupby(['Year', 'Medal']).size().reset_index(name='Count')
        fig_year = px.bar(count_by_year, x='Year', y='Count', color='Medal', color_discrete_map=color_map, title="Medals per Year", barmode='group')
        fig_year.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_year, width="stretch")

    with c2:
        sport_counts = df_filtered.groupby(['Sport', 'Medal']).size().reset_index(name='Count')
        sport_total = sport_counts.groupby('Sport')['Count'].sum().reset_index().sort_values('Count', ascending=False)
        top_sports = sport_total.head(10)['Sport'].tolist()
        fig_sport = px.bar(sport_counts[sport_counts['Sport'].isin(top_sports)], x='Sport', y='Count', color='Medal', color_discrete_map=color_map, title="Top 10 Sports by Activity", category_orders={"Sport": top_sports})
        fig_sport.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_sport, width="stretch")

    st.divider()

    # --- LEADERBOARD ---
    st.subheader("🏆 Top 20 Athletes (Leaderboard)")
    medals_only = df[df['Medal'].isin(['gold', 'silver', 'bronze'])]
    leaderboard = medals_only.groupby('Name')['Medal'].count().reset_index(name='Total Medals').sort_values('Total Medals', ascending=False).head(20)

    col_rank1, col_rank2 = st.columns(2)
    with col_rank1:
        fig_rank = px.bar(leaderboard, x='Total Medals', y='Name', orientation='h', title="All-Time Medal Leaders", color='Total Medals', color_continuous_scale='Viridis')
        fig_rank.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_rank, width="stretch")

    with col_rank2:
        st.markdown("#### Leaderboard Data (คลิกที่ตารางเพื่อดูโปรไฟล์ 👇)")
        top_names = leaderboard['Name'].tolist()
        detailed_leaderboard = pd.crosstab(medals_only[medals_only['Name'].isin(top_names)]['Name'], medals_only['Medal'])
        
        # ป้องกันตารางพังถ้ากีฬาบางประเภทไม่มีคนได้เหรียญบางสี
        for m in ['gold', 'silver', 'bronze']:
            if m not in detailed_leaderboard: detailed_leaderboard[m] = 0
            
        detailed_leaderboard = detailed_leaderboard[['gold', 'silver', 'bronze']] 
        detailed_leaderboard['Total'] = detailed_leaderboard.sum(axis=1)
        detailed_leaderboard = detailed_leaderboard.sort_values('Total', ascending=False)
        detailed_leaderboard.columns = ['🥇 Gold', '🥈 Silver', '🥉 Bronze', '🏆 Total'] 

        # ตารางแบบ Interactive กดเลือกได้
        event = st.dataframe(
            detailed_leaderboard, 
            width="stretch",
            on_select="rerun",              
            selection_mode="single-row"     
        )

        if len(event.selection.rows) > 0:
            selected_row_index = event.selection.rows[0]
            clicked_athlete = detailed_leaderboard.index[selected_row_index]
            go_to_athlete(clicked_athlete)
            st.rerun()

elif st.session_state.current_page == 'athlete_profile':
    # -------------------------------------------------------------------------
    # PAGE 2: ATHLETE PROFILE PAGE
    # -------------------------------------------------------------------------
    if st.button("🔙 กลับไปหน้า Dashboard หลัก"):
        go_to_dashboard()
        st.rerun()

    athlete_name = st.session_state.selected_athlete
    ath_df = df[df['Name'] == athlete_name]
    latest_ath = ath_df.sort_values('Year', ascending=False).iloc[0]

    st.markdown(f"## 👤 Athlete Profile: **{athlete_name}**")
    st.markdown("---")

    # --- ข้อมูลกายภาพและสังกัด ---
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("Sex", latest_ath['Sex'])
    p2.metric("Latest Age", f"{int(latest_ath['Age'])}" if pd.notna(latest_ath['Age']) else "N/A")
    p3.metric("Height", f"{int(latest_ath['Height'])} cm" if pd.notna(latest_ath['Height']) else "N/A")
    p4.metric("Weight", f"{int(latest_ath['Weight'])} kg" if pd.notna(latest_ath['Weight']) else "N/A")
    p5.metric("Team", latest_ath['Team'])
    p6.metric("Region", latest_ath['region'] if 'region' in df.columns and pd.notna(latest_ath['region']) else "N/A")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- สรุปเหรียญทั้งหมดของนักกีฬาคนนี้ ---
    st.markdown("### 🏆 Career Summary")
    ath_gold = len(ath_df[ath_df['Medal'] == 'gold'])
    ath_silver = len(ath_df[ath_df['Medal'] == 'silver'])
    ath_bronze = len(ath_df[ath_df['Medal'] == 'bronze'])
    total_medals = ath_gold + ath_silver + ath_bronze
    unique_years = ath_df['Year'].nunique()

    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("🥇 Total Gold", ath_gold)
    a2.metric("🥈 Total Silver", ath_silver)
    a3.metric("🥉 Total Bronze", ath_bronze)
    a4.metric("🏅 Total Medals", total_medals)
    a5.metric("📅 Olympic Games Attended", unique_years)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- กราฟและประวัติ ---
    r1, r2 = st.columns([3, 2])
    with r1:
        st.markdown("#### 📈 Medal History Timeline")
        ath_hist = ath_df.groupby(['Year', 'Medal']).size().reset_index(name='Count')
        
        # จัดการกราฟไทม์ไลน์
        if unique_years == 1:
            fig_ath = px.scatter(ath_hist[ath_hist['Medal'] != 'no medal'], x='Year', y='Count', color='Medal', size='Count', color_discrete_map=color_map, title="Medals Won (Single Year)")
        else:
            fig_ath = px.line(ath_hist[ath_hist['Medal'] != 'no medal'], x='Year', y='Count', color='Medal', markers=True, color_discrete_map=color_map, title="Medals Won Over Years")
        
        fig_ath.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(dtick=4))
        st.plotly_chart(fig_ath, width="stretch")

    with r2:
        st.markdown("#### 📝 Detailed Event Log")
        hist_table = ath_df[['Year', 'Season', 'City', 'Sport', 'Event', 'Medal']].sort_values('Year', ascending=False)
        st.dataframe(hist_table, hide_index=True, width="stretch", height=350)

# Footer ทั่วไป
st.markdown("---")
st.markdown("© 2026 Olympic Analytics Dashboard | Built with Streamlit")