"""Complete initial migration for dockerapi app"""

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ImageInfo',
            fields=[
                ('image_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('image_name', models.CharField(max_length=256, unique=True, verbose_name='Docker镜像名称')),
                ('image_vul_name', models.CharField(max_length=256, verbose_name='漏洞名称')),
                ('image_port', models.CharField(default='', max_length=256, null=True, verbose_name='暴露端口')),
                ('image_desc', models.TextField(null=True, verbose_name='镜像描述')),
                ('rank', models.FloatField(default=2.5, verbose_name='Rank')),
                ('is_ok', models.BooleanField(default=True, verbose_name='镜像是否可用')),
                ('is_share', models.BooleanField(default=False, verbose_name='镜像是否贡献')),
                ('degree', models.TextField(blank=True, default='', verbose_name='漏洞类型')),
                ('writeup_date', models.TextField(default='', verbose_name='writeup')),
                ('is_flag', models.BooleanField(default=True, verbose_name='是否展示flag输入框')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Docker创建时间')),
                ('update_date', models.DateTimeField(auto_now_add=True, verbose_name='Docker更新时间')),
                ('is_docker_compose', models.BooleanField(default=False, verbose_name='镜像启动方式')),
                ('docker_compose_yml', models.TextField(default='', verbose_name='compose_yml')),
                ('docker_compose_env', models.TextField(default='', verbose_name='env_port')),
                ('compose_env_port', models.TextField(default='', verbose_name='env对应端口')),
                ('original_yml', models.TextField(default='', verbose_name='原生yml文件')),
                ('image_size', models.IntegerField(default=0, verbose_name='镜像大小')),
            ],
            options={
                'db_table': 'image_info',
            },
        ),
        migrations.CreateModel(
            name='SysLog',
            fields=[
                ('log_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(verbose_name='使用用户ID')),
                ('operation_type', models.CharField(max_length=255, verbose_name='操作类型')),
                ('operation_name', models.CharField(max_length=255, verbose_name='操作名称')),
                ('operation_value', models.CharField(max_length=255, verbose_name='操作内容')),
                ('operation_args', models.TextField(default='', null=True, verbose_name='参数')),
                ('ip', models.CharField(max_length=255, verbose_name='IP地址')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'db_table': 'sys_log',
            },
        ),
        migrations.CreateModel(
            name='SysConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config_key', models.CharField(max_length=255, unique=True, verbose_name='配置名称对应key')),
                ('config_value', models.TextField(default='', null=True, verbose_name='对应值')),
            ],
            options={
                'db_table': 'sys_config',
            },
        ),
        migrations.CreateModel(
            name='TimeTemp',
            fields=[
                ('temp_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(default='', max_length=256, verbose_name='模版名称')),
                ('user_id', models.IntegerField(verbose_name='用户ID')),
                ('time_range', models.IntegerField(verbose_name='计时模式时间')),
                ('image_name', models.TextField(default='', verbose_name='图片名称')),
                ('time_desc', models.TextField(null=True, verbose_name='计时模版描述')),
                ('time_img_type', models.TextField(default='', verbose_name='漏洞类型')),
                ('rank_range', models.TextField(default='', verbose_name='Rank范围')),
                ('flag_status', models.BooleanField(default=False, verbose_name='用于判断')),
                ('image_ids', models.TextField(default='', verbose_name='镜像id')),
                ('template_pattern', models.IntegerField(default=1, verbose_name='计时模式分类')),
                ('total_view', models.IntegerField(default=0, verbose_name='查看数')),
            ],
            options={
                'db_table': 'time_temp',
            },
        ),
        migrations.CreateModel(
            name='TimeRank',
            fields=[
                ('rank_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('user_id', models.IntegerField(verbose_name='用户ID')),
                ('user_name', models.CharField(max_length=256, verbose_name='用户名称')),
                ('rank', models.FloatField(verbose_name='Rank')),
                ('time_temp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dockerapi.timetemp')),
            ],
            options={
                'db_table': 'time_rank',
            },
        ),
        migrations.CreateModel(
            name='TimeMoudel',
            fields=[
                ('time_id', models.CharField(default=str(uuid.uuid4()), max_length=255, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(verbose_name='用户ID')),
                ('start_time', models.FloatField(verbose_name='开始时间戳')),
                ('end_time', models.FloatField(verbose_name='结束时间')),
                ('status', models.BooleanField(default=False, verbose_name='用于判断')),
                ('temp_time_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dockerapi.timetemp')),
            ],
            options={
                'db_table': 'time_moudel',
            },
        ),
        migrations.CreateModel(
            name='ContainerVul',
            fields=[
                ('container_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='漏洞容器创建ID')),
                ('docker_container_id', models.CharField(max_length=255, verbose_name='Docker容器运行进ID')),
                ('user_id', models.IntegerField(verbose_name='用户ID')),
                ('vul_host', models.CharField(max_length=255, verbose_name='容器漏洞URL')),
                ('container_status', models.CharField(max_length=255, verbose_name='容器当前状态')),
                ('container_port', models.CharField(max_length=255, verbose_name='容器端口')),
                ('vul_port', models.TextField(default='', verbose_name='容器对应端口')),
                ('container_flag', models.CharField(max_length=255, verbose_name='flag')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='容器创建时间')),
                ('is_check', models.BooleanField(default=False, verbose_name='Flag是否通过')),
                ('is_check_date', models.DateTimeField(null=True, verbose_name='Flag提交时间')),
                ('time_model_id', models.CharField(max_length=255, verbose_name='时间模式 ID')),
                ('docker_compose_path', models.TextField(default='', verbose_name='docker_compose_path')),
                ('is_docker_compose_correlation', models.BooleanField(default=False, verbose_name='docker-compose相关辅助镜像')),
                ('image_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dockerapi.imageinfo', verbose_name='镜像ID')),
            ],
            options={
                'db_table': 'container_vul',
            },
        ),
    ]
