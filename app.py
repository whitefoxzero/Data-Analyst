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
# 2. UI/UX & Custom CSS (Soft Cream Theme)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    /* Force ALL text to black */
    html, body, [class*="css"]  {
        color: #000000 !important;
    }

    .stApp {
        background-color: #FDFBF7;
        color: #000000 !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
    }

    /* Markdown & Text */
    .stMarkdown, .stText, p, span, label {
        color: #000000 !important;
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #F5EFE6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.05);
        border: 1px solid #E6DCCD;
    }

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricValue"] {
        color: #000000 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] * {
        color: #000000 !important;
    }

    /* Plotly Titles */
    .stPlotlyChart * {
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. Data Loading & Cleaning (รวมโค้ดที่ 1 และ 2 เข้าด้วยกันตรงนี้)
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_clean_data():
    """
    โหลดข้อมูลและทำความสะอาดข้อมูลในฟังก์ชันเดียว 
    ใช้ @st.cache_data เพื่อไม่ให้ Streamlit ทำความสะอาดข้อมูลซ้ำทุกครั้งที่กด Filter
    """
    try:
        # 1. โหลดข้อมูล
        df = pd.read_csv("dataset2.csv")

        # 2. ลบคอลัมน์ที่ไม่จำเป็น (Cleaning)
        if 'notes' in df.columns:
            df = df.drop(columns=['notes'])

        if 'Name' in df.columns:
            df = df[df['Name'].str.match(
            r'^[^\W\d_]+(?:[ \.\-][^\W\d_]+)*$', 
            na=False
        )]

        # 3. จัดการชนิดข้อมูล (Data Types) ให้เหมาะสมและประหยัดหน่วยความจำ
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
        
        # ตรวจสอบว่ามีคอลัมน์เหล่านี้ก่อนแปลงเป็น category
        cat_cols = ['Sex', 'Season', 'Team', 'NOC', 'Sport', 'Event', 'City']
        existing_cat_cols = [col for col in cat_cols if col in df.columns]
        df[existing_cat_cols] = df[existing_cat_cols].astype('category')

        # 4. จัดการคอลัมน์ Medal (ตัวแปรเป้าหมายที่สำคัญ)
        df['Medal'] = df['Medal'].astype(str)

# 2️⃣ ทำความสะอาด
        df['Medal'] = df['Medal'].str.strip().str.lower()

# 3️⃣ แทนค่าที่ไม่ใช่เหรียญเป็น NaN
        df['Medal'] = df['Medal'].replace({
        'no medal': np.nan,
        '-': np.nan
        })

# 4️⃣ เติม NaN เป็น 'no medal'
        df['Medal'] = df['Medal'].fillna('no medal')

# 5️⃣ แปลงเป็น category ตอนสุดท้าย
        df['Medal'] = df['Medal'].astype('category')

        # 5. จัดการค่าว่างของ 'region'
        if 'region' in df.columns:
            df['region'] = df['region'].fillna('Unknown')

        # 6. ตรวจสอบและจัดการค่าผิดปกติทางกายภาพ (Logical Outliers)
        df.loc[(df['Age'] > 75) | (df['Age'] < 10), 'Age'] = np.nan 
        if 'Height' in df.columns:
            df.loc[(df['Height'] > 250) | (df['Height'] < 120), 'Height'] = np.nan
        if 'Weight' in df.columns:
            df.loc[(df['Weight'] > 200) | (df['Weight'] < 25), 'Weight'] = np.nan

        # 7. จัดการค่าว่างด้วยวิธีที่เหมาะสม (Group Imputation)
        cols_to_impute = [col for col in ['Age', 'Height', 'Weight'] if col in df.columns]
        for col in cols_to_impute:
            # เติมค่าว่างด้วยค่า Median โดยจัดกลุ่มตาม "เพศ" และ "ประเภทกีฬา"
            df[col] = df.groupby(['Sex', 'Sport'])[col].transform(lambda x: x.fillna(x.median()))
            # กรณีหา Median ไม่ได้ ให้เติมด้วย Median ของ "เพศ" นั้นๆ แทน
            df[col] = df.groupby('Sex')[col].transform(lambda x: x.fillna(x.median()))
            # กรณีกันเหนียว (Fallback) หากยังมีค่าว่างเหลืออีก ให้เติมด้วย Median รวม
            df[col] = df[col].fillna(df[col].median())

        # 8. ลบข้อมูลที่ซ้ำซ้อน (Completeness)
        df.drop_duplicates(inplace=True)

        return df

    except FileNotFoundError:
        st.error("Error: 'dataset2.csv' not found. Please ensure the file exists.")
        return pd.DataFrame()

# เรียกใช้งานฟังก์ชันโหลดและทำความสะอาดข้อมูล
df = load_and_clean_data()

# หยุดการทำงานถ้าไม่มีข้อมูล
if df.empty:
    st.stop()

# -----------------------------------------------------------------------------
# 4. Sidebar Filters
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Filters")

# Year Range Slider
min_year = int(df['Year'].min())
max_year = int(df['Year'].max())
year_range = st.sidebar.slider(
    "Select Year Range:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Sport Filter
all_sports = sorted(df['Sport'].dropna().unique())
selected_sports = st.sidebar.multiselect(
    "Select Sport(s):",
    options=all_sports,
    default=all_sports[:5] # Default to first 5
)
if not selected_sports:
    selected_sports = all_sports

# Medal Type Filter
medal_options = ['gold', 'silver', 'bronze', 'no medal']
selected_medals = st.sidebar.multiselect(
    "Select Medal Type(s):",
    options=medal_options,
    default=medal_options
)

# Apply Filters
df_filtered = df[
    (df['Year'] >= year_range[0]) & 
    (df['Year'] <= year_range[1]) &
    (df['Sport'].isin(selected_sports if selected_sports else all_sports)) &
    (df['Medal'].isin(selected_medals if selected_medals else medal_options))
]

# Color mapping
color_map = {
    'gold': '#FFD700',
    'silver': '#C0C0C0',
    'bronze': '#CD7F32',
    'no medal': '#E0E0E0'
}

# -----------------------------------------------------------------------------
# 5. Header
# -----------------------------------------------------------------------------
st.title("🏅 Olympic Analytics Dashboard")
st.markdown("---")

# -----------------------------------------------------------------------------
# SECTION 1: Medal Overview
# -----------------------------------------------------------------------------
st.subheader("📊 Global Medal Overview")

total_gold = df_filtered[df_filtered['Medal'] == 'gold'].shape[0]
total_silver = df_filtered[df_filtered['Medal'] == 'silver'].shape[0]
total_bronze = df_filtered[df_filtered['Medal'] == 'bronze'].shape[0]
total_no_medal = df_filtered[df_filtered['Medal'] == 'no medal'].shape[0]
total_athletes = df_filtered['Name'].nunique()

m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("Total Gold", f"{total_gold:,}")
with m2: st.metric("Total Silver", f"{total_silver:,}")
with m3: st.metric("Total Bronze", f"{total_bronze:,}")
with m4: st.metric("Participations (No Medal)", f"{total_no_medal:,}")
with m5: st.metric("Unique Athletes", f"{total_athletes:,}")

st.markdown("<br>", unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    st.markdown("#### 📅 Medal Count by Year")
    count_by_year = df_filtered.groupby(['Year', 'Medal']).size().reset_index(name='Count')
    fig_year = px.bar(
        count_by_year, 
        x='Year', 
        y='Count', 
        color='Medal',
        color_discrete_map=color_map,
        title="Medals per Year",
        barmode='group'
    )
    fig_year.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_year, width="stretch")

with c2:
    st.markdown("#### 🏃‍♂️ Medal Count by Sport")
    sport_counts = df_filtered.groupby(['Sport', 'Medal']).size().reset_index(name='Count')
    sport_total = sport_counts.groupby('Sport')['Count'].sum().reset_index().sort_values('Count', ascending=False)
    top_sports = sport_total.head(15)['Sport'].tolist()
    sport_counts_filtered = sport_counts[sport_counts['Sport'].isin(top_sports)]
    
    fig_sport = px.bar(
        sport_counts_filtered,
        x='Sport',
        y='Count',
        color='Medal',
        color_discrete_map=color_map,
        title="Top 15 Sports by Medal Count (Descending)",
        category_orders={"Sport": top_sports} 
    )
    fig_sport.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_sport, width="stretch")

st.divider()

# -----------------------------------------------------------------------------
# SECTION 2: Athlete Profile Explorer
# -----------------------------------------------------------------------------
st.subheader("👤 Athlete Profile Explorer")



filtered_names = (
        df['Name']
        .dropna()
        .astype(str)
        .loc[lambda x: x.str.contains(search_text, case=False, na=False)]
        .unique()
    )

selected_athlete = st.selectbox(
        "Select Athlete:",
        options=[""] + list(filtered_names[:10])
    )

if selected_athlete:
    ath_df = df[df['Name'] == selected_athlete]
    latest_ath = ath_df.sort_values('Year', ascending=False).iloc[0]
    
    st.markdown(f"##### Profile: {latest_ath['Name']}")
    
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("Sex", latest_ath['Sex'])
    p2.metric("Age", f"{int(latest_ath['Age'])}" if pd.notna(latest_ath['Age']) else "N/A")
    p3.metric("Height", f"{int(latest_ath['Height'])} cm" if pd.notna(latest_ath['Height']) else "N/A")
    p4.metric("Weight", f"{int(latest_ath['Weight'])} kg" if pd.notna(latest_ath['Weight']) else "N/A")
    p5.metric("Team", latest_ath['Team'])
    p6.metric("Region", latest_ath['region'] if pd.notna(latest_ath['region']) else "N/A")
    
    st.markdown("###### Career Medal Summary")
    ath_gold = len(ath_df[ath_df['Medal'] == 'Gold'])
    ath_silver = len(ath_df[ath_df['Medal'] == 'Silver'])
    ath_bronze = len(ath_df[ath_df['Medal'] == 'Bronze'])
    ath_no_medal = len(ath_df[ath_df['Medal'] == 'No Medal'])
    
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("🥇 Gold", ath_gold)
    a2.metric("🥈 Silver", ath_silver)
    a3.metric("🥉 Bronze", ath_bronze)
    a4.metric("Participations", ath_no_medal)
    
    r1, r2 = st.columns([2, 1])
    
    with r1:
        st.markdown("###### Medal History by Year")
        ath_hist = ath_df.groupby(['Year', 'Medal']).size().reset_index(name='Count')
        fig_ath = px.bar(
            ath_hist, x='Year', y='Count', color='Medal',
            color_discrete_map=color_map, barmode='stack',
            title=f"Medal Timeline for {selected_athlete}"
        )
        fig_ath.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig_ath.update_yaxes(dtick=1) 
        st.plotly_chart(fig_ath, width="stretch")
        
    with r2:
        st.markdown("###### Competition Log")
        hist_table = ath_df[['Year', 'Season', 'City', 'Sport', 'Event', 'Medal']].sort_values('Year', ascending=False)
        st.dataframe(hist_table, hide_index=True, width="stretch", height=400)

else:
    st.info("👆 Please select an athlete above to view their profile.")

st.divider()

# -----------------------------------------------------------------------------
# SECTION 3: Athlete Ranking Summary
# -----------------------------------------------------------------------------
st.subheader("🏆 Top 20 Athletes (Leaderboard)")

medals_only = df[df['Medal'].isin(['Gold', 'Silver', 'Bronze'])]

leaderboard = medals_only.groupby('Name')['Medal'].count().reset_index(name='Total Medals')
leaderboard = leaderboard.sort_values('Total Medals', ascending=False).head(20)

col_rank1, col_rank2 = st.columns(2)

with col_rank1:
    st.markdown("#### Top 20 by Total Medals")
    fig_rank = px.bar(
        leaderboard,
        x='Total Medals',
        y='Name',
        orientation='h',
        title="All-Time Medal Leaders",
        color='Total Medals',
        color_continuous_scale='Viridis'
    )
    fig_rank.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_rank, width="stretch")

with col_rank2:
    st.markdown("#### Leaderboard Data")
    top_names = leaderboard['Name'].tolist()
    detailed_leaderboard = medals_only[medals_only['Name'].isin(top_names)].groupby(['Name', 'Medal']).size().unstack(fill_value=0)
    
    for col in ['Gold', 'Silver', 'Bronze']:
        if col not in detailed_leaderboard.columns:
            detailed_leaderboard[col] = 0
            
    detailed_leaderboard['Total'] = detailed_leaderboard['Gold'] + detailed_leaderboard['Silver'] + detailed_leaderboard['Bronze']
    detailed_leaderboard = detailed_leaderboard.sort_values('Total', ascending=False)
    
    st.dataframe(detailed_leaderboard, width="stretch")

# Footer
st.markdown("---")
st.markdown("© 2026 Olympic Analytics Dashboard | Built with Streamlit")