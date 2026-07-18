"""Initial migration for network app"""
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NetWorkInfo',
            fields=[
                ('net_work_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='网卡UUID')),
                ('net_work_client_id', models.CharField(max_length=255, verbose_name='Dcoker网卡链接ID')),
                ('create_user', models.IntegerField(verbose_name='创建用户ID')),
                ('net_work_name', models.CharField(max_length=255, verbose_name='网卡名称')),
                ('net_work_subnet', models.CharField(max_length=255, verbose_name='子网')),
                ('net_work_gateway', models.CharField(max_length=255, verbose_name='网关')),
                ('net_work_scope', models.CharField(default='local', max_length=255, verbose_name='空间')),
                ('net_work_driver', models.CharField(default='bridge', max_length=255, verbose_name='驱动')),
                ('enable_ipv6', models.BooleanField(default=False, verbose_name='是否开启 IPv6')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'db_table': 'net_work_info',
            },
        ),
    ]
