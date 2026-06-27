import sqlite3
import json

DB_PATH = 'gaokao.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Load JSON data
print('Loading JSON...')
with open('gaokao_data.json', 'r', encoding='utf-8') as f:
    records = json.load(f)
print(f'Loaded {len(records)} records')

# Get all column names from first record
all_cols = list(records[0].keys())
print(f'Columns: {len(all_cols)}')

# Create table
col_defs = []
for col in all_cols:
    if col in ('id', 'year', 'plan_count', 'study_years', 'tuition', 'major_group_plan_count',
               'admit_count_2025', 'lowest_score_2025', 'lowest_rank_2025', 'avg_score_2025', 'avg_rank_2025',
               'highest_score_2025', 'highest_rank_2025',
               'admit_count_2024', 'lowest_score_2024', 'lowest_rank_2024', 'avg_score_2024', 'avg_rank_2024',
               'highest_score_2024', 'highest_rank_2024', 'recruit_count_2024', 'plan_count_2024',
               'admit_count_2023', 'lowest_score_2023', 'lowest_rank_2023', 'avg_score_2023', 'avg_rank_2023',
               'highest_score_2023', 'highest_rank_2023', 'recruit_count_2023', 'plan_count_2023',
               'admit_count_2025_detail', 'lowest_score_2025_detail', 'lowest_rank_2025_detail',
               'school_master_count', 'school_phd_count'):
        col_defs.append(f'"{col}" REAL')
    else:
        col_defs.append(f'"{col}" TEXT')

create_sql = f'CREATE TABLE IF NOT EXISTS gaokao ({", ".join(col_defs)})'
cursor.execute(create_sql)

# Create indexes
cursor.execute('CREATE INDEX IF NOT EXISTS idx_school_name ON gaokao(school_name)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_major_full_name ON gaokao(major_full_name)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_batch ON gaokao(batch)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject_category ON gaokao(subject_category)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_school_province ON gaokao(school_province)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_school_type ON gaokao(school_type)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_school_tag ON gaokao(school_tag)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_avg_rank_2025 ON gaokao(avg_rank_2025)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_major_category ON gaokao(major_category)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_school_city ON gaokao(school_city)')

# Insert data in batches
placeholders = ', '.join(['?' for _ in all_cols])
insert_sql = f'INSERT INTO gaokao ({", ".join(f"\"{c}\"" for c in all_cols)}) VALUES ({placeholders})'

batch_size = 1000
for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]
    values = [[r.get(c) for c in all_cols] for r in batch]
    cursor.executemany(insert_sql, values)
    conn.commit()
    if (i + batch_size) % 10000 == 0:
        print(f'Inserted {min(i+batch_size, len(records))}/{len(records)}')

conn.commit()
print('Database created successfully!')

# Verify
cursor.execute('SELECT COUNT(*) FROM gaokao')
count = cursor.fetchone()[0]
print(f'Total rows in DB: {count}')

cursor.execute('SELECT COUNT(DISTINCT school_name) FROM gaokao')
schools = cursor.fetchone()[0]
print(f'Distinct schools: {schools}')

cursor.execute('SELECT COUNT(DISTINCT major_full_name) FROM gaokao')
majors = cursor.fetchone()[0]
print(f'Distinct majors: {majors}')

conn.close()
