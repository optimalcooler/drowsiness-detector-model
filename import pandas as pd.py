import pandas as pd
import numpy as np

# 1. Load the dataset
df = pd.read_csv('customer_data.csv')

# 2. Inspect shape and schema
print("Dataset Shape:", df.shape)  # (rows, columns)
print("\nColumn Info:")
df.info()

# 3. Check class balance of the target column
print("\nTarget Distribution:")
print(df['churn'].value_counts(normalize=True))