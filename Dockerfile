FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask waitress

# Copy application files
COPY server.py .
COPY index.html .
COPY gaokao.db .

# Create a non-root user
RUN useradd -m -s /bin/bash app && chown -R app:app /app
USER app

EXPOSE 5000

# Use waitress for production
CMD ["python", "-c", "from waitress import serve; from server import app; print('🚀 安徽高考数据查询系统已启动 → http://localhost:5000'); serve(app, host='0.0.0.0', port=5000)"]
