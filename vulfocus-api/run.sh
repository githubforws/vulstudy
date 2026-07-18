#!/bin/sh

# 启动系统服务
service redis-server start
service nginx start

# 执行数据库迁移（首次启动必须）
python /vulfocus-api/manage.py migrate --noinput

# 确保新增的 network_type 列和相关表存在（处理迁移状态污染的情况）
python /vulfocus-api/manage.py shell <<EOF
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vulfocus.settings")
import django; django.setup()
from django.db import connection
c = connection.cursor()

c.execute("PRAGMA table_info(layout)")
cols = [r[1] for r in c.fetchall()]

if "network_type" not in cols:
    c.execute('ALTER TABLE layout ADD COLUMN network_type varchar(20) NOT NULL DEFAULT "legacy"')
    print("[schema] Added network_type column to layout")

c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='network_segment'")
if not c.fetchone():
    c.execute('CREATE TABLE network_segment (segment_id char(32) NOT NULL PRIMARY KEY, layout_id char(32) NOT NULL REFERENCES layout(layout_id), network_type varchar(20) NOT NULL, network_name varchar(255) NOT NULL UNIQUE, subnet varchar(18) NOT NULL, gateway varchar(15) NOT NULL, icc_enabled bool NOT NULL, create_date datetime NOT NULL)')
    print("[schema] Created network_segment table")

c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='service_network_access'")
if not c.fetchone():
    c.execute('CREATE TABLE service_network_access (access_id char(32) NOT NULL PRIMARY KEY, service_id char(32) NOT NULL REFERENCES layout_service(service_id), segment_id char(32) NOT NULL REFERENCES network_segment(segment_id), ipv4_address varchar(15) NOT NULL, create_date datetime NOT NULL)')
    print("[schema] Created service_network_access table")
EOF

# 启动 Django 开发服务器（后台运行）
python /vulfocus-api/manage.py runserver 0.0.0.0:8000 &

# 等待 Django 完全初始化（约 3~5 秒，取决于项目大小）
sleep 3

# 启动 Celery worker 和 beat（合并启动）
celery -A vulfocus worker --beat --loglevel=info