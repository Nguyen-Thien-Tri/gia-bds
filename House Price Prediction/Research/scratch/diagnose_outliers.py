import pandas as pd
import numpy as np

df = pd.read_csv('filtered_hanoi_data.csv', encoding='utf-8', low_memory=False)
for col in ['Khoảng giá', 'Diện tích']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna(subset=['Khoảng giá', 'Diện tích'])

print(f"Total rows: {len(df)}")
print(f"Price Min: {df['Khoảng giá'].min():,.0f}")
print(f"Price Max: {df['Khoảng giá'].max():,.0f}")
print(f"Area Min: {df['Diện tích'].min():,.2f}")
print(f"Area Max: {df['Diện tích'].max():,.2f}")

# Check PPM outliers
ppm = df['Khoảng giá'] / df['Diện tích']
print(f"PPM Min: {ppm.min():,.0f}")
print(f"PPM Max: {ppm.max():,.0f}")

# Sample extreme PPM
print("\nExtreme low PPM samples (Possible price in Millions instead of VND?):")
print(df[ppm < 1e5][['Khoảng giá', 'Diện tích', 'Tiêu đề']].head())

print("\nExtreme high PPM samples:")
print(df[ppm > 1e10][['Khoảng giá', 'Diện tích', 'Tiêu đề']].head())
