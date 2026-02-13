import pandas as pd

df = pd.read_csv("dataset2.csv")

before = df.shape[0]

invalid_names = df[~df['Name'].str.match(r'^[^\W\d_]+(?:[ \.\-][^\W\d_]+)*$', na=False)]

print("Invalid rows:", invalid_names.shape[0])
print(invalid_names['Name'].head())
