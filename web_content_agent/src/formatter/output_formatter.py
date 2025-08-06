import re
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import html

logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """输出格式枚举"""
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    JSON = "json"


class OutputFormatter:
    """输出格式化器，负责将AI生成的内容格式化为不同的输出格式"""
    
    def __init__(self, default_format: OutputFormat = OutputFormat.MARKDOWN):
        self.default_format = default_format
    
    def format_content(self, content: str, format_type: OutputFormat = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        格式化内容
        
        Args:
            content: 要格式化的内容
            format_type: 输出格式类型
            metadata: 元数据信息
            
        Returns:
            str: 格式化后的内容
        """
        if format_type is None:
            format_type = self.default_format
        
        try:
            if format_type == OutputFormat.MARKDOWN:
                return self._format_as_markdown(content, metadata)
            elif format_type == OutputFormat.HTML:
                return self._format_as_html(content, metadata)
            elif format_type == OutputFormat.TEXT:
                return self._format_as_text(content, metadata)
            elif format_type == OutputFormat.JSON:
                return self._format_as_json(content, metadata)
            else:
                logger.warning(f"未知的格式类型: {format_type}，使用默认格式")
                return self._format_as_markdown(content, metadata)
                
        except Exception as e:
            logger.error(f"内容格式化失败: {str(e)}")
            return content  # 返回原始内容
    
    def _format_as_markdown(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """格式化为Markdown格式"""
        result = []
        
        # 添加元数据头部
        if metadata:
            result.append("---")
            if metadata.get('source_url'):
                result.append(f"**来源**: {metadata['source_url']}")
            if metadata.get('timestamp'):
                result.append(f"**生成时间**: {metadata['timestamp']}")
            if metadata.get('template'):
                result.append(f"**风格模板**: {metadata['template']}")
            result.append("---\n")
        
        # 处理主要内容
        formatted_content = self._enhance_markdown_formatting(content)
        result.append(formatted_content)
        
        # 添加统计信息
        if metadata and any(key in metadata for key in ['word_count', 'char_count']):
            result.append("\n---")
            result.append("**统计信息**")
            if metadata.get('word_count'):
                result.append(f"- 字数: {metadata['word_count']}")
            if metadata.get('char_count'):
                result.append(f"- 字符数: {metadata['char_count']}")
        
        return '\n'.join(result)
    
    def _format_as_html(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """格式化为HTML格式"""
        html_parts = []
        
        # HTML头部
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="zh-CN">')
        html_parts.append('<head>')
        html_parts.append('    <meta charset="UTF-8">')
        html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append('    <title>网页内容整理结果</title>')
        html_parts.append('    <style>')
        html_parts.append(self._get_html_styles())
        html_parts.append('    </style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        
        # 元数据信息
        if metadata:
            html_parts.append('    <div class="metadata">')
            html_parts.append('        <h3>📋 信息概览</h3>')
            if metadata.get('source_url'):
                html_parts.append(f'        <p><strong>来源:</strong> <a href="{metadata["source_url"]}" target="_blank">{metadata["source_url"]}</a></p>')
            if metadata.get('timestamp'):
                html_parts.append(f'        <p><strong>生成时间:</strong> {metadata["timestamp"]}</p>')
            if metadata.get('template'):
                html_parts.append(f'        <p><strong>风格模板:</strong> {metadata["template"]}</p>')
            html_parts.append('    </div>')
        
        # 主要内容
        html_parts.append('    <div class="content">')
        formatted_content = self._convert_markdown_to_html(content)
        html_parts.append(f'        {formatted_content}')
        html_parts.append('    </div>')
        
        # 统计信息
        if metadata and any(key in metadata for key in ['word_count', 'char_count']):
            html_parts.append('    <div class="stats">')
            html_parts.append('        <h3>📊 统计信息</h3>')
            if metadata.get('word_count'):
                html_parts.append(f'        <span class="stat-item">字数: {metadata["word_count"]}</span>')
            if metadata.get('char_count'):
                html_parts.append(f'        <span class="stat-item">字符数: {metadata["char_count"]}</span>')
            html_parts.append('    </div>')
        
        # HTML尾部
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
    
    def _format_as_text(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """格式化为纯文本格式"""
        result = []
        
        # 添加分隔线
        result.append("=" * 80)
        result.append("网页内容整理结果")
        result.append("=" * 80)
        
        # 元数据信息
        if metadata:
            result.append("")
            result.append("【信息概览】")
            if metadata.get('source_url'):
                result.append(f"来源: {metadata['source_url']}")
            if metadata.get('timestamp'):
                result.append(f"生成时间: {metadata['timestamp']}")
            if metadata.get('template'):
                result.append(f"风格模板: {metadata['template']}")
        
        # 主要内容
        result.append("")
        result.append("【整理内容】")
        result.append("-" * 50)
        
        # 清理内容中的Markdown标记
        clean_content = self._remove_markdown_formatting(content)
        result.append(clean_content)
        
        # 统计信息
        if metadata and any(key in metadata for key in ['word_count', 'char_count']):
            result.append("")
            result.append("-" * 50)
            result.append("【统计信息】")
            if metadata.get('word_count'):
                result.append(f"字数: {metadata['word_count']}")
            if metadata.get('char_count'):
                result.append(f"字符数: {metadata['char_count']}")
        
        result.append("=" * 80)
        
        return '\n'.join(result)
    
    def _format_as_json(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """格式化为JSON格式"""
        data = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "format": "json"
        }
        
        if metadata:
            data["metadata"] = metadata
        
        # 计算内容统计
        data["statistics"] = {
            "character_count": len(content),
            "word_count": len(content.split()),
            "line_count": len(content.split('\n'))
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _enhance_markdown_formatting(self, content: str) -> str:
        """增强Markdown格式"""
        # 确保标题格式正确
        content = re.sub(r'^([^#\n].*?)$', r'\1', content, flags=re.MULTILINE)
        
        # 添加适当的段落间距
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 确保emoji后有空格
        content = re.sub(r'([^\s])([🎉🔥💡📝🎯✨👍💪🚀🌟⭐])', r'\1 \2', content)
        
        return content.strip()
    
    def _convert_markdown_to_html(self, content: str) -> str:
        """简单的Markdown到HTML转换"""
        # 转义HTML字符
        content = html.escape(content)
        
        # 转换标题
        content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        
        # 转换加粗
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        
        # 转换斜体
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        
        # 转换段落
        paragraphs = content.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # 检查是否已经是HTML标签
                if not re.match(r'^<[hH][1-6]>', para):
                    para = f'<p>{para.replace(chr(10), "<br>")}</p>'
                html_paragraphs.append(para)
        
        return '\n'.join(html_paragraphs)
    
    def _remove_markdown_formatting(self, content: str) -> str:
        """移除Markdown格式标记"""
        # 移除标题标记
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
        
        # 移除加粗标记
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        
        # 移除斜体标记
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        
        # 移除链接标记
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        
        return content
    
    def _get_html_styles(self) -> str:
        """获取HTML样式"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .metadata {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        
        .metadata h3 {
            margin-top: 0;
            color: #1976d2;
        }
        
        .content {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .content h1, .content h2, .content h3 {
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        
        .content p {
            margin-bottom: 15px;
            text-align: justify;
        }
        
        .stats {
            background: #f1f8e9;
            border-left: 4px solid #8bc34a;
            padding: 15px;
            border-radius: 4px;
        }
        
        .stats h3 {
            margin-top: 0;
            color: #689f38;
        }
        
        .stat-item {
            display: inline-block;
            background: #dcedc8;
            padding: 5px 10px;
            border-radius: 15px;
            margin-right: 10px;
            font-size: 14px;
        }
        
        a {
            color: #1976d2;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
        """
    
    def add_metadata(self, content: str, source_url: str = None, 
                    template: str = None, **kwargs) -> Dict[str, Any]:
        """
        添加内容元数据
        
        Args:
            content: 内容文本
            source_url: 源URL
            template: 使用的模板
            **kwargs: 其他元数据
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'char_count': len(content),
            'word_count': len(content.split()),
            'line_count': len(content.split('\n'))
        }
        
        if source_url:
            metadata['source_url'] = source_url
        
        if template:
            metadata['template'] = template
        
        # 添加其他自定义元数据
        metadata.update(kwargs)
        
        return metadata
    
    def format_with_template(self, content: str, template_name: str,
                           source_url: str = None, output_format: OutputFormat = None) -> str:
        """
        使用指定模板格式化内容
        
        Args:
            content: 内容
            template_name: 模板名称
            source_url: 源URL
            output_format: 输出格式
            
        Returns:
            str: 格式化后的内容
        """
        metadata = self.add_metadata(
            content=content,
            source_url=source_url,
            template=template_name
        )
        
        return self.format_content(content, output_format, metadata)


# 便捷函数
def format_content_output(content: str, format_type: str = "markdown",
                         metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    格式化内容输出的便捷函数
    
    Args:
        content: 要格式化的内容
        format_type: 格式类型 ("markdown", "html", "text", "json")
        metadata: 元数据
        
    Returns:
        str: 格式化后的内容
    """
    formatter = OutputFormatter()
    
    # 转换格式类型
    format_enum = OutputFormat.MARKDOWN
    if format_type.lower() == "html":
        format_enum = OutputFormat.HTML
    elif format_type.lower() == "text":
        format_enum = OutputFormat.TEXT
    elif format_type.lower() == "json":
        format_enum = OutputFormat.JSON
    
    return formatter.format_content(content, format_enum, metadata)