import json
import uuid
import datetime

from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView

from dockerapi.models import TimeTemp, TimeRank, TimeMoudel, ContainerVul, SysLog
from dockerapi.serializers import TimeTempSerializer, TimeRankSerializer, TimeMoudelSerializer
from user.models import UserProfile
from vulfocus.settings import client
from .utils_views import get_request_ip
from .common import R


class CreateTimeTemplate(viewsets.ModelViewSet):
    serializer_class = TimeTempSerializer

    def get_queryset(self, *args, **kwargs):
        return TimeTemp.objects.all()

    def create(self, request, *args, **kwargs):
        user_id = request.user.id
        # 使用 .get() 兼容前端 Vue 3 重写后的字段名，缺失字段给默认值
        time_desc = request.data.get('time_desc', '')
        time_img_type = request.data.get('time_img_type', '')
        rank_range = request.data.get('rank_range', '')
        name = request.data.get('name', '')
        ilist = request.data.get('ilist', '')
        template_pattern = request.data.get('template_pattern', None) or 1
        # timer_minutes 和 time_range 双兼容（前端发 timer_minutes，旧调用发 time_range）
        timer_value = request.data.get('timer_minutes', request.data.get('time_range', 0))
        img = request.data.get('imageName', '')

        try:
            time_range = int(timer_value)
        except (TypeError, ValueError):
            return JsonResponse(data={"code": 2001, "message": "时间范围必须为有效整数"})

        existence_name = TimeTemp.objects.filter(name=name).first()
        if ilist:
            ilist = json.dumps(ilist.split(","))

        if existence_name:
            return JsonResponse(data={"code": 2001, "message": "名称已存在"})
        if not name:
            return JsonResponse(data={"code": 2001, "message": "名称不能为空"})
        if len(name) > 255:
            return JsonResponse(data={"code": 2001, "message": "名称过长"})
        if time_range <= 0 or time_range % 30 != 0:
            return JsonResponse(data={"code": 2001, "message": "时间范围不能为空，并且必须是整数，且是30的倍数"})

        image_type_list = []
        if time_img_type:
            for image_type in time_img_type.split(','):
                image_type = image_type.strip()
                if not image_type:
                    continue
                if image_type in image_type_list:
                    continue
                image_type_list.append(image_type)
        time_img_type = json.dumps(image_type_list)

        timetemp_info = TimeTemp(
            user_id=user_id, time_range=time_range, time_desc=time_desc, image_name=img,
            time_img_type=time_img_type, rank_range=rank_range, name=name, image_ids=ilist,
            template_pattern=template_pattern
        )
        timetemp_info.save()
        data = self.serializer_class(timetemp_info).data
        return JsonResponse(R.ok(data=data))

    def destroy(self, request, *args, **kwargs):
        user = request.user
        now_time = datetime.datetime.now().timestamp()
        
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"))
        
        if "id" in request.data:
            temp_id = request.data['id']
        else:
            temp = self.get_object()
            temp_id = self.get_serializer(temp).data['temp_id']
        
        data = TimeMoudel.objects.filter(temp_time_id_id=temp_id, end_time__gte=now_time).first()
        if data:
            return JsonResponse({"code": 2001, "message": "删除失败，该模版计时模式已启动"})
        
        try:
            temp = TimeTemp.objects.filter(temp_id=temp_id).first()
            temp.delete()
        except Exception as e:
            return JsonResponse({"code": 2001, "message": "删除失败"})
        
        return JsonResponse({"code": 200, "message": "删除成功"})


class TimeRankSet(APIView):
    serializer_class = TimeRankSerializer

    def get(self, request):
        user_name = request.user.username
        value = self.request.GET.get("value")
        page = self.request.GET.get("page", 1)
        
        if page:
            min_size = (int(page) - 1) * 20
            max_size = int(page) * 20
        else:
            min_size = 0
            max_size = 20
        
        time_data = TimeTemp.objects.all().filter(temp_id=value).first()
        if not time_data:
            time_data = TimeTemp.objects.all().filter(time_desc=value).first()
        
        count = TimeRank.objects.all().filter(time_temp_id=time_data.temp_id, rank__gt=0).order_by("-rank").count()
        all_temp_data = TimeRank.objects.all().filter(time_temp_id=time_data.temp_id, rank__gt=0).order_by("-rank").all()
        
        current_rank = 0
        current_score = 0
        for i, _score in enumerate(all_temp_data):
            _score = TimeRankSerializer(_score).data
            if user_name != _score['name']:
                continue
            current_rank = i + 1
            current_score = _score["rank"]
            break
        
        temp_data = TimeRank.objects.all().filter(time_temp_id=time_data.temp_id, rank__gt=0).order_by("-rank")[min_size:max_size]
        temp_list = []
        for tmp in temp_data:
            temp = TimeRankSerializer(tmp).data
            user_info = UserProfile.objects.filter(username=temp['name']).first()
            avatar = ""
            if user_info:
                avatar = user_info.avatar
            temp['avatar'] = avatar
            temp_list.append(temp)
        
        return JsonResponse({'results': temp_list, 'count': count, "current_rank": current_rank, 'current_score': current_score})


class TimeMoudelSet(viewsets.ModelViewSet):
    serializer_class = TimeMoudelSerializer

    def get_queryset(self):
        now_time = datetime.datetime.now().timestamp()
        # 到期自动标记过期并清理所有用户的容器
        expired = TimeMoudel.objects.filter(end_time__lt=now_time, status=True)
        for em in expired:
            container_vul_list = ContainerVul.objects.filter(time_model_id=em.time_id)
            for cv in container_vul_list:
                try:
                    docker_container = client.containers.get(container_id=cv.docker_container_id)
                    docker_container.remove()
                except Exception:
                    pass
                cv.delete()
        expired.update(status=False)
        return TimeMoudel.objects.filter(status=True)

    @action(methods=["get"], detail=True, url_path="get")
    def get_layout(self, request, pk=None):
        if not pk or pk == "undefined":
            return JsonResponse(R.build(msg="环境不存在"))
        time_info = TimeTemp.objects.filter(temp_id=pk).first()
        time_info.total_view += 1
        time_info.save()
        data = TimeTempSerializer(time_info).data
        return JsonResponse(data)

    def delete(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"code": "2001", "msg": "权限不足"})
        now_time = datetime.datetime.now().timestamp()

        try:
            session = TimeMoudel.objects.filter(end_time__gte=now_time, status=True).first()
            if not session:
                session = TimeMoudel.objects.filter(end_time__lte=now_time).first()
            if not session:
                return JsonResponse({"code": "2001", "msg": "无活跃计时会话"})
            time_id = session.time_id

            # 清理所有用户在此会话中的容器
            container_vul_list = ContainerVul.objects.filter(time_model_id=time_id)
            for container_vul in container_vul_list:
                try:
                    docker_container = client.containers.get(container_id=container_vul.docker_container_id)
                    docker_container.remove()
                except Exception:
                    pass
                container_vul.delete()

            TimeMoudel.objects.filter(time_id=time_id).delete()
            return JsonResponse({"code": "2000", "msg": "成功"}, status=201)
        except Exception as e:
            return JsonResponse({"code": "2001", "msg": str(e)})

    @action(methods=['get'], detail=False, url_path="info")
    def info(self, request, pk=None):
        user_id = request.user.id
        now_time = datetime.datetime.now().timestamp()
        user_data = UserProfile.objects.filter(id=user_id).first()
        # 全局会话：按模板 ID 查找当前活跃的计时会话
        temp_id = request.GET.get('temp_id', '')
        if temp_id:
            data = TimeMoudel.objects.filter(temp_time_id_id=temp_id, end_time__gte=now_time).first()
        else:
            data = TimeMoudel.objects.filter(end_time__gte=now_time).first()
        
        if not data:
            return JsonResponse({"code": "2001", "msg": "不在答题模式中", "data": ""})
        
        time_moudel_serializer = TimeMoudelSerializer(data)
        info = time_moudel_serializer.data
        
        time_id = data.time_id
        total_rank = 0.0
        time_moudel_vul_list = ContainerVul.objects.filter(time_model_id=time_id, is_check=True)
        for time_moudel_vul in time_moudel_vul_list:
            total_rank += time_moudel_vul.image_id.rank
        
        trdata = TimeRank.objects.filter(time_temp_id=data.temp_time_id_id, user_id=user_id).first()
        if trdata:
            trdata.update(rank=total_rank)
        else:
            tr = TimeRank(
                user_id=user_id, rank=total_rank, time_temp_id=data.temp_time_id_id,
                user_name=user_data.username
            )
            tr.save()
        
        info['rank'] = total_rank
        return JsonResponse({"code": "200", "msg": "", "data": info})

    @action(methods=['get'], detail=False, url_path="check")
    def check(self, request, pk=None):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"code": "2001", "msg": "权限不足"})
        now_time = datetime.datetime.now().timestamp()
        data = TimeMoudel.objects.filter(end_time__gte=now_time).first()
        
        if data:
            # 清理所有用户在此会话中的容器
            container_vul_list = ContainerVul.objects.filter(time_model_id=data.time_id)
            for container_vul in container_vul_list:
                try:
                    docker_container = client.containers.get(container_id=container_vul.docker_container_id)
                    docker_container.remove()
                except Exception:
                    pass
                container_vul.delete()
            data.delete()
            return JsonResponse({"code": "200", "msg": "OK"})
        else:
            return JsonResponse({"code": "2001", "msg": "时间已到"})

    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse({"code": "2001", "msg": "权限不足"})
        user_id = user.id
        now_time = datetime.datetime.now().timestamp()
        temp_id = request.data.get('temp_id', '')
        # 从模板中读取时间范围，前端不再单独发送 time_range
        time_temp = TimeTemp.objects.filter(temp_id=temp_id).first()
        if not time_temp:
            return JsonResponse({"code": "2001", "msg": "计时模板不存在"})
        time_minute = time_temp.time_range

        # 同一模板已有活跃会话则不允许重复启动
        data = TimeMoudel.objects.filter(temp_time_id_id=temp_id, end_time__gte=now_time).first()

        if data:
            return JsonResponse({"code": "2001", "msg": "计时已启动，请勿重复操作", "data": ""})
        else:
            try:
                request_ip = get_request_ip(request)
                sys_log = SysLog(
                    user_id=user_id, operation_type="时间模式", operation_name="创建 ", operation_value="",
                    operation_args={}, ip=request_ip
                )
                sys_log.save()
            except Exception:
                pass

            now_time_dt = datetime.datetime.now()
            end_time_dt = now_time_dt + datetime.timedelta(minutes=time_minute)
            start_time_timestamp = now_time_dt.timestamp()
            end_time_timestamp = end_time_dt.timestamp()

            time_moudel = TimeMoudel(
                time_id=str(uuid.uuid4()), user_id=user_id, start_time=start_time_timestamp,
                end_time=end_time_timestamp, temp_time_id_id=temp_id, status=True
            )
            time_moudel.save()
            time_moudel_info = TimeMoudelSerializer(time_moudel)
            data = time_moudel_info.data

            return JsonResponse({"code": "200", "msg": "OK", "data": data}, status=201)