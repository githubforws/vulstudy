import unittest
from unittest.mock import Mock, patch

from django.test import TestCase
from django.db.models import Q

from dockerapi.services.image_service import ImageService
from dockerapi.services.container_service import ContainerService
from dockerapi.services.setting_service import SettingService
from dockerapi.models import ImageInfo, ContainerVul, SysConfig
from user.models import UserProfile


class ImageServiceTest(TestCase):
    
    def setUp(self):
        self.user = Mock()
        self.user.username = 'test_user'
        self.user.id = 1
        self.user.is_superuser = False
        
        self.user_profile = Mock()
        self.user_profile.greenhand = False
        
        ImageInfo.objects.create(
            image_name='test_image:latest',
            image_vul_name='Test Vul',
            image_desc='Test description',
            rank=2.5,
            is_ok=True
        )
    
    def test_search_docker_hub(self):
        with patch('dockerapi.services.image_service.requests') as mock_requests:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "summaries": [{"name": "vulfocus/test"}]
            }
            mock_requests.get.return_value = mock_response
            
            result = ImageService.search_docker_hub('test')
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['name'], 'vulfocus/test')
    
    def test_get_local_images(self):
        with patch('dockerapi.services.image_service.client') as mock_client:
            mock_image = Mock()
            mock_image.tags = ['test_image:latest']
            mock_client.images.list.return_value = [mock_image]
            
            result = ImageService.get_local_images()
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['name'], 'test_image:latest')


class SettingServiceTest(TestCase):
    
    def test_get_config_default(self):
        config = SettingService.get_config()
        self.assertIn('username', config)
        self.assertEqual(config['username'], 'admin')
    
    def test_update_config(self):
        data = {
            'username': 'new_admin',
            'pwd': 'new_password',
            'time': '3600',
            'share_username': 'test_share'
        }
        result = SettingService.update_config(data)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['username'], 'new_admin')


class ContainerServiceTest(TestCase):
    
    def test_get_containers(self):
        user = Mock()
        user.id = 1
        user.is_superuser = False
        
        containers = ContainerService.get_containers(user)
        self.assertIsInstance(containers, list)


if __name__ == '__main__':
    unittest.main()