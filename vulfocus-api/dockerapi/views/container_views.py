import datetime
import json

from django.http import JsonResponse
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action

from dockerapi.models import ContainerVul, ImageInfo, SysLog, TimeMoudel
from dockerapi.serializers import ContainerVulSerializer
from user.models import UserProfile
from tasks.modules.container_tasks import create_container_task, stop_container_task, delete_container_task
from .utils_views import get_request_ip
from .common import R, get_setting_config


class ContainerVulViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContainerVulSerializer

    def get_queryset(self):
        request = self.request
        user = request.user
        flag = request.GET.get("flag", "")
        image_id = request.GET.get("image_id", "")

        now_time = datetime.datetime.now().timestamp()
        time_moudel_data = TimeMoudel.objects.filter(user_id=user.id, end_time__gte=now_time).first()
        time_model_id = ''
        if time_moudel_data:
            time_model_id = time_moudel_data.time_id

        base_query = ContainerVul.objects.select_related('image_id')

        if flag == 'list' and user.is_superuser:
            if image_id:
                container_vul_list = base_query.filter(
                    image_id=image_id, is_docker_compose_correlation=False
                ).order_by('-create_date')
            else:
                container_vul_list = base_query.filter(
                    is_docker_compose_correlation=False
                ).all().order_by('-create_date')
        else:
            container_vul_list = base_query.filter(
                user_id=user.id, time_model_id=time_model_id, is_docker_compose_correlation=False
            )

        return container_vul_list

    @action(methods=["get"], detail=True, url_path='start')
    def start_container(self, request, pk=None):
        user_info = request.user
        container_vul = self.get_object()
        
        task_id = create_container_task(
            container_vul=container_vul, user_info=user_info,
            request_ip=get_request_ip(request)
        )
        return JsonResponse(R.ok(task_id))

    @action(methods=["get"], detail=True, url_path='stop')
    def stop_container(self, request, pk=None):
        user_info = request.user
        container_vul = self.get_object()
        expire = request.GET.get('expire', "")
        
        image_info = ImageInfo.objects.filter(image_id=container_vul.image_id_id).first()
        
        if image_info.is_docker_compose == True:
            original_container = ContainerVul.objects.filter(
                Q(user_id=user_info.id) & Q(image_id=image_info.image_id) &
                Q(container_status="running") & ~Q(docker_compose_path="")
            ).first()
            task_id = stop_container_task(
                container_vul=original_container, user_info=user_info,
                request_ip=get_request_ip(request)
            )
            return JsonResponse(R.ok(task_id))
        
        task_id = stop_container_task(
            container_vul=container_vul, user_info=user_info,
            request_ip=get_request_ip(request)
        )
        
        setting_config = get_setting_config()
        del_container = setting_config['del_container']
        
        if expire != "" and expire == "true":
            if del_container and del_container != 0 and del_container != '0':
                delete_container_task(
                    container_vul=container_vul, user_info=user_info,
                    request_ip=get_request_ip(request)
                )
        
        return JsonResponse(R.ok(task_id))

    @action(methods=["delete"], detail=True, url_path="delete")
    def delete_container(self, request, pk=None):
        if not pk:
            return JsonResponse(R.build(msg="id不能为空"))
        
        user_id = request.user.id
        original_container = ContainerVul.objects.filter(container_id=pk).first()
        
        if not original_container:
            return JsonResponse(R.build(msg="环境不存在"))
        
        user_info = request.user
        task_id = delete_container_task(
            container_vul=original_container, user_info=user_info,
            request_ip=get_request_ip(request)
        )
        return JsonResponse(R.ok(task_id))

    @action(methods=["post", "get"], detail=True, url_path="flag")
    def check_flag(self, request, pk=None):
        request = self.request
        flag = request.GET.get('flag', "")
        container_vul = self.get_object()
        user_info = request.user
        user_id = user_info.id
        
        operation_args = ContainerVulSerializer(container_vul).data
        request_ip = get_request_ip(request)
        
        sys_log = SysLog(
            user_id=user_id, operation_type="容器", operation_name="提交Flag",
            operation_value=operation_args["vul_name"], operation_args={"flag": flag},
            ip=request_ip
        )
        sys_log.save()
        
        if user_id != container_vul.user_id:
            return JsonResponse(R.build(msg="Flag 与用户不匹配"))
        
        if not flag:
            return JsonResponse(R.build(msg="Flag不能为空"))
        
        if flag != container_vul.container_flag:
            return JsonResponse(R.build(msg="flag错误"))
        else:
            if not container_vul.is_check:
                container_vul.is_check_date = datetime.timezone.now()
                
                is_compose_container = ContainerVul.objects.filter(
                    user_id=user_id, is_check=True, time_model_id="",
                    image_id=operation_args['image_id']
                ).first()
                
                img = ImageInfo.objects.filter(image_id=operation_args['image_id']).first()
                
                if is_compose_container and img.is_docker_compose == True:
                    container_vul.is_check = False
                else:
                    container_vul.is_check = True
                
                container_vul.save()
                
                now_time = datetime.datetime.now().timestamp()
                time_moudel_data = TimeMoudel.objects.filter(user_id=user_id, end_time__gte=now_time).first()
                
                if time_moudel_data:
                    rank = 0
                    time_model_id = time_moudel_data.time_id
                    successful = ContainerVul.objects.filter(
                        is_check=True, user_id=user_id, time_model_id=time_model_id
                    ).values('image_id').distinct()
                    
                    rd = TimeRank.objects.filter(
                        time_temp_id=time_moudel_data.temp_time_id_id, user_id=user_id
                    ).first()
                    
                    for i in successful:
                        img = ImageInfo.objects.filter(image_id=i['image_id']).first()
                        rank += img.rank
                    
                    if rank >= rd.rank:
                        rd.rank = rank
                        rd.save()
            
            stop_container_task(
                container_vul=container_vul, user_info=user_info,
                request_ip=get_request_ip(request)
            )
            
            users = UserProfile.objects.filter(id=user_id).first()
            if users.greenhand == True:
                users.greenhand = False
                users.save()
            
            return JsonResponse(R.ok())


def get_setting_config():
    from .common import get_setting_config as _get_setting_config
    return _get_setting_config()