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
# 2. State Management
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
# 3. UI/UX & Custom CSS (บังคับ Light Mode & ตัวหนังสือสีดำ)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    /* บังคับพื้นหลังหลักและ Sidebar ให้เป็นสีสว่าง (ล้างค่า Dark Mode) */
    .stApp, .stApp > header { background-color: #F4F6F9 !important; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background-color: #FFFFFF !important; }
    
    /* บังคับตัวหนังสือทุกส่วนให้เป็นสีดำ */
    html, body, p, span, h1, h2, h3, h4, h5, h6, li, label, div { 
        color: #000000 !important; 
    }
    
    /* ตกแต่งกล่อง Metric ให้ดูมีมิติ */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05) !important;
        border-left: 5px solid #FFD700 !important;
    }
    
    /* ทำให้ข้อความใน Tabs เห็นชัดเจน */
    button[data-baseweb="tab"] p {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #000000 !important;
    }
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

        df['Medal'] = df['Medal'].astype(str).str.strip().str.lower()
        df['Medal'] = df['Medal'].replace({'no medal': np.nan, '-': np.nan, 'nan': np.nan})
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
        st.error("Error: ไม่พบไฟล์ 'dataset2.csv'")
        return pd.DataFrame()

df = load_and_clean_data()

if df.empty: 
    st.stop()

color_map = {
    'gold': '#FFD700', 'silver': '#C0C0C0', 
    'bronze': '#CD7F32', 'no medal': '#E0E0E0'
}

# =============================================================================
# 5. ROUTING LOGIC
# =============================================================================

if st.session_state.current_page == 'dashboard':
    st.sidebar.header("🎯 ตัวกรองข้อมูล (Filters)")
    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.sidebar.slider("เลือกช่วงปี:", min_year, max_year, (min_year, max_year))
    
    all_sports = sorted(df['Sport'].dropna().unique())
    selected_sports = st.sidebar.multiselect("เลือกประเภทกีฬา:", all_sports, default=all_sports[:5])
    if not selected_sports: selected_sports = all_sports
    
    medal_options = ['gold', 'silver', 'bronze', 'no medal']
    selected_medals = st.sidebar.multiselect("เลือกเหรียญรางวัล:", medal_options, default=medal_options)

    df_filtered = df[
        (df['Year'] >= year_range[0]) & (df['Year'] <= year_range[1]) &
        (df['Sport'].isin(selected_sports)) & (df['Medal'].isin(selected_medals))
    ]

    st.title("🏅 Olympic Analytics Dashboard")
    
    search_list = df['Name'].dropna().unique()
    selected_search = st.selectbox("🔎 พิมพ์หรือเลือกชื่อนักกีฬาเพื่อดูสถิติเจาะลึก:", options=["-- กรุณาเลือกนักกีฬา --"] + list(search_list))
    if selected_search != "-- กรุณาเลือกนักกีฬา --":
        go_to_athlete(selected_search)
        st.rerun()

    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📊 ภาพรวมสถิติ (Overview)", "🏆 ตารางอันดับนักกีฬา (Leaderboard)"])

    with tab1:
        st.subheader("ภาพรวมการแข่งขันทั่วโลก")
        t_gold = len(df_filtered[df_filtered['Medal'] == 'gold'])
        t_silver = len(df_filtered[df_filtered['Medal'] == 'silver'])
        t_bronze = len(df_filtered[df_filtered['Medal'] == 'bronze'])
        t_none = len(df_filtered[df_filtered['Medal'] == 'no medal'])
        t_athletes = df_filtered['Name'].nunique()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🥇 เหรียญทอง", f"{t_gold:,}")
        m2.metric("🥈 เหรียญเงิน", f"{t_silver:,}")
        m3.metric("🥉 เหรียญทองแดง", f"{t_bronze:,}")
        m4.metric("🏃‍♂️ เข้าร่วม (ไม่ได้รับเหรียญ)", f"{t_none:,}")
        m5.metric("👥 จำนวนนักกีฬา", f"{t_athletes:,}")

        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            count_by_year = df_filtered.groupby(['Year', 'Medal']).size().reset_index(name='Count')
            # เพิ่ม template="plotly_white" เพื่อบังคับกราฟเป็นโหมดสว่าง
            fig_year = px.bar(count_by_year, x='Year', y='Count', color='Medal', color_discrete_map=color_map, title="สถิติเหรียญรางวัลแบ่งตามปี", barmode='group', template="plotly_white")
            fig_year.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#000000"))
            st.plotly_chart(fig_year, width="stretch")

        with c2:
            sport_counts = df_filtered.groupby(['Sport', 'Medal']).size().reset_index(name='Count')
            sport_total = sport_counts.groupby('Sport')['Count'].sum().reset_index().sort_values('Count', ascending=False)
            top_sports = sport_total.head(10)['Sport'].tolist()
            # เพิ่ม template="plotly_white"
            fig_sport = px.bar(sport_counts[sport_counts['Sport'].isin(top_sports)], x='Sport', y='Count', color='Medal', color_discrete_map=color_map, title="10 กีฬายอดนิยม", category_orders={"Sport": top_sports}, template="plotly_white")
            fig_sport.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#000000"))
            st.plotly_chart(fig_sport, width="stretch")

    with tab2:
        st.subheader("Top 20 นักกีฬาที่ได้เหรียญมากที่สุด")
        medals_only = df_filtered[df_filtered['Medal'].isin(['gold', 'silver', 'bronze'])]
        
        if medals_only.empty:
            st.warning("⚠️ ไม่พบข้อมูลการได้เหรียญรางวัลในประเภทกีฬาหรือช่วงเวลาที่คุณเลือก กรุณาปรับตัวกรองใหม่ครับ")
        else:
            leaderboard = medals_only.groupby('Name')['Medal'].count().reset_index(name='Total Medals').sort_values('Total Medals', ascending=False).head(20)

            col_rank1, col_rank2 = st.columns([1, 1])
            with col_rank1:
                # เพิ่ม template="plotly_white"
                fig_rank = px.bar(leaderboard, x='Total Medals', y='Name', orientation='h', title="ทำเนียบนักกีฬา (เหรียญรวม)", color='Total Medals', color_continuous_scale='Viridis', template="plotly_white")
                fig_rank.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#000000"))
                st.plotly_chart(fig_rank, width="stretch")

            with col_rank2:
                st.markdown("##### 📊 รายละเอียดเหรียญรางวัล")
                top_names = leaderboard['Name'].tolist()
                detailed_leaderboard = pd.crosstab(medals_only[medals_only['Name'].isin(top_names)]['Name'], medals_only['Medal'])
                
                for m in ['gold', 'silver', 'bronze']:
                    if m not in detailed_leaderboard: detailed_leaderboard[m] = 0
                    
                detailed_leaderboard = detailed_leaderboard[['gold', 'silver', 'bronze']] 
                detailed_leaderboard['Total'] = detailed_leaderboard.sum(axis=1)
                detailed_leaderboard = detailed_leaderboard.sort_values('Total', ascending=False)
                detailed_leaderboard.columns = ['🥇 Gold', '🥈 Silver', '🥉 Bronze', '🏆 Total'] 

                st.dataframe(detailed_leaderboard, use_container_width=True)
                st.info("💡 หากต้องการดูสถิติเจาะลึกของนักกีฬาในตารางนี้ สามารถพิมพ์ชื่อในช่องค้นหาด้านบนได้เลยครับ")

elif st.session_state.current_page == 'athlete_profile':
    col_back, col_space = st.columns([1, 5])
    with col_back:
        if st.button("🔙 กลับไปหน้าหลัก", use_container_width=True):
            go_to_dashboard()
            st.rerun()

    athlete_name = st.session_state.selected_athlete
    ath_df = df[df['Name'] == athlete_name]
    latest_ath = ath_df.sort_values('Year', ascending=False).iloc[0]

    st.markdown(f"## 👤 สถิตินักกีฬา: **{athlete_name}**")
    st.markdown("---")

    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("เพศ", latest_ath['Sex'])
    p2.metric("อายุล่าสุดตอนแข่ง", f"{int(latest_ath['Age'])} ปี" if pd.notna(latest_ath['Age']) else "N/A")
    p3.metric("ส่วนสูง", f"{int(latest_ath['Height'])} cm" if pd.notna(latest_ath['Height']) else "N/A")
    p4.metric("น้ำหนัก", f"{int(latest_ath['Weight'])} kg" if pd.notna(latest_ath['Weight']) else "N/A")
    p5.metric("ทีม/ประเทศ", latest_ath['Team'])
    p6.metric("ภูมิภาค", latest_ath['region'] if 'region' in df.columns and pd.notna(latest_ath['region']) else "N/A")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### 🏆 สรุปผลงานตลอดชีพ (Career Summary)")
    ath_gold = len(ath_df[ath_df['Medal'] == 'gold'])
    ath_silver = len(ath_df[ath_df['Medal'] == 'silver'])
    ath_bronze = len(ath_df[ath_df['Medal'] == 'bronze'])
    total_medals = ath_gold + ath_silver + ath_bronze
    unique_years = ath_df['Year'].nunique()

    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("🥇 เหรียญทอง", ath_gold)
    a2.metric("🥈 เหรียญเงิน", ath_silver)
    a3.metric("🥉 เหรียญทองแดง", ath_bronze)
    a4.metric("🏅 รวมเหรียญที่ได้", total_medals)
    a5.metric("📅 จำนวนปีที่ลงแข่ง", unique_years)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 📈 ไทม์ไลน์: ปีที่แข่งขัน และกีฬาที่ได้เหรียญ")
    
    plot_df = ath_df.copy()
    plot_df['Marker_Size'] = plot_df['Medal'].apply(lambda m: 12 if m in ['gold', 'silver', 'bronze'] else 4)
    plot_df['Medal_Rank'] = plot_df['Medal'].map({'gold': 1, 'silver': 2, 'bronze': 3, 'no medal': 4})
    plot_df = plot_df.sort_values(by=['Medal_Rank'], ascending=False)
    
    # เพิ่ม template="plotly_white"
    fig_ath = px.scatter(
        plot_df, x='Year', y='Sport', color='Medal', size='Marker_Size',
        hover_name='Event', hover_data={'Year': True, 'Sport': False, 'City': True, 'Marker_Size': False, 'Medal_Rank': False},
        color_discrete_map=color_map, title="จุดกลมใหญ่ = ได้เหรียญรางวัล | เอาเมาส์ชี้เพื่อดู Event การแข่งขัน",
        template="plotly_white"
    )
    fig_ath.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig_ath.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#000000"),
        xaxis=dict(dtick=4, title="ปีที่แข่งขัน (Year)"), yaxis=dict(title="ประเภทกีฬา (Sport)"), height=400
    )
    st.plotly_chart(fig_ath, width="stretch")

    st.markdown("#### 📝 ประวัติการลงแข่งทั้งหมด (Detailed Event Log)")
    hist_table = ath_df[['Year', 'Season', 'City', 'Sport', 'Event', 'Medal']].sort_values('Year', ascending=False)
    st.dataframe(hist_table, hide_index=True, width="stretch", height=300)

st.markdown("---")
st.markdown("© 2026 Olympic Analytics Dashboard | Built with Streamlit")