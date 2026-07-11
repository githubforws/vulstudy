import json
import os
import re

from django.db import transaction
from typing import Dict, Any

from dockerapi.models import SysConfig, ImageInfo, ContainerVul
from dockerapi.serializers import ImageInfoSerializer



DEFAULT_CONFIG = {
    "username": "admin",
    "pwd": "admin",
    "time": "3600",
    "share_username": "",
    "is_synchronization": "0",
    "del_container": "0",
    "url_name": "vulfocus",
    "cancel_validation": "0",
    "cancel_registration": "0",
    "enterprise_bg": "",
    "enterprise_logo": "",
}


class SettingService:
    
    @staticmethod
    def get_config() -> Dict:
        sys_configs = SysConfig.objects.all()
        config_dict = {}
        
        for config_key in DEFAULT_CONFIG.keys():
            config_dict[config_key] = DEFAULT_CONFIG[config_key]
        
        for sys_config in sys_configs:
            if sys_config.config_key in config_dict:
                config_dict[sys_config.config_key] = sys_config.config_value
        
        return config_dict
    
    @staticmethod
    def get_version() -> Dict:
        version_config = {}
        
        try:
            version_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "VERSION")
            if os.path.exists(version_file_path):
                with open(version_file_path, 'r') as f:
                    version_config["version"] = f.read().strip()
            else:
                version_config["version"] = "2.3.0"
        except:
            version_config["version"] = "2.3.0"
        
        version_config["github_url"] = "https://github.com/fofapro/vulfocus"
        
        return version_config
    
    @staticmethod
    def update_config(data: Dict) -> Dict:
        username = data.get("username")
        if not username:
            return {"success": False, "message": "用户名不能为空"}
        
        pwd = data.get("pwd", DEFAULT_CONFIG["pwd"])
        if not pwd:
            return {"success": False, "message": "密码不能为空"}
        
        time = data.get("time")
        share_username = data.get("share_username")
        
        if not share_username:
            return {"success": False, "message": "分享用户名不能为空"}
        
        share_username_reg = "[\da-zA-z\-]+"
        if not re.match(share_username_reg, share_username):
            return {"success": False, "message": "分享用户名不符合要求"}
        
        is_synchronization = data.get("is_synchronization")
        cancel_validation = data.get("cancel_validation")
        cancel_registration = data.get("cancel_registration")
        del_container = data.get("del_container")
        url_name = data.get("url_name")
        
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
        
        try:
            with transaction.atomic():
                for config_key, config_value in configs:
                    config, created = SysConfig.objects.get_or_create(
                        config_key=config_key,
                        defaults={'config_value': DEFAULT_CONFIG.get(config_key, "")}
                    )
                    if config.config_value != str(config_value):
                        config.config_value = str(config_value)
                        config.save()
        except Exception as e:
            return {"success": False, "message": f"修改失败: {str(e)}"}
        
        return {"success": True, "message": "修改成功", "data": SettingService.get_config()}
    
    @staticmethod
    def update_enterprise_config(data: Dict) -> Dict:
        url_name = data.get("url_name")
        enterprise_bg = data.get("enterprise_bg", "")
        enterprise_logo = data.get("enterprise_logo", "")
        
        if not url_name:
            url_name = 'vulfocus'
        
        try:
            with transaction.atomic():
                for config_key, config_value in [
                    ("url_name", str(url_name)),
                    ("enterprise_bg", str(enterprise_bg)),
                    ("enterprise_logo", str(enterprise_logo)),
                ]:
                    config, created = SysConfig.objects.get_or_create(
                        config_key=config_key,
                        defaults={'config_value': DEFAULT_CONFIG.get(config_key, "")}
                    )
                    if config.config_value != str(config_value):
                        config.config_value = str(config_value)
                        config.save()
        except:
            return {"success": False, "message": "修改失败"}
        
        return {"success": True, "message": "修改成功", "data": SettingService.get_config()}
    
    @staticmethod
    def get_writeup_info(image_id: str) -> Dict:
        writeup_date = ""
        
        if image_id:
            img_info = ImageInfo.objects.filter(image_id=image_id).first()
            if img_info:
                if img_info.writeup_date:
                    writeup_date = json.loads(img_info.writeup_date)
        
        return {"username": '', "writeup_date": writeup_date}
    
    @staticmethod
    def get_setting_img() -> list:
        img_list = []
        container_vul_list = ContainerVul.objects.filter(container_status="running")
        for container_vul in container_vul_list:
            image_info = ImageInfo.objects.filter(image_id=container_vul.image_id_id).first()
            if image_info:
                img_list.append(ImageInfoSerializer(image_info).data)
        return img_list
    
    @staticmethod
    def get_container_status(container_id: str) -> str:
        container_vul = ContainerVul.objects.filter(container_id=container_id).first()
        if container_vul:
            return container_vul.container_status
        else:
            return "stop"
    
    @staticmethod
    def get_operation_image_api(image_name: str) -> Dict:
        image_info = ImageInfo.objects.filter(image_name=image_name).first()
        if image_info:
            return ImageInfoSerializer(image_info).data
        else:
            return ""