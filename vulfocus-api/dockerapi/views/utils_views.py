import socket
from typing import Optional

from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request

from vulfocus.settings import VUL_IP


class MyPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    page_query_param = "page"


def get_request_ip(request: Request) -> str:
    request_ip = request.META.get("HTTP_X_REAL_IP", "")
    if not request_ip:
        request_ip = request.META.get("REMOTE_ADDR", "")
    return request_ip


def get_local_ip() -> str:
    if VUL_IP:
        return VUL_IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    finally:
        s.close()