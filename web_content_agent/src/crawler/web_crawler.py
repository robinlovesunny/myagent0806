import requests
import time
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class WebCrawler:
    """网页内容爬取器，支持反爬虫策略和错误重试"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建带有重试策略的Session"""
        session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认headers以模拟真实浏览器
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def crawl_url(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, str, Dict[str, str]]:
        """
        爬取指定URL的网页内容
        
        Args:
            url: 要爬取的网页URL
            headers: 可选的自定义headers
            
        Returns:
            Tuple[bool, str, Dict[str, str]]: (是否成功, 内容或错误信息, 响应元数据)
        """
        try:
            # 验证URL格式
            if not self._validate_url(url):
                return False, f"Invalid URL format: {url}", {}
            
            logger.info(f"开始爬取URL: {url}")
            
            # 合并自定义headers
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            # 发起请求
            response = self.session.get(
                url,
                headers=request_headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 尝试获取正确的编码
            response.encoding = response.apparent_encoding or 'utf-8'
            
            # 提取响应元数据
            metadata = {
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content_length': len(response.text),
                'final_url': response.url,
                'encoding': response.encoding
            }
            
            logger.info(f"成功爬取URL: {url}, 内容长度: {metadata['content_length']}")
            
            return True, response.text, metadata
            
        except requests.exceptions.Timeout:
            error_msg = f"请求超时: {url}"
            logger.error(error_msg)
            return False, error_msg, {}
            
        except requests.exceptions.ConnectionError:
            error_msg = f"连接错误: {url}"
            logger.error(error_msg)
            return False, error_msg, {}
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP错误 {e.response.status_code}: {url}"
            logger.error(error_msg)
            return False, error_msg, {}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
            
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def _validate_url(self, url: str) -> bool:
        """验证URL格式是否正确"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def crawl_multiple_urls(self, urls: list, delay: float = 1.0) -> Dict[str, Tuple[bool, str, Dict[str, str]]]:
        """
        批量爬取多个URL
        
        Args:
            urls: URL列表
            delay: 请求间隔时间（秒）
            
        Returns:
            Dict[str, Tuple[bool, str, Dict[str, str]]]: URL -> (是否成功, 内容或错误信息, 元数据)
        """
        results = {}
        
        for i, url in enumerate(urls):
            results[url] = self.crawl_url(url)
            
            # 添加延时避免被反爬虫
            if i < len(urls) - 1:
                time.sleep(delay)
        
        return results
    
    def close(self):
        """关闭Session"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便捷函数
def crawl_single_url(url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, str, Dict[str, str]]:
    """
    爬取单个URL的便捷函数
    
    Args:
        url: 要爬取的URL
        timeout: 超时时间
        headers: 自定义headers
        
    Returns:
        Tuple[bool, str, Dict[str, str]]: (是否成功, 内容或错误信息, 响应元数据)
    """
    with WebCrawler(timeout=timeout) as crawler:
        return crawler.crawl_url(url, headers)