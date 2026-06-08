import csv
from pathlib import Path

csv_path = Path('dashboard/data/OBD_2024_I_2026-05-02T11_45_16 (1).csv')
with csv_path.open('r', encoding='utf-8-sig', errors='replace', newline='') as handle:
    reader = csv.reader(handle, delimiter=';')
    headers = next(reader)
    for row in reader:
        if row and row[0] == '82c533fa-7117-4101-a286-d2d7c207e696':
            print('row length', len(row))
            for index, value in enumerate(row):
                if value:
                    header = headers[index] if index < len(headers) else f'col_{index}'
                    print(index, header, value)
            break
