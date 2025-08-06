import re
import logging
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class ContentProcessor:
    """网页内容处理器，负责HTML解析、文本提取和内容清洗"""
    
    def __init__(self, min_text_length: int = 10, max_text_length: int = 50000):
        """
        初始化内容处理器
        
        Args:
            min_text_length: 最小有效文本长度
            max_text_length: 最大文本长度限制
        """
        self.min_text_length = min_text_length
        self.max_text_length = max_text_length
        
        # 需要移除的标签
        self.remove_tags = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'advertisement', 'ads', 'sidebar', 'menu', 'comment'
        ]
        
        # 需要移除的CSS类名关键词
        self.remove_classes = [
            'nav', 'menu', 'sidebar', 'footer', 'header', 'ad', 'ads',
            'advertisement', 'comment', 'share', 'social', 'related',
            'recommend', 'popup', 'modal'
        ]
    
    def process_html(self, html_content: str, base_url: Optional[str] = None) -> Dict[str, str]:
        """
        处理HTML内容，提取结构化文本信息
        
        Args:
            html_content: 原始HTML内容
            base_url: 基础URL，用于处理相对链接
            
        Returns:
            Dict[str, str]: 包含标题、正文、摘要等信息的字典
        """
        try:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除不需要的标签
            self._remove_unwanted_elements(soup)
            
            # 提取页面信息
            result = {
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'main_content': self._extract_main_content(soup),
                'keywords': self._extract_keywords(soup),
                'links': self._extract_links(soup, base_url),
                'images': self._extract_images(soup, base_url)
            }
            
            # 生成摘要
            result['summary'] = self._generate_summary(result['main_content'])
            
            logger.info(f"内容处理完成，标题: {result['title'][:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"HTML处理失败: {str(e)}")
            return {
                'title': '',
                'description': '',
                'main_content': '',
                'summary': '',
                'keywords': '',
                'links': [],
                'images': []
            }
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup):
        """移除不需要的HTML元素"""
        # 移除指定标签
        for tag_name in self.remove_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # 移除包含特定class的元素
        for element in soup.find_all(class_=True):
            classes = element.get('class', [])
            if any(keyword in ' '.join(classes).lower() for keyword in self.remove_classes):
                element.decompose()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        # 优先级：h1 > title > og:title
        title_selectors = [
            'h1',
            'title',
            'meta[property="og:title"]',
            'meta[name="title"]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    title = element.get('content', '').strip()
                else:
                    title = element.get_text(strip=True)
                
                if title and len(title) > 3:
                    return self._clean_text(title)
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取页面描述"""
        description_selectors = [
            'meta[name="description"]',
            'meta[property="og:description"]',
            'meta[name="summary"]'
        ]
        
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                description = element.get('content', '').strip()
                if description and len(description) > 10:
                    return self._clean_text(description)
        
        return ""
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取主要内容"""
        # 优先查找常见的内容容器
        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.content',
            '.main-content',
            '.article-content',
            '.post-content',
            '.entry-content',
            '#content',
            '#main-content'
        ]
        
        main_content = ""
        
        # 尝试找到主要内容区域
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                main_content = self._extract_text_from_elements(elements)
                if len(main_content) > 100:
                    break
        
        # 如果没有找到明确的内容区域，提取body中的所有文本
        if len(main_content) < 100:
            body = soup.find('body')
            if body:
                main_content = self._extract_text_from_elements([body])
        
        # 清洗文本
        main_content = self._clean_text(main_content)
        
        # 长度限制
        if len(main_content) > self.max_text_length:
            main_content = main_content[:self.max_text_length] + "..."
        
        return main_content
    
    def _extract_text_from_elements(self, elements: List[Tag]) -> str:
        """从HTML元素中提取文本"""
        texts = []
        
        for element in elements:
            # 处理段落结构
            paragraphs = element.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            
            if paragraphs:
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) >= self.min_text_length:
                        texts.append(text)
            else:
                # 如果没有段落结构，直接提取文本
                text = element.get_text(strip=True)
                if text:
                    texts.append(text)
        
        return '\n'.join(texts)
    
    def _extract_keywords(self, soup: BeautifulSoup) -> str:
        """提取关键词"""
        keywords_selectors = [
            'meta[name="keywords"]',
            'meta[property="article:tag"]'
        ]
        
        keywords = []
        
        for selector in keywords_selectors:
            elements = soup.select(selector)
            for element in elements:
                content = element.get('content', '').strip()
                if content:
                    keywords.extend([kw.strip() for kw in content.split(',')])
        
        return ', '.join(keywords[:10])  # 限制关键词数量
    
    def _extract_links(self, soup: BeautifulSoup, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        """提取页面链接"""
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '').strip()
            text = a_tag.get_text(strip=True)
            
            if href and text:
                # 处理相对链接
                if base_url and not href.startswith(('http://', 'https://', '#')):
                    href = urljoin(base_url, href)
                
                links.append({
                    'url': href,
                    'text': text[:100]  # 限制链接文本长度
                })
                
                # 限制链接数量
                if len(links) >= 50:
                    break
        
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        """提取页面图片"""
        images = []
        
        for img_tag in soup.find_all('img', src=True):
            src = img_tag.get('src', '').strip()
            alt = img_tag.get('alt', '').strip()
            
            if src:
                # 处理相对链接
                if base_url and not src.startswith(('http://', 'https://', 'data:')):
                    src = urljoin(base_url, src)
                
                images.append({
                    'url': src,
                    'alt': alt[:100]  # 限制alt文本长度
                })
                
                # 限制图片数量
                if len(images) >= 20:
                    break
        
        return images
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成内容摘要"""
        if not content or len(content) < 50:
            return content
        
        # 分句
        sentences = re.split(r'[.!?。！？]', content)
        
        summary = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                if len(summary + sentence) > max_length:
                    break
                summary += sentence + "。"
        
        return summary.strip()
    
    def _clean_text(self, text: str) -> str:
        """清洗文本内容"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    def extract_readable_content(self, html_content: str, base_url: Optional[str] = None) -> str:
        """
        提取可读性强的纯文本内容
        
        Args:
            html_content: 原始HTML内容
            base_url: 基础URL
            
        Returns:
            str: 清洗后的纯文本内容
        """
        processed_content = self.process_html(html_content, base_url)
        
        # 组合主要信息
        readable_parts = []
        
        if processed_content['title']:
            readable_parts.append(f"标题: {processed_content['title']}")
        
        if processed_content['description']:
            readable_parts.append(f"描述: {processed_content['description']}")
        
        if processed_content['main_content']:
            readable_parts.append(f"正文内容:\n{processed_content['main_content']}")
        
        return '\n\n'.join(readable_parts)


# 便捷函数
def extract_content_from_html(html_content: str, base_url: Optional[str] = None) -> str:
    """
    从HTML中提取纯文本内容的便捷函数
    
    Args:
        html_content: HTML内容
        base_url: 基础URL
        
    Returns:
        str: 提取的纯文本内容
    """
    processor = ContentProcessor()
    return processor.extract_readable_content(html_content, base_url)