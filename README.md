# 安徽高考数据查询系统

基于 2023-2025 年安徽省高考录取数据，提供名次匹配、专业查询、院校详情等功能。

## 数据

- 2,192 所院校
- 12,857 个专业
- 43,190 条录取记录

## 快速启动

### Docker（推荐）

```bash
docker compose up -d
```

访问 `http://localhost:5000`

### 本地 Python

```bash
pip install flask
python server.py
```

访问 `http://localhost:5000`

## 数据生成

如果 `gaokao.db` 不存在，先放置原始 Excel 文件 `安徽-2026-专家版数据23-26.xlsx`，然后执行：

```bash
python process_data.py    # Excel → JSON
python create_db.py        # JSON → SQLite
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `server.py` | Flask API 后端 |
| `index.html` | 前端界面 |
| `Dockerfile` | Docker 镜像 |
| `docker-compose.yml` | Docker 编排 |
| `process_data.py` | Excel → JSON |
| `create_db.py` | JSON → SQLite |

## 功能

- 🎯 名次匹配：输入排名，±N 范围内匹配院校专业
- 📖 专业查询：按专业查看所有院校的历年录取数据
- 🏫 院校查询：查看院校详细信息+历年趋势图表
- 🔍 高级筛选：多维度组合筛选
