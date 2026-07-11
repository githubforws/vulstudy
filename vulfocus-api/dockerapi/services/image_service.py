import json
import re
import datetime
import logging

import django.utils
import django.utils.timezone as timezone
from django.db.models import Q
from typing import List, Dict, Optional, Any

from dockerapi.models import ImageInfo, ContainerVul, SysLog, TimeMoudel, TimeTemp
from dockerapi.serializers import ImageInfoSerializer, ContainerVulSerializer
from user.models import UserProfile
from tasks.modules.image_tasks import create_image_task
from tasks.models import TaskInfo
from vulfocus.settings import client
from ..views.utils_views import get_request_ip


class ImageService:
    
    @staticmethod
    def get_images(query: str = "", flag: str = "", temp: str = "", rank: str = "",
                   img_t: str = "", user: Any = None, activate_name: str = "all") -> Dict:
        now_time = datetime.datetime.now().timestamp()
        
        min_rank = 0
        try:
            if rank != "undefined" and rank != "":
                rank = float(rank)
                if rank == 0.5:
                    min_rank = 0.0
                if rank == 2.0:
                    min_rank = 1.0
                if rank == 3.5:
                    min_rank = 2.5
                if rank == 5.0:
                    min_rank = 4.0
        except:
            rank = 0.0
        
        time_img_type = []
        rank_range = ""
        image_ids = ""
        
        user_info = UserProfile.objects.filter(username=user.username).first()
        data = TimeMoudel.objects.filter(user_id=user.id, end_time__gte=now_time).first()
        
        if data:
            data_temp = TimeTemp.objects.filter(temp_id=data.temp_time_id_id).first()
            if data_temp.image_ids:
                image_ids = json.loads(data_temp.image_ids)
            if data_temp.rank_range != "":
                rank_range = float(data_temp.rank_range)
            try:
                time_img_type = json.loads(data_temp.time_img_type)
            except Exception as e:
                pass
        
        if user_info.greenhand:
            rank_range_greenhand = Q()
            rank_range_greenhand.children.append(('rank__lte', 0.5))
            rank_range_greenhand.children.append(('rank__gte', 0.0))
            return ImageInfo.objects.filter(rank_range_greenhand).order_by('-create_date')
        
        elif user.is_superuser:
            return ImageService._get_superuser_images(
                query, flag, temp, rank, min_rank, img_t, time_img_type, rank_range,
                image_ids, data, user
            )
        else:
            return ImageService._get_normal_user_images(
                query, temp, rank, min_rank, img_t, time_img_type, rank_range,
                image_ids, data, user
            )
    
    @staticmethod
    def _get_superuser_images(query: str, flag: str, temp: str, rank: float, min_rank: float,
                               img_t: str, time_img_type: List, rank_range: float,
                               image_ids: List, data: Any, user: Any) -> List:
        if query:
            query = query.strip()
            if flag and flag == "flag":
                image_info_list = ImageInfo.objects.filter(
                    Q(image_name__contains=query) | Q(image_vul_name__contains=query)
                    | Q(image_desc__contains=query)).order_by('-create_date')
            else:
                query_q = ImageService._build_query_q(time_img_type, rank_range, min_rank)
                image_q = Q()
                image_q.connector = "OR"
                image_q.children.append(('image_name__contains', query))
                image_q.children.append(('image_desc__contains', query))
                image_q.children.append(('image_vul_name__contains', query))
                
                if not data:
                    query_q.add(image_q, 'AND')
                
                image_info_list = ImageInfo.objects.filter(query_q).order_by('-create_date')
        else:
            if temp == "temp":
                if rank == 0.0:
                    rank = 5
                if not img_t:
                    image_info_list = ImageInfo.objects.filter(
                        Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True)).all()
                else:
                    img_t_list = img_t.split(",")
                    rank_q = Q()
                    rank_q.connector = "AND"
                    rank_q.children.append(('rank__lte', rank))
                    rank_q.children.append(('rank__gte', min_rank))
                    
                    degree_q = Q()
                    if len(img_t_list) > 0:
                        degree_q.connector = 'OR'
                        for img_type in img_t_list:
                            degree_q.children.append(('degree__contains', json.dumps(img_type)))
                    
                    image_info_list = ImageInfo.objects.filter(
                        ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q).all()
            elif flag and flag == "flag":
                image_info_list = ImageInfo.objects.filter().order_by('-create_date')
            else:
                query_q = ImageService._build_query_q(time_img_type, rank_range, min_rank)
                image_info_list = ImageInfo.objects.filter(query_q).order_by('-create_date')
                
                if image_ids:
                    imageids_q = Q()
                    imageids_q.connector = 'OR'
                    for img_id in image_ids:
                        imageids_q.children.append(('image_id', img_id))
                    image_info_list = ImageInfo.objects.filter(imageids_q & Q(is_ok=True)).order_by('-create_date')
        
        if data and not flag and temp != 'temp':
            for image_info in image_info_list:
                image_info.image_name = ''
                image_info.image_vul_name = ''
                image_info.image_desc = ''
        
        return image_info_list
    
    @staticmethod
    def _get_normal_user_images(query: str, temp: str, rank: float, min_rank: float,
                                 img_t: str, time_img_type: List, rank_range: float,
                                 image_ids: List, data: Any, user: Any) -> List:
        if query:
            query = query.strip()
            query_q = ImageService._build_query_q(time_img_type, rank_range, min_rank)
            image_q = Q()
            image_q.connector = "OR"
            image_q.children.append(('image_name__contains', query))
            image_q.children.append(('image_desc__contains', query))
            image_q.children.append(('image_vul_name__contains', query))
            
            if not data:
                query_q.add(image_q, 'AND')
            
            image_info_list = ImageInfo.objects.filter(query_q).order_by('-create_date')
        else:
            if temp == "temp":
                if rank == 0.0:
                    rank = 5
                if not img_t:
                    image_info_list = ImageInfo.objects.filter(
                        Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True)).all()
                else:
                    img_t_list = img_t.split(",")
                    rank_q = Q()
                    rank_q.connector = "AND"
                    rank_q.children.append(('rank__lte', rank))
                    rank_q.children.append(('rank__gte', min_rank))
                    
                    degree_q = Q()
                    if len(img_t_list) > 0:
                        degree_q.connector = 'OR'
                        for img_type in img_t_list:
                            degree_q.children.append(('degree__contains', json.dumps(img_type)))
                    
                    image_info_list = ImageInfo.objects.filter(
                        ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q).all()
            else:
                query_q = ImageService._build_query_q(time_img_type, rank_range, min_rank)
                image_info_list = ImageInfo.objects.filter(query_q).order_by('-create_date')
                
                if image_ids:
                    imageids_q = Q()
                    imageids_q.connector = 'OR'
                    for img_id in image_ids:
                        imageids_q.children.append(('image_id', img_id))
                    image_info_list = ImageInfo.objects.filter(imageids_q & Q(is_ok=True)).order_by('-create_date')
        
        if data:
            for image_info in image_info_list:
                image_info.image_name = ''
                image_info.image_vul_name = ''
                image_info.image_desc = ''
        
        return image_info_list
    
    @staticmethod
    def _build_query_q(time_img_type: List, rank_range: float, min_rank: float) -> Q:
        query_q = Q()
        
        time_img_type_q = Q()
        if len(time_img_type) > 0:
            time_img_type_q.connector = 'OR'
            for img_type in time_img_type:
                time_img_type_q.children.append(('degree__contains', json.dumps(img_type)))
        
        rank_range_q = Q()
        if rank_range != "":
            rank_range_q.connector = 'AND'
            rank_range_q.children.append(('rank__lte', rank_range))
            rank_range_q.children.append(('rank__gte', min_rank))
        
        is_ok_q = Q()
        is_ok_q.connector = 'AND'
        is_ok_q.children.append(('is_ok', True))
        
        if len(time_img_type_q) > 0:
            query_q.add(time_img_type_q, 'AND')
        if type(rank_range) == float:
            query_q.add(rank_range_q, 'AND')
        query_q.add(is_ok_q, 'AND')
        
        return query_q
    
    @staticmethod
    def edit_image(image_id: int, data: Dict, user: Any) -> bool:
        if not user.is_superuser:
            return False
        
        image_info = ImageInfo.objects.filter(image_id=image_id).first()
        if not image_info:
            return False
        
        if "rank" in data:
            try:
                rank = float(data["rank"])
            except:
                rank = 2.5
            image_info.rank = rank
        
        if "is_flag" in data:
            image_info.is_flag = data['is_flag']
        
        if "image_vul_name" in data:
            image_info.image_vul_name = data["image_vul_name"].strip()
        
        if "image_desc" in data:
            image_info.image_desc = data["image_desc"].strip()
        
        if "degree" in data:
            degree = data['degree']
            if degree['HoleType']:
                degree['HoleType'] = list(set(degree['HoleType']))
            if degree['devLanguage']:
                degree['devLanguage'] = list(set(degree['devLanguage']))
            if degree['devDatabase']:
                degree['devDatabase'] = list(set(degree['devDatabase']))
            if degree['devClassify']:
                degree['devClassify'] = list(set(degree['devClassify']))
            image_info.degree = json.dumps(degree)
        
        image_info.update_date = django.utils.timezone.now()
        image_info.save()
        return True
    
    @staticmethod
    def create_image(user: Any, image_name: str, image_vul_name: str, image_desc: str,
                     data: Dict, image_file: Any = None) -> str:
        degree_dict = dict()
        if data.get('HoleType'):
            degree_dict['HoleType'] = list(set(data['HoleType'].split(',')))
        if data.get('devLanguage'):
            degree_dict['devLanguage'] = list(set(data['devLanguage'].split(',')))
        if data.get('devDatabase'):
            degree_dict['devDatabase'] = list(set(data['devDatabase'].split(',')))
        if data.get('devClassify'):
            degree_dict['devClassify'] = list(set(data['devClassify'].split(',')))
        
        try:
            image_rank = float(data.get("rank", 2.5))
        except:
            image_rank = 2.5
        
        is_flag = data.get("is_flag", True)
        if is_flag == 'true':
            is_flag = True
        if is_flag == 'false':
            is_flag = False
        
        if image_name:
            if ":" not in image_name:
                image_name += ":latest"
            image_info = ImageInfo.objects.filter(image_name=image_name).first()
        
        if not image_info:
            image_info = ImageInfo(
                image_name=image_name, image_vul_name=image_vul_name, image_desc=image_desc,
                rank=image_rank, is_ok=False, create_date=timezone.now(),
                update_date=timezone.now(), degree=json.dumps(degree_dict), is_flag=is_flag
            )
            if not image_file:
                image_info.save()
        
        task_id = create_image_task(
            image_info=image_info, user_info=user, request_ip="",
            image_file=image_file
        )
        
        return task_id
    
    @staticmethod
    def search_docker_hub(keyword: str) -> List[Dict]:
        summaries = []
        try:
            import requests
            if not keyword:
                keyword = "vulfocus"
            else:
                keyword = "vulfocus/" + keyword
            
            url = "https://hub.docker.com/api/content/v1/products/search?page_size=50&q={}&type=image".format(keyword)
            headers = {
                "Search-Version": "v3",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                summaries_list = data.get("summaries", [])
                if summaries_list:
                    for item in summaries_list:
                        summaries.append({"name": item.get("name", "")})
        except Exception as e:
            logging.error(f"Docker Hub search error: {str(e)}")
        
        return summaries
    
    @staticmethod
    def get_local_images() -> List[Dict]:
        if client is None:
            return []
        
        local_images = client.images.list()
        db_image_list = ImageInfo.objects.filter(is_ok=True)
        db_image_name_list = [db_image.image_name for db_image in db_image_list]
        
        result_info = []
        for image_info in local_images:
            for image_tag in image_info.tags:
                tmp_info = {"name": image_tag, "flag": False}
                if image_tag in db_image_name_list:
                    tmp_info["flag"] = True
                result_info.append(tmp_info)
        
        return result_info
    
    @staticmethod
    def delete_image(image_id: int, user: Any) -> Dict:
        img_info = ImageInfo.objects.filter(image_id=image_id).first()
        if not img_info:
            return {"success": True, "message": ""}
        
        image_id = img_info.image_id
        container_vul = ContainerVul.objects.filter(
            Q(image_id=image_id) & ~Q(container_status='delete') & ~Q(container_status='creat')
        )
        
        if container_vul.count() == 0:
            img_info.delete()
            return {"success": True, "message": ""}
        else:
            data_json = ContainerVulSerializer(container_vul, many=True)
            return {"success": False, "message": "镜像正在使用，无法删除！", "data": data_json.data}