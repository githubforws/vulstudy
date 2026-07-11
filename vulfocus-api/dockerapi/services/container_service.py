import datetime
import json

from django.db.models import Q
from typing import Dict, Any

from dockerapi.models import ContainerVul, ImageInfo, SysLog, TimeMoudel
from dockerapi.serializers import ContainerVulSerializer
from user.models import UserProfile
from tasks.modules.container_tasks import create_container_task, stop_container_task, delete_container_task
from ..views.utils_views import get_request_ip
from ..views.common import R, get_setting_config


class ContainerService:
    
    @staticmethod
    def get_containers(user: Any, flag: str = "", image_id: str = "") -> list:
        now_time = datetime.datetime.now().timestamp()
        time_moudel_data = TimeMoudel.objects.filter(user_id=user.id, end_time__gte=now_time).first()
        time_model_id = ''
        if time_moudel_data:
            time_model_id = time_moudel_data.time_id
        
        if flag == 'list' and user.is_superuser:
            if image_id:
                return ContainerVul.objects.filter(
                    image_id=image_id, is_docker_compose_correlation=False
                ).order_by('-create_date')
            else:
                return ContainerVul.objects.filter(
                    is_docker_compose_correlation=False
                ).all().order_by('-create_date')
        else:
            return ContainerVul.objects.filter(
                user_id=user.id, time_model_id=time_model_id, is_docker_compose_correlation=False
            )
    
    @staticmethod
    def start_container(container_vul: ContainerVul, user: Any, request_ip: str) -> str:
        return create_container_task(
            container_vul=container_vul, user_info=user,
            request_ip=request_ip
        )
    
    @staticmethod
    def stop_container(container_vul: ContainerVul, user: Any, request_ip: str, expire: str = "") -> str:
        image_info = ImageInfo.objects.filter(image_id=container_vul.image_id_id).first()
        
        if image_info.is_docker_compose:
            original_container = ContainerVul.objects.filter(
                Q(user_id=user.id) & Q(image_id=image_info.image_id) &
                Q(container_status="running") & ~Q(docker_compose_path="")
            ).first()
            task_id = stop_container_task(
                container_vul=original_container, user_info=user,
                request_ip=request_ip
            )
            return task_id
        
        task_id = stop_container_task(
            container_vul=container_vul, user_info=user,
            request_ip=request_ip
        )
        
        setting_config = get_setting_config()
        del_container = setting_config['del_container']
        
        if expire == "true" and del_container and del_container != '0':
            delete_container_task(
                container_vul=container_vul, user_info=user,
                request_ip=request_ip
            )
        
        return task_id
    
    @staticmethod
    def delete_container(container_id: int, user: Any, request_ip: str) -> str:
        original_container = ContainerVul.objects.filter(container_id=container_id).first()
        if not original_container:
            return ""
        
        return delete_container_task(
            container_vul=original_container, user_info=user,
            request_ip=request_ip
        )
    
    @staticmethod
    def check_flag(container_vul: ContainerVul, flag: str, user: Any, request_ip: str) -> Dict:
        if user.id != container_vul.user_id:
            return {"success": False, "message": "Flag 与用户不匹配"}
        
        if not flag:
            return {"success": False, "message": "Flag不能为空"}
        
        if flag != container_vul.container_flag:
            return {"success": False, "message": "flag错误"}
        
        if not container_vul.is_check:
            container_vul.is_check_date = datetime.timezone.now()
            
            is_compose_container = ContainerVul.objects.filter(
                user_id=user.id, is_check=True, time_model_id="",
                image_id=container_vul.image_id_id
            ).first()
            
            img = ImageInfo.objects.filter(image_id=container_vul.image_id_id).first()
            
            if is_compose_container and img.is_docker_compose:
                container_vul.is_check = False
            else:
                container_vul.is_check = True
            
            container_vul.save()
            
            now_time = datetime.datetime.now().timestamp()
            time_moudel_data = TimeMoudel.objects.filter(user_id=user.id, end_time__gte=now_time).first()
            
            if time_moudel_data:
                rank = 0
                time_model_id = time_moudel_data.time_id
                successful = ContainerVul.objects.filter(
                    is_check=True, user_id=user.id, time_model_id=time_model_id
                ).values('image_id').distinct()
                
                from dockerapi.models import TimeRank
                rd = TimeRank.objects.filter(
                    time_temp_id=time_moudel_data.temp_time_id_id, user_id=user.id
                ).first()
                
                for i in successful:
                    img = ImageInfo.objects.filter(image_id=i['image_id']).first()
                    rank += img.rank
                
                if rank >= rd.rank:
                    rd.rank = rank
                    rd.save()
        
        stop_container_task(
            container_vul=container_vul, user_info=user,
            request_ip=request_ip
        )
        
        users = UserProfile.objects.filter(id=user.id).first()
        if users.greenhand:
            users.greenhand = False
            users.save()
        
        return {"success": True, "message": ""}