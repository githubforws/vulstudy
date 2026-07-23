import json
import re
import datetime
import logging

import django.utils
import django.utils.timezone as timezone
from django.http import JsonResponse
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action

from dockerapi.models import ImageInfo, ContainerVul, SysLog, TimeMoudel, TimeTemp
from dockerapi.serializers import ImageInfoSerializer, ContainerVulSerializer
from user.models import UserProfile
from tasks.modules.image_tasks import create_image_task
from tasks.modules.share_tasks import share_image_task
from tasks.modules.compose_tasks import start_docker_compose
from tasks.modules.container_tasks import create_container_task
from tasks.models import TaskInfo
from vulfocus.settings import client
from .utils_views import get_request_ip
from .common import R


class ImageInfoViewSet(viewsets.ModelViewSet):
    serializer_class = ImageInfoSerializer

    def get_queryset(self):
        now_time = datetime.datetime.now().timestamp()
        query = self.request.GET.get("query", "")
        flag = self.request.GET.get("flag", "")
        temp = self.request.GET.get("temp", "")
        rank = self.request.GET.get("rank", "")
        
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
        
        img_t = self.request.GET.get("type", "")
        user = self.request.user
        time_img_type = []
        rank_range = ""
        image_ids = ""
        
        user_info = UserProfile.objects.filter(username=user.username).first()
        data = TimeMoudel.objects.filter(user_id=self.request.user.id, end_time__gte=now_time).first()
        
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
        
        if user_info.greenhand == True:
            rank_range_greenhand = Q()
            rank_range_greenhand.children.append(('rank__lte', 0.5))
            rank_range_greenhand.children.append(('rank__gte', 0.0))
            return ImageInfo.objects.filter(rank_range_greenhand).order_by('-create_date')
        
        elif user.is_superuser:
            return self._get_superuser_queryset(query, flag, temp, rank, min_rank, img_t, time_img_type, rank_range, image_ids, data)
        
        else:
            return self._get_normal_user_queryset(query, temp, rank, min_rank, img_t, time_img_type, rank_range, image_ids, data)

    def _get_superuser_queryset(self, query, flag, temp, rank, min_rank, img_t, time_img_type, rank_range, image_ids, data):
        if query:
            query = query.strip()
            if flag and flag == "flag":
                image_info_list = ImageInfo.objects.filter(
                    Q(image_name__contains=query) | Q(image_vul_name__contains=query)
                    | Q(image_desc__contains=query)).order_by('-create_date')
            else:
                query_q = self._build_query_q(time_img_type, rank_range, min_rank)
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
                query_q = self._build_query_q(time_img_type, rank_range, min_rank)
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

    def _get_normal_user_queryset(self, query, temp, rank, min_rank, img_t, time_img_type, rank_range, image_ids, data):
        if query:
            query = query.strip()
            query_q = self._build_query_q(time_img_type, rank_range, min_rank)
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
                query_q = self._build_query_q(time_img_type, rank_range, min_rank)
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

    def _build_query_q(self, time_img_type, rank_range, min_rank):
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

    def destroy(self, request, *args, **kwargs):
        return JsonResponse(R.ok())

    @action(methods=["post"], detail=True, url_path="edit")
    def edit_image(self, request, pk=None):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"))
        
        data = request.data
        image_info = ImageInfo.objects.filter(image_id=pk).first()
        if not image_info:
            return JsonResponse(R.build(msg="镜像不存在"))
        
        if "rank" in data:
            try:
                rank = float(data["rank"])
            except:
                rank = 2.5
            image_info.rank = rank
        
        if "is_flag" in data:
            is_flag = data['is_flag']
            image_info.is_flag = is_flag
        
        if "image_vul_name" in data:
            image_vul_name = data["image_vul_name"].strip()
            image_info.image_vul_name = image_vul_name
        
        if "image_desc" in data:
            image_desc = data["image_desc"].strip()
            image_info.image_desc = image_desc

        if "degree" in data:
            raw = data['degree']
            # Accept both dict and JSON string (from frontend JSON.stringify)
            if isinstance(raw, str):
                try:
                    incoming_degree = json.loads(raw)
                except json.JSONDecodeError:
                    incoming_degree = {}
            else:
                incoming_degree = raw
            if not isinstance(incoming_degree, dict):
                incoming_degree = {}

            # Merge with existing degree instead of replacing entirely
            existing_degree = {}
            if image_info.degree:
                try:
                    existing_degree = json.loads(image_info.degree)
                except (json.JSONDecodeError, TypeError):
                    existing_degree = {}
            if not isinstance(existing_degree, dict):
                existing_degree = {}

            # Only overwrite fields that are present in incoming data
            for key in ['HoleType', 'devLanguage', 'devDatabase', 'devClassify']:
                if key in incoming_degree:
                    val = incoming_degree[key]
                    if isinstance(val, list):
                        existing_degree[key] = list(set(val))
                    else:
                        existing_degree[key] = val

            image_info.degree = json.dumps(existing_degree)
        
        image_info.update_date = django.utils.timezone.now()
        image_info.save()
        return JsonResponse(R.ok())

    def update(self, request, *args, **kwargs):
        return JsonResponse(R.ok())

    def create(self, request, *args, **kwargs):
        user = request.user
        image_name = request.POST.get("image_name", "")
        image_vul_name = request.POST.get("image_vul_name", "")
        image_desc = request.POST.get("image_desc", "")
        data = request.data

        degree_dict = dict()
        if data['HoleType']:
            degree_dict['HoleType'] = list(set(data['HoleType'].split(',')))
        if data['devLanguage']:
            degree_dict['devLanguage'] = list(set(data['devLanguage'].split(',')))
        if data['devDatabase']:
            degree_dict['devDatabase'] = list(set(data['devDatabase'].split(',')))
        if data['devClassify']:
            degree_dict['devClassify'] = list(set(data['devClassify'].split(',')))
        degree = degree_dict
        
        try:
            image_rank = request.POST.get("rank", default=2.5)
            image_rank = float(image_rank)
        except:
            image_rank = 2.5
        
        is_flag = request.POST.get("is_flag", True)
        if is_flag == 'true':
            is_flag = True
        if is_flag == 'false':
            is_flag = False
        
        image_file = request.FILES.get("file")
        image_info = None
        
        if image_name:
            if ":" not in image_name:
                image_name += ":latest"
            image_info = ImageInfo.objects.filter(image_name=image_name).first()
        
        if not image_info:
            image_info = ImageInfo(
                image_name=image_name, image_vul_name=image_vul_name, image_desc=image_desc,
                rank=image_rank, is_ok=False, create_date=timezone.now(), update_date=timezone.now(),
                degree=json.dumps(degree), is_flag=is_flag
            )
            if not image_file:
                image_info.save()
        
        task_id = create_image_task(
            image_info=image_info, user_info=user, request_ip=get_request_ip(request),
            image_file=image_file
        )
        
        if image_file:
            task_info = TaskInfo.objects.filter(task_id=task_id).first()
            task_msg = task_info.task_msg
            return JsonResponse(json.loads(task_msg))
        
        return JsonResponse(R.ok(task_id, msg="拉取镜像%s任务下发成功" % (image_name,)))

    @action(methods=["get"], detail=True, url_path="download")
    def download_image(self, request, pk=None):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"))

        image_info = ImageInfo.objects.filter(image_id=pk).first()
        if image_info.is_docker_compose == True:
            return JsonResponse(R.build(msg="该镜像为启动方式为docker-compose，不允许直接下载"))
        if not image_info:
            return JsonResponse(R.build(msg="镜像不存在"))
        
        task_id = create_image_task(
            image_info=image_info, user_info=user, request_ip=get_request_ip(request)
        )
        return JsonResponse(R.ok(task_id, msg="拉取镜像%s任务下发成功" % (image_info.image_name,)))

    @action(methods=["get"], detail=True, url_path="share")
    def share_image(self, request, pk=None):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"))
        
        img_info = ImageInfo.objects.filter(image_id=pk).first()
        if not img_info:
            return JsonResponse(R.build(msg="镜像不存在"))
        
        setting_config = get_setting_config()
        share_username = setting_config["share_username"].strip()
        
        if not share_username:
            return JsonResponse(R.build(msg="分享用户名不能为空，请在系统管理中的系统配置模块进行配置分享用户名。"))
        
        share_username_reg = "[\da-zA-z\-]+"
        if not re.match(share_username_reg, share_username):
            return JsonResponse(R.build(msg="分享用户名不符合要求"))
        
        task_id = share_image_task(
            image_info=img_info, user_info=user, request_ip=get_request_ip(request)
        )
        return JsonResponse(R.ok(task_id))

    @action(methods=["get"], detail=False, url_path="search")
    def search_docker_hub(self, request):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"), status=403)

        query = request.GET.get("q", "").strip().lower()
        summaries = []
        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            # Docker Hub v2 API 列出 vulfocus 命名空间下的所有镜像
            page = 1
            total_count = 0
            while True:
                url = "https://hub.docker.com/v2/repositories/vulfocus/?page={}&page_size=100".format(page)
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    break
                data = response.json()
                results = data.get("results", [])
                total_count = data.get("count", 0)
                for repo in results:
                    repo_name = repo.get("name", "")
                    # 跳过 vulfocus/vulfocus 自身（不是漏洞镜像）
                    if repo_name == "vulfocus":
                        continue
                    # 精确/模糊匹配用户输入
                    if not query or query in repo_name.lower():
                        summaries.append({"name": "vulfocus/" + repo_name})
                # 如果已匹配到足够结果或已翻完所有页
                if len(summaries) >= 20 or len(results) < 100:
                    break
                page += 1

        except requests.exceptions.Timeout:
            logging.error("Docker Hub API request timed out")
            return JsonResponse(R.build(msg="搜索超时，请稍后重试"), status=504)
        except requests.exceptions.ConnectionError:
            logging.error("Docker Hub API connection error")
            return JsonResponse(R.build(msg="网络连接失败，请检查网络"), status=502)
        except Exception as e:
            logging.error(f"Docker Hub search error: {str(e)}")
            return JsonResponse(R.build(msg=f"搜索失败: {str(e)}"), status=500)

        return JsonResponse(R.ok(data={"summaries": summaries}))

    @action(methods=["get"], detail=False, url_path="local")
    def local(self, request):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"))
        
        if client is None:
            return JsonResponse(R.build(msg="Docker客户端连接失败，请检查Docker服务是否正常运行或Docker socket是否正确挂载"))
        
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
        
        return JsonResponse(R.ok(result_info))

    @action(methods=["post"], detail=False, url_path="local_add")
    def batch_local_add(self, request):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"))
        
        image_name_str = request.POST.get("image_names", "")
        image_names = image_name_str.split(",")
        rsp_msg = []
        
        for image_name in image_names:
            if not image_name:
                continue
            if ":" not in image_name:
                image_name += ":latest"
            
            image_info = ImageInfo.objects.filter(image_name=image_name).first()
            if not image_info:
                image_vul_name = image_name[:image_name.rfind(":")]
                image_info = ImageInfo(
                    image_name=image_name, image_vul_name=image_vul_name, image_desc=image_vul_name,
                    rank=2.5, is_ok=False, create_date=timezone.now(), update_date=timezone.now()
                )
                image_info.save()
            
            task_id = create_image_task(
                image_info=image_info, user_info=user, request_ip=get_request_ip(request),
                image_file=None
            )
            if task_id:
                rsp_msg.append("拉取镜像%s任务下发成功" % (image_name,))
        
        return JsonResponse(R.ok(data=rsp_msg))

    @action(methods=["get"], detail=True, url_path="delete")
    def delete_image(self, request, pk=None):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"))
        
        img_info = ImageInfo.objects.filter(image_id=pk).first()
        if not img_info:
            return JsonResponse(R.ok())
        
        operation_args = ImageInfoSerializer(img_info).data
        request_ip = get_request_ip(request)
        
        sys_log = SysLog(
            user_id=user.id, operation_type="镜像", operation_name="删除",
            operation_value=operation_args["image_vul_name"], operation_args=json.dumps(operation_args), ip=request_ip
        )
        sys_log.save()
        
        image_id = img_info.image_id
        container_vul = ContainerVul.objects.filter(
            Q(image_id=image_id) & ~Q(container_status='delete') & ~Q(container_status='creat')
        )
        data_json = ContainerVulSerializer(container_vul, many=True)
        
        if container_vul.count() == 0:
            img_info.delete()
            return JsonResponse(R.ok())
        else:
            return JsonResponse(R.build(msg="镜像正在使用，无法删除！", data=data_json.data))

    @action(methods=["post", "get"], detail=True, url_path="start")
    def start_container(self, request, pk=None):
        img_info = self.get_object()
        user = request.user
        image_id = img_info.image_id
        user_id = user.id
        
        now_time = datetime.datetime.now().timestamp()
        # 全局会话：查找当前活跃计时会话
        time_moudel_data = TimeMoudel.objects.filter(end_time__gte=now_time).first()
        time_model_id = ''
        if time_moudel_data:
            time_model_id = time_moudel_data.time_id
        
        image_info = ImageInfoSerializer(img_info).data
        container_vul = ContainerVul.objects.filter(user_id=user_id, image_id=image_id, time_model_id=time_model_id).first()
        compose_container_vul = ContainerVul.objects.filter(
            Q(user_id=user_id) & Q(image_id=image_id) & Q(time_model_id=time_model_id) &
            Q(container_status='stop') & ~Q(docker_compose_path="")
        ).first()
        
        if not container_vul or image_info['is_docker_compose'] == True:
            if compose_container_vul:
                container_vul = compose_container_vul
            else:
                container_vul = ContainerVul(
                    image_id=img_info, user_id=user_id, vul_host="", container_status="creat",
                    docker_container_id="", vul_port="", container_port="",
                    time_model_id=time_model_id, create_date=django.utils.timezone.now(),
                    container_flag=""
                )
                container_vul.save()
        
        if image_info['is_docker_compose'] == True:
            task_id = start_docker_compose(request, image_id, container_vul, user, get_request_ip(request), time_model_id)
        else:
            task_id = create_container_task(container_vul, user, get_request_ip(request))
        
        return JsonResponse(R.ok(task_id))


def get_setting_config():
    from .common import get_setting_config as _get_setting_config
    return _get_setting_config()