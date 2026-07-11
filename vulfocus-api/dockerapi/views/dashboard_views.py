import json
import datetime

from django.http import JsonResponse
from django.db.models import Q
from rest_framework.views import APIView

from dockerapi.models import ImageInfo, ContainerVul, TimeMoudel, TimeTemp
from dockerapi.serializers import ImageInfoSerializer
from user.models import UserProfile


class DashboardView(APIView):
    serializer_class = ImageInfoSerializer

    def get(self, request):
        now_time = datetime.datetime.now().timestamp()
        query = self.request.GET.get("query", "")
        flag = self.request.GET.get("flag", "")
        temp = self.request.GET.get("temp", "")
        rank = self.request.GET.get("rank", "")
        activate_name = self.request.GET.get("activate_name", "all")
        
        image_names = []
        image_info_list = []
        count = 0
        
        if activate_name == "started":
            runnging_containers_image = ContainerVul.objects.filter(
                Q(user_id=request.user.id) & Q(container_status="running") & ~Q(docker_container_id="")
            )
            for image in runnging_containers_image:
                image_info = image.image_id
                if image_info:
                    image_names.append(image_info.image_name)
        
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
        
        if self.request.GET.get("page"):
            min_size = (int(self.request.GET.get("page")) - 1) * 20
            max_size = int(self.request.GET.get("page")) * 20
        else:
            min_size = 0
            max_size = 20
        
        img_t = self.request.GET.get("type", "")
        user = self.request.user
        
        degrees = ImageInfo.objects.all().values('degree').distinct()
        HoleType, devLanguage, devDatabase, devClassify = [], [], [], []
        
        try:
            for single_degree in degrees:
                try:
                    origin_degree = json.loads(single_degree["degree"]) if "degree" in single_degree and single_degree["degree"] else ""
                except Exception as e:
                    continue
                
                if isinstance(origin_degree, list):
                    for single_list_degree in origin_degree:
                        HoleType.append(single_list_degree.strip())
                elif isinstance(origin_degree, dict):
                    if "HoleType" in origin_degree and origin_degree["HoleType"]:
                        HoleType += list(map(lambda x: x.strip(), origin_degree["HoleType"]))
                    if "devLanguage" in origin_degree and origin_degree["devLanguage"]:
                        devLanguage += list(map(lambda x: x.strip(), origin_degree["devLanguage"]))
                    if "devDatabase" in origin_degree and origin_degree["devDatabase"]:
                        devDatabase += list(map(lambda x: x.strip(), origin_degree["devDatabase"]))
                    if "devClassify" in origin_degree and origin_degree["devClassify"]:
                        devClassify += list(map(lambda x: x.strip(), origin_degree["devClassify"]))
        except Exception as e:
            pass
        
        return_degree_dict = {
            "HoleType": list(set(HoleType)),
            "devLanguage": list(set(devLanguage)),
            "devDatabase": list(set(devDatabase)),
            "devClassify": list(set(devClassify))
        }
        
        time_img_type = []
        rank_range = ""
        image_ids = ""
        temp_pattern = None
        
        user_info = UserProfile.objects.filter(username=user.username).first()
        data = TimeMoudel.objects.filter(user_id=self.request.user.id, end_time__gte=now_time).first()
        
        if data:
            data_temp = TimeTemp.objects.filter(temp_id=data.temp_time_id_id).first()
            temp_pattern = data_temp.template_pattern
            
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
            
            count = ImageInfo.objects.filter(rank_range_greenhand, is_ok=True).count()
            
            if len(image_names) > 0:
                image_info_list = ImageInfo.objects.filter(
                    rank_range_greenhand, is_ok=True, image_name__in=image_names
                )[min_size:max_size]
            elif len(image_names) == 0 and activate_name == "started":
                pass
            else:
                image_info_list = ImageInfo.objects.filter(rank_range_greenhand, is_ok=True)[min_size:max_size]
        
        elif user.is_superuser:
            count, image_info_list = self._get_superuser_images(
                query, flag, temp, rank, min_rank, img_t, time_img_type, rank_range,
                image_ids, image_names, activate_name, min_size, max_size
            )
        
        else:
            count, image_info_list = self._get_normal_user_images(
                query, temp, rank, min_rank, img_t, time_img_type, rank_range,
                image_ids, image_names, activate_name, min_size, max_size
            )
        
        if data and temp_pattern == 1:
            for image_info in image_info_list:
                image_info.image_name = ''
                image_info.image_vul_name = ''
                image_info.image_desc = ''
        
        data_infos = []
        for imgs in image_info_list:
            img = ImageInfoSerializer(imgs, context={'request': self.request}).data
            if user_info.greenhand != True:
                del_keys = ['writeup_date', 'HoleType', 'devLanguage', 'devDatabase', 'devClassify',
                           'docker_compose_yml', 'docker_compose_env', 'compose_env_port', 'original_yml']
                for key in del_keys:
                    if key in img:
                        del img[key]
                if img.get('is_docker_compose') == True and 'status' in img and 'json_yml' in img['status']:
                    del img['status']['json_yml']
            data_infos.append(img)
        
        return JsonResponse({'results': data_infos, 'count': count, "degree": return_degree_dict})

    def _get_superuser_images(self, query, flag, temp, rank, min_rank, img_t, time_img_type,
                              rank_range, image_ids, image_names, activate_name, min_size, max_size):
        if query:
            query = query.strip()
            if flag and flag == "flag":
                if len(image_names) > 0:
                    count = ImageInfo.objects.filter(
                        Q(image_name__contains=query) | Q(image_vul_name__contains=query) |
                        Q(image_desc__contains=query) & Q(image_name__in=image_names)
                    ).count()
                    image_info_list = ImageInfo.objects.filter(
                        Q(image_name__contains=query) | Q(image_vul_name__contains=query) |
                        Q(image_desc__contains=query) & Q(image_name__in=image_names)
                    )[min_size:max_size]
                elif len(image_names) == 0 and activate_name == "started":
                    count = 0
                    image_info_list = []
                else:
                    count = ImageInfo.objects.filter(
                        Q(image_name__contains=query) | Q(image_vul_name__contains=query) |
                        Q(image_desc__contains=query)
                    ).count()
                    image_info_list = ImageInfo.objects.filter(
                        Q(image_name__contains=query) | Q(image_vul_name__contains=query) |
                        Q(image_desc__contains=query)
                    )[min_size:max_size]
            else:
                query_q = self._build_query_q(time_img_type, rank_range, min_rank)
                img_t_list = []
                if img_t != "":
                    img_t_list = img_t.split(",")
                
                degree_q = Q()
                degree_q.connector = 'AND'
                for img_type in img_t_list:
                    degree_q.children.append(('degree__contains', json.dumps(img_type)))
                
                if len(degree_q) > 0:
                    query_q.add(degree_q, 'AND')
                
                image_q = Q()
                image_q.connector = "OR"
                image_q.children.append(('image_name__contains', query))
                image_q.children.append(('image_desc__contains', query))
                image_q.children.append(('image_vul_name__contains', query))
                
                if not data:
                    query_q.add(image_q, 'AND')
                
                if len(image_names) > 0:
                    image_info_list = ImageInfo.objects.filter(query_q, image_name__in=image_names)[min_size:max_size]
                elif len(image_names) == 0 and activate_name == "started":
                    count = 0
                    image_info_list = []
                else:
                    image_info_list = ImageInfo.objects.filter(query_q)[min_size:max_size]
        else:
            if temp == "temp":
                if rank == 0.0:
                    rank = 5
                if not img_t:
                    if len(image_names) > 0:
                        count = ImageInfo.objects.filter(
                            Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True) &
                            Q(image_name__in=image_names)
                        ).all().count()
                        image_info_list = ImageInfo.objects.filter(
                            Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True) &
                            Q(image_name__in=image_names)
                        ).all()[min_size:max_size]
                    elif len(image_names) == 0 and activate_name == "started":
                        count = 0
                        image_info_list = []
                    else:
                        count = ImageInfo.objects.filter(
                            Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True)
                        ).all().count()
                        image_info_list = ImageInfo.objects.filter(
                            Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True)
                        ).all()[min_size:max_size]
                else:
                    img_t_list = img_t.split(",")
                    rank_q = Q()
                    rank_q.connector = "AND"
                    rank_q.children.append(('rank__lte', rank))
                    rank_q.children.append(('rank__gte', min_rank))
                    
                    degree_q = Q()
                    if len(img_t_list) > 0:
                        degree_q.connector = 'AND'
                        for img_type in img_t_list:
                            degree_q.children.append(('degree__contains', json.dumps(img_type)))
                    
                    if len(image_names) > 0:
                        count = ImageInfo.objects.filter(
                            ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q &
                            Q(image_name__in=image_names)
                        ).all().count()
                        image_info_list = ImageInfo.objects.filter(
                            ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q &
                            Q(image_name__in=image_names)
                        ).all()[min_size:max_size]
                    elif len(image_names) == 0 and activate_name == "started":
                        count = 0
                        image_info_list = []
                    else:
                        count = ImageInfo.objects.filter(
                            ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q
                        ).all().count()
                        image_info_list = ImageInfo.objects.filter(
                            ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q
                        ).all()[min_size:max_size]
            elif flag and flag == "flag":
                if len(image_names) > 0:
                    count = ImageInfo.objects.filter(image_name__in=image_names).count()
                    image_info_list = ImageInfo.objects.filter(image_name__in=image_names)[min_size:max_size]
                elif len(image_names) == 0 and activate_name == "started":
                    count = 0
                    image_info_list = []
                else:
                    count = ImageInfo.objects.all().count()
                    image_info_list = ImageInfo.objects.all()[min_size:max_size]
            else:
                query_q = self._build_query_q(time_img_type, rank_range, min_rank)
                
                if len(image_names) > 0:
                    count = ImageInfo.objects.filter(query_q, image_name__in=image_names).count()
                    image_info_list = ImageInfo.objects.filter(query_q, image_name__in=image_names)[min_size:max_size]
                elif len(image_names) == 0 and activate_name == "started":
                    count = 0
                    image_info_list = []
                else:
                    count = ImageInfo.objects.filter(query_q).count()
                    image_info_list = ImageInfo.objects.filter(query_q)[min_size:max_size]
                
                if image_ids:
                    imageids_q = Q()
                    imageids_q.connector = 'OR'
                    for img_id in image_ids:
                        imageids_q.children.append(('image_id', img_id))
                    
                    if len(image_names) > 0:
                        count = ImageInfo.objects.filter(imageids_q & Q(is_ok=True) & Q(image_name__in=image_names)).count()
                        image_info_list = ImageInfo.objects.filter(imageids_q & Q(is_ok=True) & Q(image_name__in=image_names))[min_size:max_size]
                    elif len(image_names) == 0 and activate_name == "started":
                        count = 0
                        image_info_list = []
                    else:
                        count = ImageInfo.objects.filter(imageids_q & Q(is_ok=True)).count()
                        image_info_list = ImageInfo.objects.filter(imageids_q & Q(is_ok=True))[min_size:max_size]
        
        return count, image_info_list

    def _get_normal_user_images(self, query, temp, rank, min_rank, img_t, time_img_type,
                                rank_range, image_ids, image_names, activate_name, min_size, max_size):
        if query:
            query = query.strip()
            query_q = self._build_query_q(time_img_type, rank_range, min_rank)
            image_q = Q()
            image_q.connector = "OR"
            image_q.children.append(('image_name__contains', query))
            image_q.children.append(('image_desc__contains', query))
            image_q.children.append(('image_vul_name__contains', query))
            
            img_t_list = []
            if img_t != "":
                img_t_list = img_t.split(",")
            
            degree_q = Q()
            if len(img_t_list) > 0:
                degree_q.connector = 'AND'
                for img_type in img_t_list:
                    degree_q.children.append(('degree__contains', json.dumps(img_type)))
            
            if len(degree_q) > 0:
                query_q.add(degree_q, 'AND')
            
            if not data:
                query_q.add(image_q, 'AND')
            
            if len(image_names) > 0:
                count = ImageInfo.objects.filter(query_q, image_name__in=image_names).count()
                image_info_list = ImageInfo.objects.filter(query_q, image_name__in=image_names)[min_size:max_size]
            elif len(image_names) == 0 and activate_name == "started":
                count = 0
                image_info_list = []
            else:
                count = ImageInfo.objects.filter(query_q).count()
                image_info_list = ImageInfo.objects.filter(query_q)[min_size:max_size]
        else:
            if temp == "temp":
                if rank == 0.0:
                    rank = 5
                if not img_t:
                    if len(image_names) > 0:
                        count = ImageInfo.objects.filter(
                            Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True) &
                            Q(image_name__in=image_names)
                        ).all().count()
                        image_info_list = ImageInfo.objects.filter(
                            Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True) &
                            Q(image_name__in=image_names)
                        ).all()[min_size:max_size]
                    elif len(image_names) == 0 and activate_name == "started":
                        count = 0
                        image_info_list = []
                    else:
                        count = ImageInfo.objects.filter(
                            Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True)
                        ).all().count()
                        image_info_list = ImageInfo.objects.filter(
                            Q(rank__lte=rank) & Q(rank__gte=min_rank) & Q(is_ok=True)
                        ).all()[min_size:max_size]
                else:
                    img_t_list = img_t.split(",")
                    rank_q = Q()
                    rank_q.connector = "AND"
                    rank_q.children.append(('rank__lte', rank))
                    rank_q.children.append(('rank__gte', min_rank))
                    
                    degree_q = Q()
                    if len(img_t_list) > 0:
                        degree_q.connector = 'AND'
                        for img_type in img_t_list:
                            degree_q.children.append(('degree__contains', json.dumps(img_type)))
                    
                    if len(image_names) > 0:
                        count = ImageInfo.objects.filter(
                            ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q &
                            Q(image_name__in=image_names)
                        ).all().count()
                        image_info_list = ImageInfo.objects.filter(
                            ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q &
                            Q(image_name__in=image_names)
                        ).all()[min_size:max_size]
                    elif len(image_names) == 0 and activate_name == "started":
                        count = 0
                        image_info_list = []
                    else:
                        count = ImageInfo.objects.filter(
                            ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q
                        ).all().count()
                        image_info_list = ImageInfo.objects.filter(
                            ~Q(degree="") & rank_q & Q(is_ok=True) & degree_q
                        ).all()[min_size:max_size]
            else:
                query_q = self._build_query_q(time_img_type, rank_range, min_rank)
                
                if len(image_names) > 0:
                    count = ImageInfo.objects.filter(query_q, image_name__in=image_names).count()
                    image_info_list = ImageInfo.objects.filter(query_q, image_name__in=image_names)[min_size:max_size]
                elif len(image_names) == 0 and activate_name == "started":
                    count = 0
                    image_info_list = []
                else:
                    count = ImageInfo.objects.filter(query_q).count()
                    image_info_list = ImageInfo.objects.filter(query_q)[min_size:max_size]
                
                if image_ids:
                    imageids_q = Q()
                    imageids_q.connector = 'OR'
                    for img_id in image_ids:
                        imageids_q.children.append(('image_id', img_id))
                    
                    if len(image_names) > 0:
                        count = ImageInfo.objects.filter(imageids_q & Q(is_ok=True) & Q(image_name__in=image_names)).count()
                        image_info_list = ImageInfo.objects.filter(imageids_q & Q(is_ok=True) & Q(image_name__in=image_names))[min_size:max_size]
                    elif len(image_names) == 0 and activate_name == "started":
                        count = 0
                        image_info_list = []
                    else:
                        count = ImageInfo.objects.filter(imageids_q & Q(is_ok=True)).count()
                        image_info_list = ImageInfo.objects.filter(imageids_q & Q(is_ok=True))[min_size:max_size]
        
        return count, image_info_list

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