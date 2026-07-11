from __future__ import absolute_import, unicode_literals
from celery import shared_task
import json
import traceback
import time
import os

from vulfocus.settings import client, REDIS_POOL
from dockerapi.models import ImageInfo, SysLog
from dockerapi.serializers import ImageInfoSerializer
from dockerapi.common import R
from tasks.models import TaskInfo
import django.utils.timezone as timezone
import redis

r = redis.Redis(connection_pool=REDIS_POOL)


def create_create_image_task(image_info, user_info):
    user_id = user_info.id
    operation_args = {
        "image_name": image_info.image_name,
        "image_desc": image_info.image_desc,
        "image_vul_name": image_info.image_vul_name,
        "image_rank": image_info.rank,
        "image_port": image_info.image_port,
    }
    task_info = TaskInfo(
        task_name="拉取镜像：" + image_info.image_name,
        user_id=user_id,
        task_status=1,
        task_msg=json.dumps({}),
        task_start_date=timezone.now(),
        operation_type=1,
        operation_args=json.dumps(operation_args),
        create_date=timezone.now(),
        update_date=timezone.now()
    )
    task_info.save()
    return task_info.task_id


@shared_task(name="tasks.create_image")
def create_image(task_id):
    """
    拉取镜像
    """
    task_info = TaskInfo.objects.filter(task_id=task_id).first()
    if not task_info:
        return

    try:
        operation_args = json.loads(task_info.operation_args)
        image_name = operation_args.get("image_name", "")

        if not image_name:
            task_info.task_msg = json.dumps(R.build(msg="镜像名称不能为空"))
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()
            return

        try:
            image = client.images.get(image_name)
            progress_info = {
                "total": 1,
                "progress_count": 1,
                "progress": round(100.00, 2),
            }
            r.set(str(task_id), json.dumps(progress_info, ensure_ascii=False))
            time.sleep(0.5)
        except Exception:
            for line in client.api.pull(image_name, stream=True, decode=True):
                if "progressDetail" in line:
                    progress_info = {
                        "total": line["progressDetail"].get("total", 0),
                        "progress_count": line["progressDetail"].get("current", 0),
                        "progress": round(
                            (line["progressDetail"].get("current", 0) / line["progressDetail"].get("total", 1)) * 100,
                            2
                        ),
                    }
                    r.set(str(task_id), json.dumps(progress_info, ensure_ascii=False))

        image_info = ImageInfo.objects.filter(image_name=image_name).first()
        if image_info:
            image_info.is_ok = True
            image_info.update_date = timezone.now()
            image_info.save()

        task_info.task_msg = json.dumps(R.ok(data="%s 拉取成功" % image_name))
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    except Exception as e:
        traceback.print_exc()
        task_info.task_msg = json.dumps(R.err())
        task_info.task_status = 4
        task_info.update_date = timezone.now()
        task_info.save()


def create_image_task(image_info, user_info, request_ip, image_file=None):
    """
    创建镜像任务
    """
    user_id = user_info.id
    task_id = create_create_image_task(image_info=image_info, user_info=user_info)

    if user_info.is_superuser:
        image_name = image_info.image_name
        image_desc = image_info.image_desc
        image_vul_name = image_info.image_vul_name
        image_rank = image_info.rank
        task_info = TaskInfo.objects.filter(task_id=task_id).first()

        if image_file:
            task_msg = {}
            try:
                file_info = image_file.read()
                images = client.images.load(file_info)
                image = images[0]
                repo_tags = image.attrs["RepoTags"]

                if len(repo_tags) == 0:
                    try:
                        client.images.remove(image.id)
                    except Exception:
                        pass
                    task_msg = R.build(msg="文件镜像 Tag 不能为空")
                else:
                    config = image.attrs["ContainerConfig"]
                    port_list = []
                    if "ExposedPorts" in config:
                        port_list = config["ExposedPorts"]
                    else:
                        port_list = image.attrs['Config']['ExposedPorts']

                    ports = []
                    for port in port_list:
                        port = port.replace("/", "").replace("tcp", "").replace("udp", "")
                        ports.append(port)

                    image_name = repo_tags[0]
                    image_port = ",".join(ports)
                    image_info = ImageInfo.objects.filter(image_name=image_name).first()

                    if not image_info:
                        image_info = ImageInfo()

                    image_info.image_name = image_name
                    image_info.image_port = image_port
                    image_info.image_vul_name = image_name.replace("vulfocus/", "") if not image_vul_name else image_vul_name
                    image_info.image_desc = image_name.replace("vulfocus/", "") if not image_desc else image_desc
                    image_info.rank = 2.5 if image_rank > 5 or image_rank < 0.5 else image_rank
                    image_info.is_ok = True
                    image_info.save()

                    task_info.task_name = "拉取镜像：" + image_name
                    task_info.task_status = 3
                    task_msg = R.ok(data="%s 添加成功" % image_name)

            except Exception as e:
                traceback.print_exc()
                task_msg = R.err()
                try:
                    image_info.delete()
                except Exception:
                    pass
                task_info.task_status = 4
            finally:
                task_info.task_msg = json.dumps(task_msg)
                task_info.update_date = timezone.now()
                task_info.save()

        elif image_name:
            create_image.delay(task_id)
        else:
            R.build(msg="镜像文件或镜像名称不能为空")

        operation_args = ImageInfoSerializer(image_info).data
        sys_log = SysLog(
            user_id=user_id, operation_type="镜像", operation_name="创建", ip=request_ip,
            operation_value=operation_args["image_vul_name"], operation_args=json.dumps(operation_args)
        )
        sys_log.save()
    else:
        task_info = TaskInfo.objects.filter(task_id=task_id).first()
        task_info.task_msg = json.dumps(R.build(msg="权限不足"))
        task_info.task_status = 3
        task_info.update_date = timezone.now()
        task_info.save()

    return task_id


@shared_task(name="tasks.synchronous_image")
def synchronous_image():
    """
    同步镜像
    """
    try:
        image_infos = ImageInfo.objects.filter(is_ok=False)
        for image_info in image_infos:
            try:
                client.images.get(image_info.image_name)
                image_info.is_ok = True
                image_info.update_date = timezone.now()
                image_info.save()
            except Exception:
                pass
    except Exception as e:
        traceback.print_exc()


@shared_task(name="tasks.update_images")
def update_images():
    """
    更新镜像信息
    """
    try:
        image_infos = ImageInfo.objects.all()
        for image_info in image_infos:
            try:
                image = client.images.get(image_info.image_name)
                image_info.image_size = image.attrs.get("Size", 0)
                image_info.update_date = timezone.now()
                image_info.save()
            except Exception:
                pass
    except Exception as e:
        traceback.print_exc()


@shared_task(name="tasks.check_images")
def check_images():
    """
    检查镜像状态
    """
    try:
        image_infos = ImageInfo.objects.all()
        for image_info in image_infos:
            try:
                client.images.get(image_info.image_name)
                image_info.is_ok = True
            except Exception:
                image_info.is_ok = False
            image_info.update_date = timezone.now()
            image_info.save()
    except Exception as e:
        traceback.print_exc()


@shared_task(name="tasks.download_images")
def download_images():
    """
    下载镜像
    """
    try:
        image_infos = ImageInfo.objects.filter(is_ok=False)
        for image_info in image_infos:
            try:
                task_info = TaskInfo(
                    task_name="拉取镜像：" + image_info.image_name,
                    user_id=0,
                    task_status=1,
                    task_msg=json.dumps({}),
                    task_start_date=timezone.now(),
                    operation_type=1,
                    operation_args=json.dumps({"image_name": image_info.image_name}),
                    create_date=timezone.now(),
                    update_date=timezone.now()
                )
                task_info.save()
                create_image.delay(task_info.task_id)
            except Exception:
                pass
    except Exception as e:
        traceback.print_exc()


@shared_task(name="tasks.duplicate")
def duplicate():
    """
    检查重复容器
    """
    try:
        pass
    except Exception as e:
        traceback.print_exc()