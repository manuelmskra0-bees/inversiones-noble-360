import pandas as pd

print("Convirtiendo HISTO26...")
# Agregamos on_bad_lines para saltar errores y el encoding para tildes
df1 = pd.read_csv('HISTO26.csv', on_bad_lines='skip', encoding='latin-1', low_memory=False)
df1.to_parquet('HISTO26.parquet')

print("Convirtiendo HISTORIAL 2025...")
df2 = pd.read_csv('HISTORIAL 2025.csv', on_bad_lines='skip', encoding='latin-1', low_memory=False)
df2.to_parquet('HISTORIAL_2025.parquet')

print("¡Listo! Archivos ligeros creados.")