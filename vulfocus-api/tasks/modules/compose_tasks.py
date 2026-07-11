from __future__ import absolute_import, unicode_literals
from celery import shared_task, chain
import json
import traceback
import uuid
import os
import random

from vulfocus.settings import client, REDIS_POOL, DOCKER_COMPOSE, VUL_IP
from dockerapi.models import ContainerVul, ImageInfo, SysLog, TimeMoudel
from dockerapi.serializers import ImageInfoSerializer
from dockerapi.common import R, get_setting_config, DEFAULT_CONFIG
from tasks.models import TaskInfo
from layout_image.bridge import get_project
from .container_tasks import create_run_container_task
import django.utils.timezone as timezone
import redis

r = redis.Redis(connection_pool=REDIS_POOL)


@shared_task(name="tasks.run_docker_compose")
def run_docker_compose(image_id, container_id, user_id, time_model_id, task_id, countdown):
    img_info = ImageInfo.objects.filter(image_id=image_id).first()
    if not img_info:
        return

    try:
        container_vul = ContainerVul.objects.filter(container_id=container_id).first()
        if not container_vul:
            return

        compose_path = os.path.join(DOCKER_COMPOSE, str(container_id))
        os.makedirs(compose_path, exist_ok=True)

        with open(os.path.join(compose_path, 'docker-compose.yml'), 'w') as f:
            f.write(img_info.docker_compose_yml)

        project = get_project(compose_path)
        containers = project.up()

        ports_info = {}
        for container in containers:
            container_vul_info = ContainerVul(
                image_id=img_info,
                user_id=user_id,
                vul_host="",
                container_status="running",
                docker_container_id=container.id,
                vul_port="",
                container_port="",
                time_model_id=time_model_id,
                docker_compose_path=compose_path,
                is_docker_compose_correlation=True,
                create_date=timezone.now()
            )
            container_vul_info.save()

            for port, bindings in container.ports.items():
                if bindings:
                    host_port = bindings[0]['HostPort']
                    ports_info[port] = host_port

        if VUL_IP:
            host_ip = VUL_IP
        else:
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                host_ip = s.getsockname()[0]
            finally:
                s.close()

        container_vul.docker_container_id = containers[0].id if containers else ""
        container_vul.vul_host = host_ip
        container_vul.container_status = "running"
        container_vul.docker_compose_path = compose_path
        container_vul.vul_port = json.dumps(ports_info)

        flag = str(uuid.uuid4()).replace("-", "")[:16]
        container_vul.container_flag = flag

        container_vul.save()

        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if task_info:
            task_info.task_msg = json.dumps(R.ok())
            task_info.task_status = 3
            task_info.update_date = timezone.now()
            task_info.save()

    except Exception as e:
        traceback.print_exc()
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if task_info:
            task_info.task_msg = json.dumps(R.err())
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()


@shared_task(name="tasks.stop_docker_compose")
def stop_docker_compose(task_id):
    try:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if not task_info:
            return

        operation_args = json.loads(task_info.operation_args)
        container_id = operation_args.get("container_id")

        container_vul = ContainerVul.objects.filter(container_id=container_id).first()
        if not container_vul:
            return

        compose_path = container_vul.docker_compose_path
        if compose_path and os.path.exists(compose_path):
            project = get_project(compose_path)
            project.stop()

        container_vul.container_status = "stop"
        container_vul.save()

        task_info.task_msg = json.dumps(R.ok())
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    except Exception as e:
        traceback.print_exc()
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if task_info:
            task_info.task_msg = json.dumps(R.err())
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()


@shared_task(name="tasks.delete_docker_compose")
def delete_docker_compose(task_id):
    try:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if not task_info:
            return

        operation_args = json.loads(task_info.operation_args)
        container_id = operation_args.get("container_id")

        container_vul = ContainerVul.objects.filter(container_id=container_id).first()
        if not container_vul:
            return

        compose_path = container_vul.docker_compose_path
        if compose_path and os.path.exists(compose_path):
            project = get_project(compose_path)
            project.stop()
            import shutil
            shutil.rmtree(compose_path)

        container_vul.container_status = "delete"
        container_vul.save()

        task_info.task_msg = json.dumps(R.ok())
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    except Exception as e:
        traceback.print_exc()
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if task_info:
            task_info.task_msg = json.dumps(R.err())
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()


def docker_container_run(docker_container, command):
    try:
        exec_result = docker_container.exec_run(command)
        if exec_result.exit_code != 0:
            return {"status": 500, "msg": str(exec_result.output)}
        return {"status": 200, "msg": str(exec_result.output)}
    except Exception as e:
        traceback.print_exc()
        return {"status": 500, "msg": str(e)}


def create_compose_task(user_info, image_info, tag, request_ip):
    user_id = user_info.id
    task_info = TaskInfo(
        task_name="构建镜像：" + tag,
        user_id=user_id,
        task_status=1,
        task_msg=json.dumps({}),
        task_start_date=timezone.now(),
        operation_type=1,
        operation_args=json.dumps({"image_name": image_info.image_name}),
        create_date=timezone.now(),
        update_date=timezone.now()
    )
    task_info.save()

    try:
        image_info.is_ok = True
        image_info.update_date = timezone.now()
        image_info.save()

        task_info.task_status = 3
        task_info.task_msg = json.dumps(R.ok(data="%s 构建成功" % tag))
        task_info.update_date = timezone.now()
        task_info.save()

        sys_log = SysLog(
            user_id=user_id, operation_type="镜像", operation_name="构建", ip=request_ip,
            operation_value=tag, operation_args=""
        )
        sys_log.save()

        return {"status": 200, "task_id": task_info.task_id}
    except Exception as e:
        traceback.print_exc()
        task_info.task_status = 4
        task_info.task_msg = json.dumps(R.err())
        task_info.update_date = timezone.now()
        task_info.save()
        return {"status": 500, "msg": str(e)}


def create_layout_image_download_task(layout_instance, user):
    pass


def start_docker_compose(request, image_id, container_vul, user_info, request_ip, time_model_id):
    image_info = container_vul.image_id
    user_id = user_info.id
    task_id = create_run_container_task(container_vul, user_info)

    if user_info.is_superuser or user_id == container_vul.user_id:
        operation_args = ImageInfoSerializer(image_info).data

        sys_log = SysLog(
            user_id=user_id, operation_type="容器", operation_name="启动", ip=request_ip,
            operation_value=operation_args["image_vul_name"], operation_args=json.dumps(operation_args)
        )
        sys_log.save()

        setting_config = get_setting_config()
        try:
            countdown = int(setting_config["time"])
        except Exception:
            countdown = int(DEFAULT_CONFIG["time"])

        if countdown == 0:
            run_docker_compose(image_id, container_vul.container_id, user_id, time_model_id, task_id, countdown)
        elif countdown != 0 and countdown > 60:
            setting_config = get_setting_config()
            if 'del_container' in setting_config:
                del_container = setting_config['del_container']
                if not del_container or del_container == 0 or del_container == '0':
                    add_chain_sig = chain(
                        run_docker_compose.s(image_id, container_vul.container_id, user_id, time_model_id, task_id, countdown) |
                        stop_docker_compose.s().set(countdown=countdown)
                    )
                else:
                    add_chain_sig = chain(
                        run_docker_compose.s(image_id, container_vul.container_id, user_id, time_model_id, task_id, countdown) |
                        stop_docker_compose.s().set(countdown=countdown)
                    )
                add_chain_sig.apply_async()
        else:
            task_info = TaskInfo.objects.filter(task_id=task_id).first()
            task_info.task_msg = json.dumps(R.build(msg="停止时间最小为 1 分钟"))
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()
    else:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        task_info.task_msg = json.dumps(R.build(msg="权限不足"))
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    return task_id