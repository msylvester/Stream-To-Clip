# test_video_options.py
import unittest
from server import app
import json
from unittest.mock import patch, MagicMock

class TestVideoOptions(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_no_url(self):
        """Test when no URL is provided"""
        response = self.client.post('/api/get-video-options', json={})
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'URL is required')

    def test_success(self):
        """Test successful video options retrieval"""
        test_url = "https://www.twitch.tv/videos/12345"
        mock_output = """
        Available qualities:
        1080p60 (source)
        720p60
        720p
        480p
        360p
        160p
        144p
        """
        
        with patch('subprocess.run') as mock_run:
            mock_process = MagicMock()
            mock_process.stdout = mock_output
            mock_process.stderr = ""
            mock_run.return_value = mock_process
            
            response = self.client.post('/api/get-video-options', 
                                      json={'url': test_url})
            
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['success'])
            self.assertIn('qualities', data)
            self.assertGreater(len(data['qualities']), 0)
            self.assertIn('raw_output', data)

    def test_command_failure(self):
        """Test when twitchdl command fails"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Command failed')
            
            response = self.client.post('/api/get-video-options', 
                                      json={'url': 'https://www.twitch.tv/videos/12345'})
            
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 500)
            self.assertIn('error', data)
            self.assertIn('Server error', data['error'])

if __name__ == '__main__':
    unittest.main()
