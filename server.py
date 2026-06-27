"""
GAOKAO Data Query System - Backend API
Flask app serving gaokao admission data with filtering, ranking, and recommendations.
"""
import sqlite3
import json
from flask import Flask, request, jsonify, g, send_from_directory
import os

app = Flask(__name__, static_folder='.')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gaokao.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ---------- HTML Page ----------
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# ---------- Filter Options API ----------
@app.route('/api/filter-options')
def filter_options():
    db = get_db()
    options = {}

    # These are the distinct values we want for dropdowns
    queries = {
        'batch': 'SELECT DISTINCT batch FROM gaokao WHERE batch IS NOT NULL AND batch != "" ORDER BY batch',
        'subject_category': 'SELECT DISTINCT subject_category FROM gaokao WHERE subject_category IS NOT NULL AND subject_category != "" ORDER BY subject_category',
        'school_province': 'SELECT DISTINCT school_province FROM gaokao WHERE school_province IS NOT NULL AND school_province != "" ORDER BY school_province',
        'school_city': 'SELECT DISTINCT school_city FROM gaokao WHERE school_city IS NOT NULL AND school_city != "" ORDER BY school_city',
        'school_type': 'SELECT DISTINCT school_type FROM gaokao WHERE school_type IS NOT NULL AND school_type != "" ORDER BY school_type',
        'school_nature': 'SELECT DISTINCT school_nature FROM gaokao WHERE school_nature IS NOT NULL AND school_nature != "" ORDER BY school_nature',
        'school_degree_level': 'SELECT DISTINCT school_degree_level FROM gaokao WHERE school_degree_level IS NOT NULL AND school_degree_level != "" ORDER BY school_degree_level',
        'school_tag': 'SELECT DISTINCT school_tag FROM gaokao WHERE school_tag IS NOT NULL AND school_tag != "" ORDER BY school_tag',
        'major_category': 'SELECT DISTINCT major_category FROM gaokao WHERE major_category IS NOT NULL AND major_category != "" ORDER BY major_category',
        'subject_requirement': 'SELECT DISTINCT subject_requirement FROM gaokao WHERE subject_requirement IS NOT NULL AND subject_requirement != "" ORDER BY subject_requirement',
    }

    for key, sql in queries.items():
        rows = db.execute(sql).fetchall()
        options[key] = [r[0] for r in rows]

    return jsonify(options)


# ---------- Main Search API ----------
@app.route('/api/search')
def search():
    db = get_db()

    # Collect filters
    conditions = []
    params = []

    # Text search
    school_name = request.args.get('school_name', '').strip()
    if school_name:
        conditions.append('school_name LIKE ?')
        params.append(f'%{school_name}%')

    major_name = request.args.get('major_name', '').strip()
    if major_name:
        conditions.append('major_full_name LIKE ?')
        params.append(f'%{major_name}%')

    # Dropdown filters
    for field in ['batch', 'subject_category', 'school_province', 'school_city',
                  'school_type', 'school_nature', 'school_degree_level', 'school_tag',
                  'major_category', 'subject_requirement']:
        val = request.args.get(field, '').strip()
        if val:
            conditions.append(f'{field} = ?')
            params.append(val)

    # Score range
    min_score = request.args.get('min_score', '').strip()
    max_score = request.args.get('max_score', '').strip()
    if min_score:
        conditions.append('CAST(avg_score_2025 AS REAL) >= ?')
        params.append(float(min_score))
    if max_score:
        conditions.append('CAST(avg_score_2025 AS REAL) <= ?')
        params.append(float(max_score))

    # Tuition range
    min_tuition = request.args.get('min_tuition', '').strip()
    max_tuition = request.args.get('max_tuition', '').strip()
    if min_tuition:
        conditions.append('CAST(tuition AS REAL) >= ?')
        params.append(float(min_tuition))
    if max_tuition:
        conditions.append('CAST(tuition AS REAL) <= ?')
        params.append(float(max_tuition))

    # Study years
    study_years = request.args.get('study_years', '').strip()
    if study_years:
        conditions.append('study_years = ?')
        params.append(int(study_years))

    where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''

    # Sorting
    sort_by = request.args.get('sort_by', 'avg_rank_2025')
    sort_order = request.args.get('sort_order', 'asc')

    allowed_sort = [
        'school_name', 'major_full_name', 'avg_score_2025', 'avg_rank_2025',
        'lowest_score_2025', 'lowest_rank_2025', 'highest_score_2025', 'highest_rank_2025',
        'avg_score_2024', 'avg_rank_2024', 'avg_score_2023', 'avg_rank_2023',
        'tuition', 'study_years', 'plan_count', 'batch'
    ]
    if sort_by not in allowed_sort:
        sort_by = 'avg_rank_2025'
    if sort_order not in ('asc', 'desc'):
        sort_order = 'asc'

    order_clause = f'ORDER BY CAST({sort_by} AS REAL) {sort_order} NULLS LAST'

    # Pagination
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(10, int(request.args.get('per_page', 30))))
    offset = (page - 1) * per_page

    # Count total
    count_sql = f'SELECT COUNT(*) FROM gaokao {where}'
    total = db.execute(count_sql, params).fetchone()[0]

    # Query data
    data_sql = f'SELECT * FROM gaokao {where} {order_clause} LIMIT ? OFFSET ?'
    rows = db.execute(data_sql, params + [per_page, offset]).fetchall()

    results = [dict(r) for r in rows]

    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'results': results,
    })


# ---------- School Detail API ----------
@app.route('/api/school/<path:school_name>')
def school_detail(school_name):
    db = get_db()

    # Get all records for this school
    rows = db.execute(
        'SELECT * FROM gaokao WHERE school_name = ? ORDER BY CAST(avg_rank_2025 AS REAL) ASC',
        [school_name]
    ).fetchall()

    if not rows:
        return jsonify({'error': 'School not found'}), 404

    records = [dict(r) for r in rows]

    # Build school summary
    first = records[0]
    summary = {
        'school_name': first['school_name'],
        'school_code': first['school_code'],
        'school_province': first['school_province'],
        'school_city': first['school_city'],
        'school_type': first['school_type'],
        'school_nature': first['school_nature'],
        'school_degree_level': first['school_degree_level'],
        'school_tag': first['school_tag'],
        'school_level': first['school_level'],
        'school_level_tag': first['school_level_tag'],
        'school_unit': first['school_unit'],
        'school_description': first['school_description'],
        'school_transfer_policy': first['school_transfer_policy'],
        'school_district': first['school_district'],
        'school_master_count': first['school_master_count'],
        'school_master_majors': first['school_master_majors'],
        'school_phd_count': first['school_phd_count'],
        'school_phd_majors': first['school_phd_majors'],
        'school_admission_guide_2025': first['school_admission_guide_2025'],
        'school_merge_info': first['school_merge_info'],
    }

    # Build majors list with historical data
    majors = []
    for r in records:
        majors.append({
            'major_full_name': r['major_full_name'],
            'major_short_name': r['major_short_name'],
            'major_code': r['major_code'],
            'major_category': r['major_category'],
            'major_class': r['major_class'],
            'major_intro': r['major_intro'],
            'major_objective': r['major_objective'],
            'major_requirements': r['major_requirements'],
            'major_level': r['major_level'],
            'major_master_point': r['major_master_point'],
            'major_phd_point': r['major_phd_point'],
            'batch': r['batch'],
            'subject_category': r['subject_category'],
            'subject_requirement': r['subject_requirement'],
            'study_years': r['study_years'],
            'tuition': r['tuition'],
            'plan_count': r['plan_count'],
            'admission': {
                '2025': {
                    'admit_count': r['admit_count_2025'],
                    'lowest_score': r['lowest_score_2025'],
                    'lowest_rank': r['lowest_rank_2025'],
                    'avg_score': r['avg_score_2025'],
                    'avg_rank': r['avg_rank_2025'],
                    'highest_score': r['highest_score_2025'],
                    'highest_rank': r['highest_rank_2025'],
                },
                '2024': {
                    'admit_count': r['admit_count_2024'],
                    'lowest_score': r['lowest_score_2024'],
                    'lowest_rank': r['lowest_rank_2024'],
                    'avg_score': r['avg_score_2024'],
                    'avg_rank': r['avg_rank_2024'],
                    'highest_score': r['highest_score_2024'],
                    'highest_rank': r['highest_rank_2024'],
                },
                '2023': {
                    'admit_count': r['admit_count_2023'],
                    'lowest_score': r['lowest_score_2023'],
                    'lowest_rank': r['lowest_rank_2023'],
                    'avg_score': r['avg_score_2023'],
                    'avg_rank': r['avg_rank_2023'],
                    'highest_score': r['highest_score_2023'],
                    'highest_rank': r['highest_rank_2023'],
                },
            }
        })

    return jsonify({
        'summary': summary,
        'majors': majors,
        'major_count': len(majors),
    })


# ---------- Rank Match API ----------
@app.route('/api/rank-match')
def rank_match():
    """Match schools by rank: input your rank, get schools within ±gap rank range"""
    db = get_db()

    rank = request.args.get('rank', '').strip()
    gap = request.args.get('gap', '1000').strip()

    if not rank:
        return jsonify({'error': 'Please provide a rank (位次)'}), 400

    try:
        rank = int(rank)
        gap = int(gap)
    except ValueError:
        return jsonify({'error': 'Invalid rank/gap value'}), 400

    min_rank = max(1, rank - gap)
    max_rank = rank + gap

    # Additional filters
    batch = request.args.get('batch', '').strip()
    subject_category = request.args.get('subject_category', '').strip()
    major_name = request.args.get('major_name', '').strip()

    conditions = [
        'CAST(avg_rank_2025 AS REAL) >= ?',
        'CAST(avg_rank_2025 AS REAL) <= ?'
    ]
    params = [min_rank, max_rank]

    if batch:
        conditions.append('batch = ?')
        params.append(batch)
    if subject_category:
        conditions.append('subject_category = ?')
        params.append(subject_category)
    if major_name:
        conditions.append('major_full_name LIKE ?')
        params.append(f'%{major_name}%')

    where = 'WHERE ' + ' AND '.join(conditions)

    rows = db.execute(
        f'SELECT * FROM gaokao {where} ORDER BY CAST(avg_rank_2025 AS REAL) ASC',
        params
    ).fetchall()

    results = [dict(r) for r in rows]

    # Group by school for summary
    schools_map = {}
    for r in results:
        sn = r['school_name']
        if sn not in schools_map:
            schools_map[sn] = {
                'school_name': sn,
                'school_code': r['school_code'],
                'school_province': r['school_province'],
                'school_city': r['school_city'],
                'school_type': r['school_type'],
                'school_nature': r['school_nature'],
                'school_degree_level': r['school_degree_level'],
                'school_tag': r['school_tag'],
                'majors': [],
            }
        schools_map[sn]['majors'].append({
            'major_full_name': r['major_full_name'],
            'batch': r['batch'],
            'subject_category': r['subject_category'],
            'avg_score_2025': r['avg_score_2025'],
            'avg_rank_2025': r['avg_rank_2025'],
            'lowest_score_2025': r['lowest_score_2025'],
            'lowest_rank_2025': r['lowest_rank_2025'],
            'tuition': r['tuition'],
            'study_years': r['study_years'],
            'plan_count': r['plan_count'],
        })

    return jsonify({
        'your_rank': rank,
        'gap': gap,
        'rank_range': [min_rank, max_rank],
        'total_schools': len(schools_map),
        'total_majors': len(results),
        'schools': sorted(schools_map.values(), key=lambda x: x['school_name']),
        'all_results': results,
    })


# ---------- Major History API ----------
@app.route('/api/major-history')
def major_history():
    """Get historical admission data for a specific major across all schools"""
    db = get_db()

    major_name = request.args.get('major_name', '').strip()
    if not major_name:
        return jsonify({'error': 'Please provide a major name'}), 400

    batch = request.args.get('batch', '').strip()
    subject_category = request.args.get('subject_category', '').strip()

    conditions = ['major_full_name LIKE ?']
    params = [f'%{major_name}%']

    if batch:
        conditions.append('batch = ?')
        params.append(batch)
    if subject_category:
        conditions.append('subject_category = ?')
        params.append(subject_category)

    where = 'WHERE ' + ' AND '.join(conditions)

    rows = db.execute(
        f'SELECT * FROM gaokao {where} ORDER BY CAST(avg_rank_2025 AS REAL) ASC',
        params
    ).fetchall()

    results = [dict(r) for r in rows]

    # Group stats
    ranks_2025 = [r['avg_rank_2025'] for r in results if r['avg_rank_2025']]
    scores_2025 = [r['avg_score_2025'] for r in results if r['avg_score_2025']]

    return jsonify({
        'major_name': major_name,
        'total': len(results),
        'results': results,
        'stats': {
            'school_count': len(set(r['school_name'] for r in results)),
            'avg_rank_2025': sum(ranks_2025) / len(ranks_2025) if ranks_2025 else None,
            'min_rank_2025': min(ranks_2025) if ranks_2025 else None,
            'max_rank_2025': max(ranks_2025) if ranks_2025 else None,
            'avg_score_2025': sum(scores_2025) / len(scores_2025) if scores_2025 else None,
        }
    })


# ---------- School Autocomplete API ----------
@app.route('/api/autocomplete/schools')
def autocomplete_schools():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    db = get_db()
    rows = db.execute(
        'SELECT DISTINCT school_name FROM gaokao WHERE school_name LIKE ? ORDER BY school_name LIMIT 20',
        [f'%{q}%']
    ).fetchall()
    return jsonify([r[0] for r in rows])


@app.route('/api/autocomplete/majors')
def autocomplete_majors():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    db = get_db()
    rows = db.execute(
        'SELECT DISTINCT major_full_name FROM gaokao WHERE major_full_name LIKE ? ORDER BY major_full_name LIMIT 20',
        [f'%{q}%']
    ).fetchall()
    return jsonify([r[0] for r in rows])


# ---------- School List API (for reference) ----------
@app.route('/api/schools')
def list_schools():
    """List all schools with basic info"""
    db = get_db()
    rows = db.execute(
        'SELECT DISTINCT school_name, school_code, school_province, school_city, school_type, '
        'school_nature, school_degree_level, school_tag, school_level, school_description '
        'FROM gaokao ORDER BY school_name'
    ).fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == '__main__':
    import os
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    print('GAOKAO Data Server starting on http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=debug)
