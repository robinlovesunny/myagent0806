#!/usr/bin/env python3
"""
Web Content Agent 使用示例
演示如何在代码中使用各个模块
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.crawler.web_crawler import WebCrawler
from src.processor.content_processor import ContentProcessor
from src.prompt.prompt_manager import PromptManager
from src.formatter.output_formatter import OutputFormatter, OutputFormat


def demo_crawler():
    """演示爬虫模块使用"""
    print("=== 爬虫模块演示 ===")
    
    with WebCrawler() as crawler:
        # 爬取示例网页
        url = "https://httpbin.org/html"
        success, content, metadata = crawler.crawl_url(url)
        
        if success:
            print(f"✅ 成功爬取: {url}")
            print(f"内容长度: {len(content)} 字符")
            print(f"状态码: {metadata.get('status_code')}")
        else:
            print(f"❌ 爬取失败: {content}")


def demo_processor():
    """演示内容处理模块使用"""
    print("\n=== 内容处理模块演示 ===")
    
    # 示例HTML内容
    html_content = """
    <html>
        <head><title>测试页面</title></head>
        <body>
            <h1>这是标题</h1>
            <p>这是第一段内容，包含重要信息。</p>
            <p>这是第二段内容，提供更多详细描述。</p>
            <script>console.log('这是脚本，会被移除');</script>
        </body>
    </html>
    """
    
    processor = ContentProcessor()
    processed_data = processor.process_html(html_content)
    
    print(f"提取的标题: {processed_data['title']}")
    print(f"主要内容长度: {len(processed_data['main_content'])}")
    print(f"内容摘要: {processed_data['summary']}")


def demo_prompt_manager():
    """演示提示词管理模块使用"""
    print("\n=== 提示词管理模块演示 ===")
    
    manager = PromptManager()
    
    # 列出所有模板
    templates = manager.list_templates()
    print("可用模板:")
    for template in templates:
        print(f"  - {template['name']}: {template['description']}")
    
    # 格式化提示词
    test_content = "这是一个测试网页内容，包含一些重要信息。"
    system_prompt, user_prompt = manager.format_prompts("xiaohongshu", test_content)
    
    print(f"\n使用小红书模板格式化的提示词:")
    print(f"系统提示词长度: {len(system_prompt)} 字符")
    print(f"用户提示词: {user_prompt[:100]}...")


def demo_formatter():
    """演示输出格式化模块使用"""
    print("\n=== 输出格式化模块演示 ===")
    
    formatter = OutputFormatter()
    test_content = """
# 测试标题

这是一个测试内容，用于演示格式化功能。

## 主要特点

- 功能强大 💪
- 易于使用 ✨
- 开源免费 🎉

希望这个工具对你有帮助！
    """
    
    metadata = {
        'source_url': 'https://example.com',
        'template': 'xiaohongshu',
        'timestamp': '2024-01-01 12:00:00'
    }
    
    # 测试不同格式
    formats = [
        (OutputFormat.MARKDOWN, "Markdown"),
        (OutputFormat.HTML, "HTML"),
        (OutputFormat.TEXT, "纯文本"),
        (OutputFormat.JSON, "JSON")
    ]
    
    for format_type, format_name in formats:
        formatted = formatter.format_content(test_content, format_type, metadata)
        print(f"\n{format_name}格式输出长度: {len(formatted)} 字符")
        if format_type == OutputFormat.TEXT:
            print("纯文本格式预览:")
            print(formatted[:200] + "..." if len(formatted) > 200 else formatted)


def demo_full_workflow():
    """演示完整工作流程"""
    print("\n=== 完整工作流程演示 ===")
    
    # 1. 爬取内容
    url = "https://httpbin.org/html"
    print(f"1. 爬取网页: {url}")
    
    with WebCrawler() as crawler:
        success, html_content, crawl_metadata = crawler.crawl_url(url)
    
    if not success:
        print(f"爬取失败: {html_content}")
        return
    
    # 2. 处理内容
    print("2. 处理网页内容...")
    processor = ContentProcessor()
    readable_content = processor.extract_readable_content(html_content, url)
    
    # 3. 格式化提示词
    print("3. 格式化提示词...")
    manager = PromptManager()
    system_prompt, user_prompt = manager.format_prompts("summary", readable_content)
    
    # 4. 格式化输出（模拟AI生成的内容）
    print("4. 格式化输出...")
    ai_generated_content = "这是一个HTML测试页面的摘要。页面包含了基本的HTML结构，主要用于测试网页爬取和处理功能。"
    
    formatter = OutputFormatter()
    metadata = formatter.add_metadata(
        content=ai_generated_content,
        source_url=url,
        template="summary"
    )
    
    final_output = formatter.format_content(ai_generated_content, OutputFormat.MARKDOWN, metadata)
    
    print("✅ 完整流程执行完成！")
    print("最终输出:")
    print("-" * 50)
    print(final_output)


if __name__ == "__main__":
    print("Web Content Agent 功能演示")
    print("=" * 50)
    
    try:
        demo_crawler()
        demo_processor()
        demo_prompt_manager()
        demo_formatter()
        demo_full_workflow()
        
        print("\n🎉 所有演示完成！")
        print("\n要在实际项目中使用，请:")
        print("1. 设置阿里云百炼API密钥")
        print("2. 使用命令行工具: python main.py --api-key YOUR_KEY --url TARGET_URL")
        print("3. 或在代码中导入WebContentAgent类进行使用")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()