import unittest
import requests
from tests.test_logger_utils import test_logger, TestLoggerAdapter

class TestHuggingFaceAccess(unittest.TestCase):
    """Test Hugging Face website accessibility"""
    
    @classmethod
    def setUpClass(cls):
        cls.logger = TestLoggerAdapter(test_logger, "HuggingFace访问测试")
        cls.hf_urls = [
            "https://huggingface.co"
        ]

    def test_huggingface_accessibility(self):
        """Test if Hugging Face websites are accessible"""
        for url in self.hf_urls:
            try:
                response = requests.get(url, timeout=10)
                self.assertTrue(response.status_code < 400,
                              f"HuggingFace URL {url} returned status code {response.status_code}")
                self.logger.info(f"✓ 成功访问 {url}")
            except requests.exceptions.RequestException as e:
                self.fail(f"无法访问 {url}: {str(e)}")
                self.logger.error(f"× 访问失败 {url}: {str(e)}")

if __name__ == '__main__':
    unittest.main() 