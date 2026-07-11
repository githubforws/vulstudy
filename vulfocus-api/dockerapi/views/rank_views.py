from django.http import JsonResponse
from rest_framework.views import APIView

from dockerapi.models import TimeRank, TimeTemp
from user.models import UserProfile


class UserRank(APIView):
    
    def get(self, request):
        time_id = request.GET.get("time_id", "")
        rank_list = []
        
        if time_id:
            time_temp_data = TimeTemp.objects.filter(temp_id=time_id).first()
            if time_temp_data:
                rank_list_data = TimeRank.objects.filter(
                    time_temp_id=time_id, is_join=True
                ).order_by('-rank', 'create_date')
                
                rank_list = []
                rank = 1
                for rank_data in rank_list_data:
                    user_info = UserProfile.objects.filter(id=rank_data.user_id).first()
                    rank_dict = {}
                    if user_info:
                        rank_dict['username'] = user_info.username
                        rank_dict['rank'] = rank_data.rank
                        rank_dict['rank_index'] = rank
                        rank_dict['create_date'] = str(rank_data.create_date)
                    rank_list.append(rank_dict)
                    rank += 1
        
        return JsonResponse({"code": 200, "data": rank_list})