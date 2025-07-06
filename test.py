import pandas as pd

df = pd.read_csv('crypto_coins_sample.csv')

df_filter = df[df['Launch_Year'] > 2017]

for i in df_filter:
    print(i)