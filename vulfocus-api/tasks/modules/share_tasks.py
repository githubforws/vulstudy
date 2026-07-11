from __future__ import absolute_import, unicode_literals
from celery import shared_task
import json
import traceback

from vulfocus.settings import client, REDIS_POOL
from dockerapi.models import ImageInfo, SysLog
from dockerapi.serializers import ImageInfoSerializer
from dockerapi.common import R, get_setting_config, DEFAULT_CONFIG
from tasks.models import TaskInfo
import django.utils.timezone as timezone
import redis
import requests

r = redis.Redis(connection_pool=REDIS_POOL)


def create_share_image_task(image_info, user_info):
    setting_config = get_setting_config()
    user_id = user_info.id
    operation_args = {
        "share_username": setting_config["share_username"],
        "image_name": image_info.image_name,
        "username": setting_config["username"],
        "pwd": setting_config["pwd"]
    }
    task_info = TaskInfo(
        task_name="分享镜像：" + image_info.image_name,
        user_id=user_id,
        task_status=1,
        task_msg=json.dumps({}),
        task_start_date=timezone.now(),
        operation_type=5,
        operation_args=json.dumps(operation_args),
        create_date=timezone.now(),
        update_date=timezone.now()
    )
    task_info.save()
    return task_info.task_id


@shared_task(name="tasks.share_image")
def share_image(task_id):
    """
    分享镜像到官方库
    """
    task_info = TaskInfo.objects.filter(task_id=task_id).first()
    if not task_info:
        return

    try:
        operation_args = json.loads(task_info.operation_args)
        share_username = operation_args.get("share_username", "")
        image_name = operation_args.get("image_name", "")
        username = operation_args.get("username", "")
        pwd = operation_args.get("pwd", "")

        if not image_name or not share_username or not username or not pwd:
            task_info.task_msg = json.dumps(R.build(msg="参数不完整"))
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()
            return

        new_image_name = share_username + "/" + image_name.split("/")[-1]

        try:
            image = client.images.get(image_name)
            image.tag(new_image_name)

            headers = {
                "Content-Type": "application/json",
            }
            data = {
                "username": username,
                "password": pwd
            }
            response = requests.post(
                "https://hub.docker.com/v2/users/login/",
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )

            if response.status_code == 200:
                token = response.json().get("token", "")
                auth_config = {"username": username, "password": pwd}

                for line in client.api.push(new_image_name, stream=True, decode=True, auth_config=auth_config):
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

                task_info.task_msg = json.dumps(R.ok(data="%s 分享成功" % new_image_name))
                task_info.task_status = 3
                task_info.update_date = timezone.now()
                task_info.save()
            else:
                task_info.task_msg = json.dumps(R.build(msg="Docker Hub 登录失败"))
                task_info.task_status = 4
                task_info.update_date = timezone.now()
                task_info.save()

        except Exception as e:
            traceback.print_exc()
            task_info.task_msg = json.dumps(R.build(msg="分享失败: " + str(e)))
            task_info.task_status = 4
            task_info.update_date = timezone.now()
            task_info.save()

    except Exception as e:
        traceback.print_exc()
        task_info.task_msg = json.dumps(R.err())
        task_info.task_status = 4
        task_info.update_date = timezone.now()
        task_info.save()


def share_image_task(image_info, user_info, request_ip):
    """
    共享镜像
    """
    task_id = create_share_image_task(image_info=image_info, user_info=user_info)
    operation_args = ImageInfoSerializer(image_info).data

    sys_log = SysLog(
        user_id=user_info.id, operation_type="镜像", operation_name="分享", ip=request_ip,
        operation_value=operation_args["image_vul_name"], operation_args=json.dumps(operation_args)
    )
    sys_log.save()

    share_image.delay(task_id)
    return task_id