# Generated manually - complete schema for layout_image app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dockerapi', '0001_initial'),
        ('network', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Layout',
            fields=[
                ('layout_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='编排UUID')),
                ('layout_name', models.CharField(max_length=255, verbose_name='环境名称')),
                ('layout_desc', models.TextField(null=True, verbose_name='描述')),
                ('image_name', models.TextField(default='', verbose_name='图片名称')),
                ('create_user_id', models.IntegerField(verbose_name='用户ID')),
                ('is_release', models.BooleanField(default=False, verbose_name='是否发布，默认否')),
                ('raw_content', models.TextField(default='', verbose_name='原json内容')),
                ('yml_content', models.TextField(verbose_name='编排内容')),
                ('env_content', models.TextField(verbose_name='环境变量')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_uesful', models.BooleanField(default=True, verbose_name='编排环境是否可用')),
                ('total_view', models.IntegerField(default=0, verbose_name='查看数')),
                ('download_num', models.IntegerField(default=0, verbose_name='下载数')),
                ('network_type', models.CharField(choices=[('legacy', '旧版单网络'), ('multi', '多网络隔离')], default='legacy', max_length=20, verbose_name='网络模式')),
            ],
            options={
                'db_table': 'layout',
            },
        ),
        migrations.CreateModel(
            name='LayoutData',
            fields=[
                ('layout_user_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_user_id', models.IntegerField(verbose_name='用户ID')),
                ('status', models.CharField(max_length=255, verbose_name='状态信息')),
                ('file_path', models.TextField(default='', verbose_name='启动目录')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('layout_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layout', verbose_name='编排 ID')),
            ],
            options={
                'db_table': 'layout_data',
            },
        ),
        migrations.CreateModel(
            name='LayoutService',
            fields=[
                ('service_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_name', models.TextField(default='', verbose_name='服务环境名称')),
                ('is_exposed', models.BooleanField(editable=False, verbose_name='是否暴露')),
                ('exposed_source_port', models.CharField(max_length=255, verbose_name='暴露原端口')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('image_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dockerapi.imageinfo', verbose_name='镜像ID')),
                ('layout_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layout', verbose_name='编排 ID')),
            ],
            options={
                'db_table': 'layout_service',
            },
        ),
        migrations.CreateModel(
            name='NetworkSegment',
            fields=[
                ('segment_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='网段UUID')),
                ('network_type', models.CharField(choices=[('dmz', 'DMZ'), ('internal', '内网')], max_length=20, verbose_name='网络类型')),
                ('network_name', models.CharField(max_length=255, unique=True, verbose_name='Docker网络名称')),
                ('subnet', models.CharField(blank=True, default='', max_length=18, verbose_name='子网')),
                ('gateway', models.CharField(blank=True, default='', max_length=15, verbose_name='网关')),
                ('icc_enabled', models.BooleanField(default=False, verbose_name='是否启用容器间通信')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('layout', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layout', verbose_name='编排ID')),
            ],
            options={
                'db_table': 'network_segment',
            },
        ),
        migrations.CreateModel(
            name='ServiceNetworkAccess',
            fields=[
                ('access_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='接入ID')),
                ('ipv4_address', models.CharField(blank=True, default='', max_length=15, verbose_name='固定IPv4地址')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('segment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.networksegment', verbose_name='网络段')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layoutservice', verbose_name='服务')),
            ],
            options={
                'db_table': 'service_network_access',
            },
        ),
        migrations.CreateModel(
            name='LayoutServiceNetwork',
            fields=[
                ('layout_service_network_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('network_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='network.networkinfo', verbose_name='网卡名称')),
                ('service_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layoutservice', verbose_name='服务ID')),
            ],
            options={
                'db_table': 'layout_service_network',
            },
        ),
        migrations.CreateModel(
            name='LayoutServiceContainer',
            fields=[
                ('service_container_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(verbose_name='用户ID')),
                ('docker_container_id', models.CharField(max_length=255, verbose_name='Docker容器运行ID')),
                ('container_host', models.CharField(max_length=255, verbose_name='容器漏洞URL')),
                ('container_status', models.CharField(max_length=255, verbose_name='容器当前状态')),
                ('container_port', models.CharField(max_length=255, verbose_name='容器端口')),
                ('container_flag', models.CharField(max_length=255, verbose_name='flag')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='容器创建时间，默认为当前时间')),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('image_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dockerapi.imageinfo', verbose_name='镜像ID')),
                ('layout_user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layoutdata', verbose_name='编排环境运行信息')),
                ('service_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layoutservice', verbose_name='服务ID')),
            ],
            options={
                'db_table': 'layout_service_container',
            },
        ),
        migrations.CreateModel(
            name='LayoutServiceContainerScore',
            fields=[
                ('layout_service_container_score_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(verbose_name='用户ID')),
                ('flag', models.CharField(max_length=255, verbose_name='flag')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间，默认为当前时间')),
                ('update_date', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('image_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='dockerapi.imageinfo', verbose_name='镜像ID')),
                ('layout_data_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layoutdata', verbose_name='编排 ID')),
                ('layout_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layout', verbose_name='编排 ID')),
                ('service_container_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='layout_image.layoutservicecontainer', verbose_name='编排 ID')),
                ('service_id', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='layout_image.layoutservice', verbose_name='服务ID')),
            ],
            options={
                'db_table': 'layout_service_container_score',
            },
        ),
        migrations.CreateModel(
            name='SceneUserFav',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scene_id', models.CharField(max_length=255, verbose_name='场景id')),
                ('add_time', models.DateTimeField(auto_now_add=True, verbose_name='添加时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, verbose_name='点赞用户')),
            ],
            options={
                'db_table': 'layout_user_fav',
            },
        ),
    ]
