#!/bin/sh

# 启动系统服务
service redis-server start
service nginx start

# 执行数据库迁移（首次启动必须）
python /vulfocus-api/manage.py migrate --noinput

# 启动 Django 开发服务器（后台运行）
python /vulfocus-api/manage.py runserver 0.0.0.0:8000 &

# 等待 Django 完全初始化（约 3~5 秒，取决于项目大小）
sleep 3

# 启动 Celery worker 和 beat（合并启动）
celery -A vulfocus worker --beat --loglevel=info