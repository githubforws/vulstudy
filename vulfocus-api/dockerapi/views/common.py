import os

from dockerapi.models import SysConfig


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


class R:
    @staticmethod
    def ok(data="", msg="success"):
        return {"code": 200, "msg": msg, "data": data}

    @staticmethod
    def build(code=400, msg="error", data=""):
        return {"code": code, "msg": msg, "data": data}


def get_setting_config():
    sys_configs = SysConfig.objects.all()
    config_dict = {}
    
    for config_key in DEFAULT_CONFIG.keys():
        config_dict[config_key] = DEFAULT_CONFIG[config_key]
    
    for sys_config in sys_configs:
        if sys_config.config_key in config_dict:
            config_dict[sys_config.config_key] = sys_config.config_value
    
    config_dict['cancel_registration'] = config_dict['cancel_registration'] == '1'
    config_dict['cancel_validation'] = config_dict['cancel_validation'] == '1'
    config_dict['del_container'] = config_dict['del_container'] == '1'
    config_dict['is_synchronization'] = config_dict['is_synchronization'] == '1'
    
    return config_dict


def get_version_config():
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