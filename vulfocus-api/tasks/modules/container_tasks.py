from __future__ import absolute_import, unicode_literals
from celery import shared_task, chain
import json
import time
import random
import socket

from vulfocus.settings import client, api_docker_client, DOCKER_CONTAINER_TIME, VUL_IP, REDIS_POOL
from dockerapi.models import ContainerVul, ImageInfo, SysLog
from dockerapi.serializers import ContainerVulSerializer, ImageInfoSerializer
from dockerapi.common import R, get_setting_config, DEFAULT_CONFIG
from tasks.models import TaskInfo
import django.utils.timezone as timezone
import redis

r = redis.Redis(connection_pool=REDIS_POOL)


def create_run_container_task(container_vul, user_info):
    user_id = user_info.id
    operation_args = {
        "image_name": container_vul.image_id.image_name,
        "user_id": user_id,
        "image_port": container_vul.image_id.image_port,
    }
    task_info = TaskInfo(
        task_name="启动容器：" + container_vul.image_id.image_name,
        user_id=user_id,
        task_status=1,
        task_msg=json.dumps({}),
        task_start_date=timezone.now(),
        operation_type=2,
        operation_args=json.dumps(operation_args),
        create_date=timezone.now(),
        update_date=timezone.now()
    )
    task_info.save()
    return task_info.task_id


def create_stop_container_task(container_vul, user_info):
    user_id = user_info.id
    operation_args = {
        "container_id": str(container_vul.container_id),
        "user_id": user_id,
        "image_id": str(container_vul.image_id.image_id),
    }
    task_info = TaskInfo(
        task_name="停止容器：" + container_vul.image_id.image_name,
        user_id=user_id,
        task_status=1,
        task_msg=json.dumps({}),
        task_start_date=timezone.now(),
        operation_type=3,
        operation_args=json.dumps(operation_args),
        create_date=timezone.now(),
        update_date=timezone.now()
    )
    task_info.save()
    return task_info.task_id


def create_delete_container_task(container_vul, user_info):
    user_id = user_info.id
    operation_args = {
        "container_id": str(container_vul.container_id),
        "user_id": user_id,
        "image_id": str(container_vul.image_id.image_id),
    }
    task_info = TaskInfo(
        task_name="删除容器：" + container_vul.image_id.image_name,
        user_id=user_id,
        task_status=1,
        task_msg=json.dumps({}),
        task_start_date=timezone.now(),
        operation_type=4,
        operation_args=json.dumps(operation_args),
        create_date=timezone.now(),
        update_date=timezone.now()
    )
    task_info.save()
    return task_info.task_id


@shared_task(name="tasks.run_container")
def run_container(container_id, user_id, task_id, countdown):
    try:
        container_vul = ContainerVul.objects.filter(container_id=container_id).first()
        if not container_vul:
            return

        image_info = container_vul.image_id
        image_name = image_info.image_name
        image_port = image_info.image_port

        try:
            container = client.containers.get(container_vul.docker_container_id)
            container.start()
        except Exception:
            ports = {}
            if image_port:
                try:
                    image_port_list = json.loads(image_port)
                    if isinstance(image_port_list, list):
                        for port in image_port_list:
                            ports[str(port) + "/tcp"] = random.randint(10000, 65535)
                    else:
                        ports[str(image_port) + "/tcp"] = random.randint(10000, 65535)
                except Exception:
                    ports[str(image_port) + "/tcp"] = random.randint(10000, 65535)

            container = client.containers.run(
                image_name,
                detach=True,
                ports=ports,
                name="vulfocus_" + str(container_id)[:8],
                remove=True
            )

            container_vul.docker_container_id = container.id
            container_vul.container_port = str(container.attrs.get('Config', {}).get('ExposedPorts', {}))
            container_vul.vul_port = str(container.attrs.get('NetworkSettings', {}).get('Ports', {}))

            if VUL_IP:
                host_ip = VUL_IP
            else:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(('8.8.8.8', 80))
                    host_ip = s.getsockname()[0]
                finally:
                    s.close()

            container_vul.vul_host = host_ip
            container_vul.container_status = "running"

            flag = str(uuid.uuid4()).replace("-", "")[:16]
            container_vul.container_flag = flag

            container_vul.save()

        start_date = int(time.time())
        end_date = start_date + countdown

        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if task_info:
            task_info.task_msg = json.dumps(R.ok(data={"start_date": start_date, "end_date": end_date}))
            task_info.task_status = 3
            task_info.update_date = timezone.now()
            task_info.save()

    except Exception as e:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if task_info:
            task_info.task_msg = json.dumps(R.err())
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()


@shared_task(name="tasks.stop_container")
def stop_container(task_id):
    try:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if not task_info:
            return

        operation_args = json.loads(task_info.operation_args)
        container_id = operation_args.get("container_id")

        container_vul = ContainerVul.objects.filter(container_id=container_id).first()
        if not container_vul:
            return

        try:
            container = client.containers.get(container_vul.docker_container_id)
            container.stop()
        except Exception:
            pass

        container_vul.container_status = "stop"
        container_vul.save()

        task_info.task_msg = json.dumps(R.ok())
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    except Exception as e:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if task_info:
            task_info.task_msg = json.dumps(R.err())
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()


@shared_task(name="tasks.delete_container")
def delete_container(task_id):
    try:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if not task_info:
            return

        operation_args = json.loads(task_info.operation_args)
        container_id = operation_args.get("container_id")

        container_vul = ContainerVul.objects.filter(container_id=container_id).first()
        if not container_vul:
            return

        try:
            container = client.containers.get(container_vul.docker_container_id)
            container.remove()
        except Exception:
            pass

        container_vul.container_status = "delete"
        container_vul.save()

        task_info.task_msg = json.dumps(R.ok())
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    except Exception as e:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        if task_info:
            task_info.task_msg = json.dumps(R.err())
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()


def create_container_task(container_vul, user_info, request_ip):
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
            run_container.delay(container_vul.container_id, user_id, task_id, countdown)
        elif countdown != 0 and countdown > 60:
            setting_config = get_setting_config()
            if 'del_container' in setting_config:
                del_container = setting_config['del_container']
                if not del_container or del_container == 0 or del_container == '0':
                    add_chain_sig = chain(
                        run_container.s(container_vul.container_id, user_id, task_id, countdown) |
                        stop_container.s().set(countdown=countdown)
                    )
                else:
                    add_chain_sig = chain(
                        run_container.s(container_vul.container_id, user_id, task_id, countdown) |
                        delete_container.s().set(countdown=countdown)
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


def stop_container_task(container_vul, user_info, request_ip):
    user_id = user_info.id
    task_id = create_stop_container_task(container_vul=container_vul, user_info=user_info)

    if user_info.is_superuser or user_id == container_vul.user_id:
        operation_args = ContainerVulSerializer(container_vul).data
        img_info = ImageInfo.objects.filter(image_id=operation_args['image_id']).first()

        sys_log = SysLog(
            user_id=user_id, operation_type="容器", operation_name="停止", ip=request_ip,
            operation_value=operation_args["vul_name"], operation_args=json.dumps(operation_args)
        )
        sys_log.save()

        if img_info.is_docker_compose:
            stop_docker_compose.delay(task_id)
        else:
            stop_container.delay(task_id)
    else:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        task_info.task_msg = json.dumps(R.build(msg="权限不足"))
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    return task_id


def delete_container_task(container_vul, user_info, request_ip):
    user_id = user_info.id
    task_id = create_delete_container_task(container_vul=container_vul, user_info=user_info)

    if user_info.is_superuser or user_id == container_vul.user_id:
        operation_args = ContainerVulSerializer(container_vul).data
        img_info = ImageInfo.objects.filter(image_id=operation_args['image_id']).first()

        sys_log = SysLog(
            user_id=user_id, operation_type="容器", operation_name="删除", ip=request_ip,
            operation_value=operation_args["vul_name"], operation_args=json.dumps(operation_args)
        )
        sys_log.save()

        if img_info.is_docker_compose:
            delete_docker_compose.delay(task_id)
        else:
            delete_container.delay(task_id)
    else:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        task_info.task_msg = json.dumps(R.build(msg="权限不足"))
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    return task_id