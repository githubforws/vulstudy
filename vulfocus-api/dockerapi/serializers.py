from django.db.models import Q
from rest_framework import serializers
from dockerapi.models import ImageInfo, ContainerVul, SysLog, TimeMoudel, TimeRank, TimeTemp
from user.models import UserProfile
import json
import time
import datetime


class TimeTempSerializer(serializers.ModelSerializer):
    time_img_type = serializers.SerializerMethodField()
    rank_range = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_time_img_type(self, obj):
        img_d = obj.time_img_type
        try:
            return json.loads(img_d)
        except Exception:
            return []

    def get_rank_range(self, obj):
        if obj.rank_range != "":
            try:
                return float(obj.rank_range)
            except Exception:
                return 0.0
        return ""

    def get_name(self, obj):
        name = obj.name.rstrip()
        try:
            if not name:
                name = obj.time_desc
            return name
        except Exception:
            return name

    class Meta:
        model = TimeTemp
        fields = "__all__"


class TimeRankSerializer(serializers.ModelSerializer):
    flag_s = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TimeRank
        fields = "__all__"

    def get_flag_s(self, obj):
        return ""

    def get_name(self, obj):
        return obj.user_name

    def get_image_url(self, obj):
        try:
            user = UserProfile.objects.get(username=obj.user_name)
            return user.avatar
        except UserProfile.DoesNotExist:
            return ""


class TimeMoudelSerializer(serializers.ModelSerializer):
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()

    class Meta:
        model = TimeMoudel
        fields = ['start_date', 'end_date', "temp_time_id"]

    def get_start_date(self, obj):
        time_stamp = obj.start_time
        time_arr = time.localtime(time_stamp)
        return str(time.strftime("%Y-%m-%d %H:%M:%S", time_arr))

    def get_end_date(self, obj):
        time_stamp = obj.end_time
        time_arr = time.localtime(time_stamp)
        return str(time.strftime("%Y-%m-%d %H:%M:%S", time_arr))


class ImageInfoSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    degree = serializers.SerializerMethodField()
    writeup_date = serializers.SerializerMethodField()
    update_date = serializers.SerializerMethodField()
    image_port = serializers.SerializerMethodField()
    HoleType = serializers.SerializerMethodField()
    devLanguage = serializers.SerializerMethodField()
    devDatabase = serializers.SerializerMethodField()
    devClassify = serializers.SerializerMethodField()

    class Meta:
        model = ImageInfo
        fields = "__all__"

    def get_status(self, obj):
        status = {
            "status": "",
            "is_check": False,
            "container_id": "",
            "start_date": "",
            "end_date": "",
            "host": "",
            "port": "",
            "progress": 0.0,
            "progress_status": "",
            "task_id": "",
            "now": int(time.time()),
        }
        
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return status
        
        user_id = request.user.id
        now_time = datetime.datetime.now().timestamp()
        
        time_moudel_data = TimeMoudel.objects.filter(user_id=user_id, end_time__gte=now_time).first()
        time_model_id = time_moudel_data.time_id if time_moudel_data else ''
        
        data_is_check = ContainerVul.objects.filter(
            user_id=user_id, image_id=obj.image_id, time_model_id=time_model_id, is_check=True
        ).first()
        if data_is_check:
            status["is_check"] = True
        
        if obj.is_docker_compose:
            data = ContainerVul.objects.filter(
                Q(user_id=user_id) & Q(image_id=obj.image_id) & ~Q(docker_compose_path="") &
                Q(time_model_id=time_model_id) & Q(container_status__contains="running") &
                Q(is_docker_compose_correlation=False)
            ).first()
            if not data:
                data = ContainerVul.objects.filter(
                    Q(user_id=user_id) & Q(image_id=obj.image_id) & Q(time_model_id=time_model_id) &
                    ~Q(docker_compose_path="") & Q(container_status__contains="stop") &
                    Q(is_docker_compose_correlation=False)
                ).first()
        else:
            data = ContainerVul.objects.filter(
                Q(user_id=user_id) & Q(image_id=obj.image_id) & Q(time_model_id=time_model_id) &
                Q(container_status='running')
            ).first()
            if not data:
                data = ContainerVul.objects.filter(
                    Q(user_id=user_id) & Q(image_id=obj.image_id) & Q(time_model_id=time_model_id) &
                    Q(container_status='stop')
                ).first()
        
        if data:
            if not data.docker_container_id and not obj.is_docker_compose:
                data.container_status = "delete"
            
            if data.container_status == "running":
                try:
                    HTTP_HOST = request.META.get("HTTP_REFERER")
                    if HTTP_HOST and HTTP_HOST.count(":") == 2:
                        status["host"] = data.vul_host
                    elif HTTP_HOST:
                        HTTP_HOST = HTTP_HOST.replace("http://", "").replace("https://", "")
                        origin_host = data.vul_host.split(":")
                        if len(origin_host) >= 2:
                            status["host"] = HTTP_HOST[:-1] + ":" + origin_host[1]
                    else:
                        status["host"] = data.vul_host
                except Exception:
                    status["host"] = data.vul_host
                status["port"] = data.vul_port
            
            status["status"] = data.container_status
            status["container_id"] = data.container_id
        
        if obj.is_docker_compose:
            if obj.original_yml:
                status['json_yml'] = json.loads(obj.original_yml)
            else:
                status['json_yml'] = json.loads(obj.docker_compose_yml)
        
        return status

    def get_degree(self, obj):
        img_d = obj.degree
        d_list = []
        try:
            if img_d:
                img_ds = json.loads(img_d)
                if img_ds.get('HoleType'):
                    d_list += img_ds['HoleType']
                if img_ds.get('devLanguage'):
                    d_list += img_ds['devLanguage']
                if img_ds.get('devDatabase'):
                    d_list += img_ds['devDatabase']
                if img_ds.get('devClassify'):
                    d_list += img_ds['devClassify']
            return d_list
        except Exception:
            return []

    def get_HoleType(self, obj):
        return self._get_degree_field(obj, 'HoleType')

    def get_devLanguage(self, obj):
        return self._get_degree_field(obj, 'devLanguage')

    def get_devDatabase(self, obj):
        return self._get_degree_field(obj, 'devDatabase')

    def get_devClassify(self, obj):
        return self._get_degree_field(obj, 'devClassify')

    def _get_degree_field(self, obj, field_name):
        img_d = obj.degree
        try:
            if img_d:
                img_d = json.loads(img_d)
                if img_d.get(field_name):
                    return img_d[field_name]
            return []
        except Exception:
            return []

    def get_writeup_date(self, obj):
        content = obj.writeup_date
        try:
            return json.loads(content)
        except Exception:
            return ""

    def get_update_date(self, obj):
        return obj.update_date.strftime('%Y-%m-%d %H:%M:%S')

    def get_image_port(self, obj):
        image_port = obj.image_port
        try:
            if image_port:
                image_port = json.loads(image_port)
                if isinstance(image_port, list):
                    image_port = str(image_port).strip('[').strip(']')
            return image_port
        except Exception:
            return obj.image_port


class ContainerVulSerializer(serializers.ModelSerializer):
    rank = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image_id = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    vul_name = serializers.SerializerMethodField()
    vul_desc = serializers.SerializerMethodField()

    class Meta:
        model = ContainerVul
        fields = ['name', 'container_id', 'container_status', 'vul_host', 'create_date',
                  'is_check', 'is_check_date', 'rank', 'user_name', 'vul_name', 'vul_desc',
                  "image_id", 'docker_compose_path', 'is_docker_compose_correlation']

    def get_vul_name(self, obj):
        try:
            return obj.image_id.image_vul_name
        except Exception:
            return ""

    def get_vul_desc(self, obj):
        try:
            return obj.image_id.image_desc
        except Exception:
            return ""

    def get_rank(self, obj):
        try:
            return obj.image_id.rank
        except Exception:
            return ""

    def get_name(self, obj):
        try:
            if obj.image_id:
                return obj.image_id.image_name
            return ""
        except Exception:
            return ""

    def get_user_name(self, obj):
        try:
            user_info = UserProfile.objects.get(id=obj.user_id)
            return user_info.username
        except (UserProfile.DoesNotExist, Exception):
            return ""

    def get_image_id(self, obj):
        try:
            return str(obj.image_id.image_id)
        except Exception:
            return ""


class SysLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    create_date = serializers.SerializerMethodField()

    class Meta:
        model = SysLog
        fields = ['user_name', 'operation_type', 'operation_name', 'operation_value',
                  'operation_args', 'ip', 'create_date']

    def get_user_name(self, obj):
        try:
            user_info = UserProfile.objects.get(id=obj.user_id)
            return user_info.username
        except (UserProfile.DoesNotExist, Exception):
            return ""

    def get_create_date(self, obj):
        return obj.create_date.strftime('%Y-%m-%d %H:%M:%S')