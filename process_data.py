import pandas as pd
import json
import math

# Read Excel
df_raw = pd.read_excel('安徽-2026-专家版数据23-26.xlsx', header=None)

# Row 0: group headers, Row 1: actual column headers, Row 2+: data
col_groups = df_raw.iloc[0].tolist()
col_headers = df_raw.iloc[1].tolist()

# Build clean column names with group prefix
clean_cols = []
for i, (grp, col) in enumerate(zip(col_groups, col_headers)):
    g = str(grp) if pd.notna(grp) else ''
    c = str(col) if pd.notna(col) else ''
    clean_cols.append(f"{g}_{c}" if g and c else (c if c else f'Unnamed_{i}'))

# Print column mapping for reference
for i, (orig, clean) in enumerate(zip(col_headers, clean_cols)):
    print(f'  [{i}] {orig} -> {clean}')

# Extract data
data = df_raw.iloc[2:].copy()
data.columns = clean_cols

# Drop fully empty rows
data = data.dropna(how='all')

# Map English-friendly names
COLUMN_MAP = {
    clean_cols[0]: 'id',
    clean_cols[1]: 'year',
    clean_cols[2]: 'source_region',
    clean_cols[3]: 'batch',
    clean_cols[4]: 'subject_category',
    clean_cols[5]: 'plan_code',
    clean_cols[6]: 'school_code',
    clean_cols[7]: 'school_name',
    clean_cols[8]: 'school_major_group_code',
    clean_cols[9]: 'major_group_code',
    clean_cols[10]: 'major_group_name',
    clean_cols[11]: 'major_code',
    clean_cols[12]: 'major_full_name',
    clean_cols[13]: 'major_short_name',
    clean_cols[14]: 'major_note',
    clean_cols[15]: 'subject_requirement',
    clean_cols[16]: 'major_category',
    clean_cols[17]: 'plan_count',
    clean_cols[18]: 'study_years',
    clean_cols[19]: 'tuition',
    clean_cols[20]: 'included_majors',
    clean_cols[21]: 'major_group_plan_count',
    clean_cols[22]: 'category',
    clean_cols[23]: 'major_class',
    clean_cols[24]: 'admit_count_2025',
    clean_cols[25]: 'lowest_score_2025',
    clean_cols[26]: 'lowest_rank_2025',
    clean_cols[27]: 'admit_count_2025_detail',
    clean_cols[28]: 'lowest_score_2025_detail',
    clean_cols[29]: 'lowest_rank_2025_detail',
    clean_cols[30]: 'avg_score_2025',
    clean_cols[31]: 'avg_rank_2025',
    clean_cols[32]: 'highest_score_2025',
    clean_cols[33]: 'highest_rank_2025',
    clean_cols[34]: 'admit_count_2024',
    clean_cols[35]: 'lowest_score_2024',
    clean_cols[36]: 'lowest_rank_2024',
    clean_cols[37]: 'avg_score_2024',
    clean_cols[38]: 'avg_rank_2024',
    clean_cols[39]: 'highest_score_2024',
    clean_cols[40]: 'highest_rank_2024',
    clean_cols[41]: 'recruit_count_2024',
    clean_cols[42]: 'plan_count_2024',
    clean_cols[43]: 'admit_count_2023',
    clean_cols[44]: 'lowest_score_2023',
    clean_cols[45]: 'lowest_rank_2023',
    clean_cols[46]: 'avg_score_2023',
    clean_cols[47]: 'avg_rank_2023',
    clean_cols[48]: 'highest_score_2023',
    clean_cols[49]: 'highest_rank_2023',
    clean_cols[50]: 'recruit_count_2023',
    clean_cols[51]: 'plan_count_2023',
    clean_cols[52]: 'school_province',
    clean_cols[53]: 'school_city',
    clean_cols[54]: 'school_level_tag',
    clean_cols[55]: 'school_tag',
    clean_cols[56]: 'school_level',
    clean_cols[57]: 'school_merge_info',
    clean_cols[58]: 'school_unit',
    clean_cols[59]: 'school_type',
    clean_cols[60]: 'school_nature',
    clean_cols[61]: 'school_degree_level',
    clean_cols[62]: 'school_district',
    clean_cols[63]: 'school_description',
    clean_cols[64]: 'school_transfer_policy',
    clean_cols[65]: 'school_master_count',
    clean_cols[66]: 'school_master_majors',
    clean_cols[67]: 'school_phd_count',
    clean_cols[68]: 'school_phd_majors',
    clean_cols[69]: 'school_admission_guide_2025',
    clean_cols[70]: 'major_intro',
    clean_cols[71]: 'major_objective',
    clean_cols[72]: 'major_requirements',
    clean_cols[73]: 'major_level',
    clean_cols[74]: 'major_master_point',
    clean_cols[75]: 'major_phd_point',
}

# Rename columns
data = data.rename(columns=COLUMN_MAP)

# Keep only mapped columns
data = data[[c for c in COLUMN_MAP.values() if c in data.columns]]

# Convert numeric fields
numeric_fields = [
    'year', 'plan_count', 'study_years', 'tuition', 'major_group_plan_count',
    'admit_count_2025', 'lowest_score_2025', 'lowest_rank_2025', 'avg_score_2025', 'avg_rank_2025',
    'highest_score_2025', 'highest_rank_2025',
    'admit_count_2024', 'lowest_score_2024', 'lowest_rank_2024', 'avg_score_2024', 'avg_rank_2024',
    'highest_score_2024', 'highest_rank_2024', 'recruit_count_2024', 'plan_count_2024',
    'admit_count_2023', 'lowest_score_2023', 'lowest_rank_2023', 'avg_score_2023', 'avg_rank_2023',
    'highest_score_2023', 'highest_rank_2023', 'recruit_count_2023', 'plan_count_2023',
]

for f in numeric_fields:
    if f in data.columns:
        data[f] = pd.to_numeric(data[f], errors='coerce')

# Fill NaN with None for JSON
data = data.where(pd.notnull(data), None)

# Convert to list of dicts
records = data.to_dict(orient='records')

# Remove records that have no school_name
records = [r for r in records if r.get('school_name')]

print(f'\nTotal records: {len(records)}')

# Save JSON
with open('gaokao_data.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, default=str)

print('Data saved to gaokao_data.json')

# Print some stats
print(f'Schools: {len(set(r["school_name"] for r in records if r.get("school_name")))}')
print(f'Majors: {len(set(r["major_full_name"] for r in records if r.get("major_full_name")))}')
print(f'Batches: {sorted(set(str(r["batch"]) for r in records if r.get("batch")))}')
print(f'Subject categories: {sorted(set(str(r["subject_category"]) for r in records if r.get("subject_category")))}')
print(f'Provinces: {len(set(r["school_province"] for r in records if r.get("school_province")))}')

# Print sample record
print('\n=== Sample record ===')
for k, v in records[100].items():
    if v is not None and v != '':
        print(f'  {k}: {v}')
