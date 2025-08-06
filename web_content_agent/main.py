#!/usr/bin/env python3
"""
Web Content Agent 主程序
基于阿里云百炼大模型的网页内容整理系统
"""

import os
import sys
import logging
import argparse
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crawler.web_crawler import WebCrawler
from src.processor.content_processor import ContentProcessor
from src.prompt.prompt_manager import PromptManager
from src.ai.bailian_client import BailianClient, BailianConfig
from src.formatter.output_formatter import OutputFormatter, OutputFormat


class WebContentAgent:
    """网页内容整理Agent主类"""
    
    def __init__(self, api_key: str, model: str = "qwen-max", 
                 templates_dir: str = "config/prompts"):
        """
        初始化Agent
        
        Args:
            api_key: 阿里云百炼API密钥
            model: 使用的模型名称
            templates_dir: 提示词模板目录
        """
        self.api_key = api_key
        self.model = model
        
        # 初始化各个模块
        self.crawler = WebCrawler()
        self.processor = ContentProcessor()
        self.prompt_manager = PromptManager(templates_dir)
        self.formatter = OutputFormatter()
        
        # 初始化AI客户端
        config = BailianConfig(
            api_key=api_key,
            model=model,
            temperature=0.7,
            max_tokens=2000
        )
        self.ai_client = BailianClient(config)
        
        self.logger = logging.getLogger(__name__)
    
    def process_url(self, url: str, template_name: str = "summary",
                   output_format: str = "markdown", **kwargs) -> Dict[str, Any]:
        """
        处理单个URL
        
        Args:
            url: 要处理的网页URL
            template_name: 使用的提示词模板
            output_format: 输出格式
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        result = {
            'success': False,
            'url': url,
            'template': template_name,
            'output_format': output_format,
            'content': '',
            'error': '',
            'metadata': {}
        }
        
        try:
            self.logger.info(f"开始处理URL: {url}")
            
            # 1. 爬取网页内容
            self.logger.info("正在爬取网页内容...")
            crawl_success, html_content, crawl_metadata = self.crawler.crawl_url(url)
            
            if not crawl_success:
                result['error'] = f"网页爬取失败: {html_content}"
                return result
            
            self.logger.info(f"网页爬取成功，内容长度: {len(html_content)}")
            
            # 2. 处理和清洗内容
            self.logger.info("正在处理网页内容...")
            readable_content = self.processor.extract_readable_content(html_content, url)
            
            if not readable_content or len(readable_content.strip()) < 50:
                result['error'] = "提取的内容过短或为空"
                return result
            
            self.logger.info(f"内容处理完成，文本长度: {len(readable_content)}")
            
            # 3. 获取提示词模板
            self.logger.info(f"获取提示词模板: {template_name}")
            system_prompt, user_prompt = self.prompt_manager.format_prompts(
                template_name, readable_content, **kwargs
            )
            
            # 4. 调用AI生成内容
            self.logger.info("正在生成整理内容...")
            ai_success, generated_content, ai_metadata = self.ai_client.generate_text(
                system_prompt, user_prompt, **kwargs
            )
            
            if not ai_success:
                result['error'] = f"AI内容生成失败: {generated_content}"
                return result
            
            self.logger.info(f"内容生成成功，长度: {len(generated_content)}")
            
            # 5. 格式化输出
            self.logger.info(f"格式化输出: {output_format}")
            
            # 合并元数据
            metadata = self.formatter.add_metadata(
                content=generated_content,
                source_url=url,
                template=template_name
            )
            # 手动添加其他元数据避免参数冲突
            metadata.update(crawl_metadata)
            metadata.update(ai_metadata)
            
            # 确定输出格式
            format_enum = OutputFormat.MARKDOWN
            if output_format.lower() == "html":
                format_enum = OutputFormat.HTML
            elif output_format.lower() == "text":
                format_enum = OutputFormat.TEXT
            elif output_format.lower() == "json":
                format_enum = OutputFormat.JSON
            
            formatted_content = self.formatter.format_content(
                generated_content, format_enum, metadata
            )
            
            # 6. 返回结果
            result.update({
                'success': True,
                'content': formatted_content,
                'raw_content': generated_content,
                'metadata': metadata
            })
            
            self.logger.info(f"URL处理完成: {url}")
            return result
            
        except Exception as e:
            error_msg = f"处理过程中发生异常: {str(e)}"
            self.logger.error(error_msg)
            result['error'] = error_msg
            return result
    
    def process_multiple_urls(self, urls: list, template_name: str = "summary",
                            output_format: str = "markdown", **kwargs) -> Dict[str, Dict[str, Any]]:
        """
        批量处理多个URL
        
        Args:
            urls: URL列表
            template_name: 使用的提示词模板
            output_format: 输出格式
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Dict[str, Any]]: 每个URL的处理结果
        """
        results = {}
        
        for i, url in enumerate(urls):
            self.logger.info(f"处理URL {i+1}/{len(urls)}: {url}")
            results[url] = self.process_url(url, template_name, output_format, **kwargs)
        
        return results
    
    def list_templates(self) -> list:
        """列出所有可用的提示词模板"""
        return self.prompt_manager.list_templates()
    
    def test_connection(self) -> bool:
        """测试AI服务连接"""
        success, message = self.ai_client.test_connection()
        if success:
            self.logger.info("AI服务连接正常")
        else:
            self.logger.error(f"AI服务连接失败: {message}")
        return success
    
    def save_result_to_file(self, result: Dict[str, Any], output_file: str):
        """将结果保存到文件"""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result['content'])
            
            self.logger.info(f"结果已保存到: {output_path}")
            
        except Exception as e:
            self.logger.error(f"保存文件失败: {str(e)}")
    
    def close(self):
        """关闭所有资源"""
        if hasattr(self, 'crawler'):
            self.crawler.close()
        if hasattr(self, 'ai_client'):
            self.ai_client.close()


def setup_logging(log_level: str = "INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('web_content_agent.log', encoding='utf-8')
        ]
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="网页内容整理Agent")
    
    # 可选参数 - API密钥可以从环境变量获取
    parser.add_argument("--api-key", help="阿里云百炼API密钥（可从环境变量 BAILIAN_API_KEY 获取）")
    parser.add_argument("--url", required=True, help="要处理的网页URL")
    
    # 可选参数
    parser.add_argument("--template", default="summary", help="提示词模板名称 (默认: summary)")
    parser.add_argument("--format", default="markdown", choices=["markdown", "html", "text", "json"], 
                       help="输出格式 (默认: markdown)")
    parser.add_argument("--model", default="qwen-max", help="使用的模型名称 (默认: qwen-max)")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="日志级别 (默认: INFO)")
    
    # 解析参数
    args = parser.parse_args()
    
    # 获取API密钥：优先使用命令行参数，其次使用环境变量
    api_key = args.api_key or os.getenv('BAILIAN_API_KEY')
    if not api_key:
        print("❌ 错误：未找到API密钥！")
        print("请通过以下方式之一提供API密钥：")
        print("1. 使用命令行参数：--api-key YOUR_API_KEY")
        print("2. 设置环境变量：export BAILIAN_API_KEY=YOUR_API_KEY")
        print("3. 在 .env 文件中设置：BAILIAN_API_KEY=YOUR_API_KEY")
        return 1
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # 创建Agent实例
        logger.info("初始化Web Content Agent...")
        agent = WebContentAgent(
            api_key=api_key,
            model=args.model
        )
        
        # 测试连接
        logger.info("测试AI服务连接...")
        if not agent.test_connection():
            logger.error("AI服务连接失败，请检查API密钥和网络连接")
            return 1
        
        # 处理URL
        logger.info(f"开始处理URL: {args.url}")
        result = agent.process_url(
            url=args.url,
            template_name=args.template,
            output_format=args.format
        )
        
        if result['success']:
            # 输出结果
            if args.output:
                agent.save_result_to_file(result, args.output)
            else:
                print("\n" + "="*80)
                print("整理结果:")
                print("="*80)
                print(result['content'])
                print("="*80)
            
            logger.info("处理完成")
        else:
            logger.error(f"处理失败: {result['error']}")
            return 1
        
        # 关闭资源
        agent.close()
        return 0
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        return 1
    except Exception as e:
        logger.error(f"程序执行异常: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())