import re
from html import escape
from typing import Any, Dict, List


def xss_filter(text: str) -> str:
    if not text:
        return text
    
    text = escape(text)
    
    allowed_tags = [
        ('<br>', '&lt;br&gt;'),
        ('<br/>', '&lt;br/&gt;'),
        ('<br />', '&lt;br /&gt;'),
        ('<p>', '&lt;p&gt;'),
        ('</p>', '&lt;/p&gt;'),
        ('<strong>', '&lt;strong&gt;'),
        ('</strong>', '&lt;/strong&gt;'),
        ('<em>', '&lt;em&gt;'),
        ('</em>', '&lt;/em&gt;'),
    ]
    
    for safe, encoded in allowed_tags:
        text = text.replace(encoded, safe)
    
    return text


def sanitize_input(data: Any) -> Any:
    if isinstance(data, str):
        return xss_filter(data)
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data


def validate_image_name(image_name: str) -> bool:
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*(/[a-zA-Z0-9][a-zA-Z0-9._-]*)*(:[a-zA-Z0-9._-]+)?$'
    return bool(re.match(pattern, image_name))


def validate_container_name(container_name: str) -> bool:
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$'
    return bool(re.match(pattern, container_name))


def validate_ip_address(ip: str) -> bool:
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)


def validate_port(port: str) -> bool:
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except ValueError:
        return False


def validate_username(username: str) -> bool:
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{2,15}$'
    return bool(re.match(pattern, username))


def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True


def filter_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    sensitive_keys = ['password', 'pwd', 'secret', 'token', 'api_key']
    
    def filter_value(value: Any) -> Any:
        if isinstance(value, str):
            return '******'
        elif isinstance(value, dict):
            return {
                key: '******' if key.lower() in sensitive_keys else filter_value(val)
                for key, val in value.items()
            }
        elif isinstance(value, list):
            return [filter_value(item) for item in value]
        return value
    
    return filter_value(data)