from django.db.models import Q
from rest_framework import viewsets

from dockerapi.models import SysLog
from dockerapi.serializers import SysLogSerializer


class SysLogSet(viewsets.ModelViewSet):
    serializer_class = SysLogSerializer

    def get_queryset(self):
        request = self.request
        user = request.user
        query = self.request.GET.get("query", "")
        
        if user.is_superuser:
            return SysLog.objects.filter(
                Q(operation_args__contains=query) | Q(operation_name__contains=query) |
                Q(operation_type__contains=query) | Q(ip__contains=query) |
                Q(operation_value__contains=query)
            ).order_by('-create_date')
        else:
            return SysLog.objects.none()