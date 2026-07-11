import json
import re

from django.http import JsonResponse
from django.db import transaction
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt

from dockerapi.models import SysConfig, ImageInfo, ContainerVul
from dockerapi.serializers import ImageInfoSerializer
from tasks.modules.image_tasks import synchronous_image
from .common import R, DEFAULT_CONFIG, get_setting_config, get_version_config


@api_view(http_method_names=["GET"])
def get_writeup_info(request):
    image_id = request.GET.get("id", "")
    writeup_date = ""
    
    if image_id:
        img_info = ImageInfo.objects.filter(image_id=image_id).first()
        if img_info:
            if img_info.writeup_date:
                writeup_date = json.loads(img_info.writeup_date)
            else:
                writeup_date = ""
    
    return JsonResponse({'code': 200, 'data': {"username": '', "writeup_date": writeup_date}})


@api_view(http_method_names=["GET"])
def get_setting(request):
    user = request.user
    if not user.is_superuser:
        return JsonResponse(R.build(msg="权限不足"))
    
    rsp_data = get_setting_config()
    return JsonResponse(R.ok(data=rsp_data))


@api_view(http_method_names=["GET"])
@authentication_classes([])
@permission_classes([])
def get_version(request):
    rsp_data = get_version_config()
    return JsonResponse(R.ok(data=rsp_data))


@api_view(http_method_names=["POST"])
def update_setting(request):
    user = request.user
    if not user.is_superuser:
        return JsonResponse(R.build(msg="权限不足"))
    
    username = request.POST.get("username")
    if not username:
        return JsonResponse(R.build(msg="用户名不能为空"))
    
    pwd = request.POST.get("pwd", DEFAULT_CONFIG["pwd"])
    if not pwd:
        return JsonResponse(R.build(msg="密码不能为空"))
    
    time = request.POST.get("time")
    share_username = request.POST.get("share_username")
    
    if not share_username:
        return JsonResponse(R.build(msg="分享用户名不能为空"))
    else:
        share_username_reg = "[\da-zA-z\-]+"
        if not re.match(share_username_reg, share_username):
            return JsonResponse(R.build(msg="分享用户名不符合要求"))
    
    is_synchronization = request.POST.get("is_synchronization")
    cancel_validation = request.POST.get("cancel_validation")
    cancel_registration = request.POST.get("cancel_registration")
    del_container = request.POST.get("del_container")
    url_name = request.POST.get("url_name")
    
    if not url_name:
        url_name = 'vulfocus'
    
    is_synchronization = 1 if is_synchronization and 'true' == is_synchronization else 0
    del_container = 1 if del_container and 'true' == del_container else 0
    cancel_validation = 1 if cancel_validation and 'true' == cancel_validation else 0
    cancel_registration = 1 if cancel_registration and 'true' == cancel_registration else 0
    
    try:
        time = int(time)
        if time != 0 and time < 60:
            time = int(DEFAULT_CONFIG["time"])
    except:
        time = int(DEFAULT_CONFIG["time"])
    
    configs = [
        ("share_username", share_username),
        ("username", username),
        ("pwd", pwd),
        ("time", str(time)),
        ("is_synchronization", str(is_synchronization)),
        ("del_container", str(del_container)),
        ("url_name", str(url_name)),
        ("cancel_validation", str(cancel_validation)),
        ("cancel_registration", str(cancel_registration)),
    ]
    
    with transaction.atomic():
        for config_key, config_value in configs:
            config = SysConfig.objects.filter(config_key=config_key).first()
            if not config:
                config = SysConfig(config_key=config_key, config_value=DEFAULT_CONFIG.get(config_key, ""))
                config.save()
            else:
                if config.config_value != str(config_value):
                    config.config_value = str(config_value)
                    config.save()
    
    rsp_data = get_setting_config()
    return JsonResponse(R.ok(msg="修改成功", data=rsp_data))


@api_view(http_method_names=["POST"])
def get_timing_imgs(request):
    synchronous_image.delay()
    return JsonResponse({"code": 200, "data": "镜像同步中"})


@api_view(http_method_names=["POST"])
def update_enterprise_setting(request):
    user = request.user
    if not user.is_superuser:
        return JsonResponse(R.build(msg="权限不足"))
    
    url_name = request.POST.get("url_name")
    enterprise_bg = request.POST.get("enterprise_bg", "")
    enterprise_logo = request.POST.get("enterprise_logo", "")
    
    if not url_name:
        url_name = 'vulfocus'
    
    try:
        with transaction.atomic():
            for config_key, config_value in [
                ("url_name", str(url_name)),
                ("enterprise_bg", str(enterprise_bg)),
                ("enterprise_logo", str(enterprise_logo)),
            ]:
                config = SysConfig.objects.filter(config_key=config_key).first()
                if not config:
                    config = SysConfig(config_key=config_key, config_value=DEFAULT_CONFIG.get(config_key, ""))
                    config.save()
                else:
                    if config.config_value != str(config_value):
                        config.config_value = str(config_value)
                        config.save()
    except:
        return JsonResponse(R.build('修改失败'))
    
    rsp_data = get_setting_config()
    return JsonResponse(R.ok(msg="修改成功", data=rsp_data))


@csrf_exempt
def get_url_name(req):
    if req.method == "GET":
        configs = get_setting_config()
        try:
            url_name = configs['url_name']
        except:
            url_name = "vulfocus"
        return JsonResponse(url_name, safe=False)


@api_view(http_method_names=["GET"])
@permission_classes([AllowAny])
def get_setting_img(req):
    if req.method == "GET":
        configs = get_setting_config()
        return JsonResponse({"code": 200, "data": configs})


@api_view(http_method_names=["GET"])
def get_container_status(request):
    if request.method == "GET":
        container_id = request.GET.get("container_id", "")
        container_vul = ContainerVul.objects.filter(container_id=container_id).first()
        if container_vul:
            return JsonResponse({"code": 200, "data": container_vul.container_status})
        else:
            return JsonResponse({"code": 200, "data": "stop"})


@api_view(http_method_names=["GET"])
def get_operation_image_api(req):
    if req.method == "GET":
        image_name = req.GET.get("image_name", "")
        image_info = ImageInfo.objects.filter(image_name=image_name).first()
        if image_info:
            return JsonResponse({"code": 200, "data": ImageInfoSerializer(image_info).data})
        else:
            return JsonResponse({"code": 200, "data": ""})