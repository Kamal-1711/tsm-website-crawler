# validation.py

import pandas as pd

df = pd.read_csv('output/tsm_crawl_data.csv')

print("=" * 50)
print("TSM CRAWLER VALIDATION REPORT")
print("=" * 50)
print(f"✓ Total Pages Crawled: {len(df)}")
print(f"✓ Unique URLs: {df['url'].nunique()}")
print(f"✓ Max Depth Reached: {df['depth'].max()}")

print(f"\nPages by Depth:")
print(df['depth'].value_counts().sort_index())

print(f"\nStatus Codes Distribution:")
print(df['status_code'].value_counts())

print(f"\nTop 5 Pages with Most Links:")
print(df.nlargest(5, 'child_count')[['url', 'child_count', 'title']])

print("=" * 50)

