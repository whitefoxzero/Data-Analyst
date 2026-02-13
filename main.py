
import pandas as pd
import numpy as np

# 1. โหลดข้อมูล
df = pd.read_csv("dataset2.csv")
print("--- จำนวนค่าว่าง 'ก่อน' ทำความสะอาด ---")
print(df.isnull().sum())

# 2. ลบคอลัมน์ที่ไม่จำเป็น (Cleaning)
if 'notes' in df.columns:
    df = df.drop(columns=['notes'])

# 3. จัดการชนิดข้อมูล (Data Types) ให้เหมาะสมและประหยัดหน่วยความจำ
df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
df[['Sex', 'Season', 'Team', 'NOC', 'Sport', 'Event', 'City']] = df[['Sex', 'Season', 'Team', 'NOC', 'Sport', 'Event', 'City']].astype('category')

# 4. จัดการคอลัมน์ Medal (ตัวแปรเป้าหมายที่สำคัญ)
df['Medal'] = df['Medal'].astype('category')
if 'No Medal' not in df['Medal'].cat.categories:
    df['Medal'] = df['Medal'].cat.add_categories('No Medal')
df['Medal'] = df['Medal'].fillna('No Medal')

# 5. จัดการค่าว่างของ 'region'
df['region'] = df['region'].fillna('Unknown')

# 6. ตรวจสอบและจัดการค่าผิดปกติทางกายภาพ (Logical Outliers)
# กำหนดขอบเขตที่เป็นไปได้จริง หากอยู่นอกเหนือนี้ให้มองเป็นค่าว่าง (NaN) เพื่อนำไป Impute ใหม่
df.loc[(df['Age'] > 75) | (df['Age'] < 10), 'Age'] = np.nan 
df.loc[(df['Height'] > 250) | (df['Height'] < 120), 'Height'] = np.nan
df.loc[(df['Weight'] > 200) | (df['Weight'] < 25), 'Weight'] = np.nan

# 7. จัดการค่าว่างด้วยวิธีที่เหมาะสม (Group Imputation) **[จุดเก็บคะแนน]**
cols_to_impute = ['Age', 'Height', 'Weight']
for col in cols_to_impute:
    # เติมค่าว่างด้วยค่า Median โดยจัดกลุ่มตาม "เพศ" และ "ประเภทกีฬา"
    df[col] = df.groupby(['Sex', 'Sport'])[col].transform(lambda x: x.fillna(x.median()))
    
    # กรณีที่บางชนิดกีฬามีข้อมูลน้อยมากจนหา Median ไม่ได้ ให้เติมด้วย Median ของ "เพศ" นั้นๆ แทน
    df[col] = df.groupby('Sex')[col].transform(lambda x: x.fillna(x.median()))
    
    # กรณีกันเหนียว (Fallback) หากยังมีค่าว่างเหลืออีก ให้เติมด้วย Median รวม
    df[col] = df[col].fillna(df[col].median())

# 8. ลบข้อมูลที่ซ้ำซ้อน (Completeness)
df.drop_duplicates(inplace=True)

print("\n--- จำนวนค่าว่าง 'หลัง' ทำความสะอาด ---")
print(df.isnull().sum())

print(df.loc[~df['Medal'].isin(['Gold', 'Silver', 'Bronze']), 'Medal'].unique())
