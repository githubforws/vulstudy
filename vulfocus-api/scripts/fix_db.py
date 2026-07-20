#!/usr/bin/env python
"""
数据库迁移状态修复脚本 — 幂等、可重复执行

检测到的问题：
  4 个 app（dockerapi, network, tasks, layout_image）的 0001_initial.py 迁移文件
  曾经被删除，但 django_migrations 表中仍有 --fake 残留记录，导致 Django 认为迁移
  已应用而跳过建表。同时新增的 NetworkSegment / ServiceNetworkAccess 模型从未建表，
  Layout.network_type 字段从未添加。

修复逻辑（每次容器启动时运行）：
  1. 清理 django_migrations 表中 4 个 app 的所有残留记录（包括0001_initial和废弃的记录）
  2. 检查实际数据库表结构，创建缺失的表和列
  3. 重新运行 migrate --fake-initial 标记迁移状态为一致
"""

import os
import sys
import subprocess

# Django 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')

APPS_TO_FIX = ['dockerapi', 'network', 'tasks', 'layout_image']

# SQLite 建表语句（与 Django 自动生成的 schema 一致）
CREATE_TABLE_SQL = {
    'network_segment': '''
        CREATE TABLE IF NOT EXISTS network_segment (
            "segment_id" char(32) NOT NULL PRIMARY KEY,
            "layout_id" char(32) NOT NULL REFERENCES "layout"("layout_id") DEFERRABLE INITIALLY DEFERRED,
            "network_type" varchar(20) NOT NULL,
            "network_name" varchar(255) NOT NULL UNIQUE,
            "subnet" varchar(18) NOT NULL,
            "gateway" varchar(15) NOT NULL,
            "icc_enabled" integer NOT NULL,
            "create_date" datetime NOT NULL
        );
    ''',
    'service_network_access': '''
        CREATE TABLE IF NOT EXISTS service_network_access (
            "access_id" char(32) NOT NULL PRIMARY KEY,
            "service_id" char(32) NOT NULL REFERENCES "layout_service"("service_id") DEFERRABLE INITIALLY DEFERRED,
            "segment_id" char(32) NOT NULL REFERENCES "network_segment"("segment_id") DEFERRABLE INITIALLY DEFERRED,
            "ipv4_address" varchar(15) NOT NULL,
            "create_date" datetime NOT NULL
        );
    ''',
}


def connect_db():
    """连接 SQLite 数据库"""
    import sqlite3
    if not os.path.exists(DB_PATH):
        print(f"[DB] 数据库文件不存在: {DB_PATH}，跳过修复")
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def clean_migration_records(conn):
    """清理 4 个 app 在 django_migrations 表中的所有残留记录"""
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in APPS_TO_FIX)
    cursor.execute(
        f"SELECT app, name FROM django_migrations WHERE app IN ({placeholders})",
        APPS_TO_FIX
    )
    stale = cursor.fetchall()
    if stale:
        print(f"[迁移] 发现 {len(stale)} 条残留迁移记录，正在清理...")
        for app, name in stale:
            print(f"  删除: {app}.{name}")
        cursor.execute(
            f"DELETE FROM django_migrations WHERE app IN ({placeholders})",
            APPS_TO_FIX
        )
        conn.commit()
        print(f"[迁移] 清理完成，释放 {len(stale)} 条记录")
    else:
        print("[迁移] 未发现残留迁移记录，无需清理")


def create_missing_tables(conn):
    """创建缺失的数据库表（幂等：CREATE TABLE IF NOT EXISTS）"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row[0] for row in cursor.fetchall()}

    for table_name, ddl in CREATE_TABLE_SQL.items():
        if table_name in existing:
            print(f"[建表] {table_name} [OK] 已存在")
        else:
            cursor.execute(ddl)
            conn.commit()
            print(f"[建表] {table_name} [CREATED] 已创建")


def add_missing_columns(conn):
    """添加缺失的数据库列（幂等：检查列存在性）"""
    cursor = conn.cursor()

    # 检查 layout 表是否有 network_type 列
    cursor.execute("PRAGMA table_info(layout)")
    layout_cols = {row[1] for row in cursor.fetchall()}

    if 'network_type' not in layout_cols:
        cursor.execute(
            'ALTER TABLE layout ADD COLUMN "network_type" varchar(20) NOT NULL DEFAULT "legacy"'
        )
        conn.commit()
        print("[加列] layout.network_type [ADDED] 已添加")
    else:
        print("[加列] layout.network_type [OK] 已存在")


def run_migrate_fake_initial():
    """为 4 个 app 运行 migrate --fake-initial，标记迁移状态"""
    print("\n[迁移] 重新运行 migrate --fake-initial...")
    for app in APPS_TO_FIX:
        print(f"  >> {app} ...", end=' ')
        result = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, 'manage.py'), 'migrate', app, '--fake-initial', '--noinput'],
            capture_output=True, text=True, cwd=BASE_DIR
        )
        if result.returncode == 0:
            print("[OK] 完成")
        else:
            print(f"[FAIL] 失败 (rc={result.returncode})")
            # 尝试普通 migrate
            print(f"   尝试普通 migrate ...", end=' ')
            result2 = subprocess.run(
                [sys.executable, os.path.join(BASE_DIR, 'manage.py'), 'migrate', app, '--noinput'],
                capture_output=True, text=True, cwd=BASE_DIR
            )
            if result2.returncode == 0:
                print("[OK] 完成")
            else:
                print(f"[FAIL] 失败: {result2.stderr[:200]}")


def main():
    print("=" * 50)
    print("  Vulstudy 数据库迁移修复工具")
    print("=" * 50)

    conn = connect_db()
    if conn is None:
        return

    try:
        # 步骤 1：清理残留迁移记录
        clean_migration_records(conn)

        # 步骤 2：创建缺失的表
        create_missing_tables(conn)

        # 步骤 3：添加缺失的列
        add_missing_columns(conn)

        # 步骤 4：关闭数据库连接
        conn.close()

        # 步骤 5：运行 Django migrate --fake-initial
        run_migrate_fake_initial()

        print("\n" + "=" * 50)
        print("  [OK] 数据库迁移修复完成")
        print("=" * 50)
    except Exception as e:
        print(f"\n[错误] {e}")
        conn.close()
        sys.exit(1)


if __name__ == '__main__':
    main()
