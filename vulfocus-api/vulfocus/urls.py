"""vulbox URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import re_path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from dockerapi.views import ImageInfoViewSet, ContainerVulViewSet, SysLogSet, get_setting, update_setting, TimeMoudelSet, CreateTimeTemplate, UserRank, TimeRankSet, get_timing_imgs, DashboardView, get_writeup_info, get_version, get_url_name, update_enterprise_setting, get_setting_img, get_operation_image_api
from user.views import UserRegView, UserSet, get_user_rank, LoginViewset, SendEmailViewset, ResetPasswordViewset, UpdatePassViewset, AccessLinkView, send_register_email
from user.views import get_user_info, LogoutView, MyCode, refresh_captcha, CommentView
from tasks.views import TaskSet
from network.views import NetWorkInfoViewSet
from layout_image.views import LayoutViewSet, upload_img, build_compose, show_compose, upload_file, delete_file, update_build_compose, get_scene_data, upload_zip_file, download_layout_image, download_official_website_layout,get_official_website_layout
from user.views import refresh_captcha, AccessUpdataLinkView, upload_user_img
from notice.views import NoticeViewset, publish_notice, get_notifications_count, get_public_notice, notice_detail, get_content
from dockerapi.views import get_container_status
import notifications.urls
from layout_image.views import thumbUp

router = routers.DefaultRouter()
router.register('images', ImageInfoViewSet, basename='Images')
router.register('container', ContainerVulViewSet, basename='Container')
router.register('user/register', UserRegView, basename='register')
router.register('user', UserSet, basename='user')
router.register('syslog', SysLogSet, basename="SysLog")
router.register('tasks', TaskSet, basename="TaskSet")
router.register("network", NetWorkInfoViewSet, basename="network")
router.register('layout', LayoutViewSet, basename="layout")
router.register('time', TimeMoudelSet, basename="time")
router.register('timetemp', CreateTimeTemplate, basename="timetmep")
router.register("changepassword",UpdatePassViewset,basename="changepassword")
router.register("login",LoginViewset,basename="login")
router.register("send_email",SendEmailViewset,basename="send_email")
router.register("reset_password",ResetPasswordViewset,basename="reset_password")
router.register("notice", NoticeViewset, basename="notice")
router.register("comment", CommentView, basename="comment")

urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'^user/login', TokenObtainPairView.as_view()),
    re_path(r'^user/token/refresh', TokenRefreshView.as_view()),
    re_path(r'^user/logout', LogoutView.as_view(), name="logout"),
    re_path(r'^img/dashboard', DashboardView.as_view()),
    re_path(r'^user/info', get_user_info.as_view()),
    re_path(r'^rank/user', get_user_rank.as_view()),
    re_path(r'^setting/get', get_setting),
    re_path(r'^setting/update', update_setting),
    re_path(r'^enterprise/update', update_enterprise_setting),
    re_path(r'^img/upload', upload_img),
    re_path(r'^get/urlname', get_url_name),
    re_path(r'^get/scenedata', get_scene_data),
    re_path(r'^get/website/imgs', get_timing_imgs),
    re_path(r'^get/settingimg', get_setting_img),
    re_path(r'^getcaptcha/', MyCode.as_view()),
    re_path(r'^build/compose/', build_compose),
    re_path(r'^update/compose/', update_build_compose),
    re_path(r'^show/compose/', show_compose),
    re_path(r'^file/upload/', upload_file),
    re_path(r'^file/delete/', delete_file),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r"^accesslink",AccessLinkView.as_view()),
    re_path(r'^send_register_email', send_register_email),
    re_path(r'^captcha/', include("captcha.urls")),
    re_path(r'^refresh_captcha/', refresh_captcha),
    re_path(r"^accessupdatelink",AccessUpdataLinkView.as_view()),
    re_path(r'^uploaduserimg',upload_user_img),
    re_path(r'^get_writeup', get_writeup_info),
    re_path(r'^userrank', UserRank.as_view()),
    re_path(r'^timerank', TimeRankSet.as_view()),
    re_path(r'^get_version', get_version),
    re_path(r'^inbox/notifications', include((notifications.urls, notifications))),
    re_path(r'^public_notice', publish_notice),
    re_path(r"^get_notices", get_public_notice),
    re_path(r"^notice_detail", notice_detail),
    re_path(r'^get_notifications_count',get_notifications_count),
    re_path(r"^get_content", get_content),
    re_path(r"^get_container_status",get_container_status),
    re_path(r"^upload_zip_file", upload_zip_file),
    re_path(r"^download_layout_image", download_layout_image),
    re_path(r"^download/official/website/layout", download_official_website_layout),
    re_path(r"^get/official/website/layout", get_official_website_layout),
    re_path(r"^thumbUp", thumbUp),
    re_path(r'^imgs/operation', get_operation_image_api),
]