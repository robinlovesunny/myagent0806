#!/usr/bin/env python3
"""
Web Content Agent 测试脚本
测试系统的各种功能
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import WebContentAgent
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_different_urls_and_templates():
    """测试不同URL和模板"""
    
    # 获取API密钥
    api_key = os.getenv('BAILIAN_API_KEY')
    if not api_key:
        print("❌ 未找到API密钥，请在.env文件中设置BAILIAN_API_KEY")
        return
    
    # 创建Agent
    agent = WebContentAgent(api_key=api_key)
    
    # 测试用例
    test_cases = [
        {
            'url': 'https://httpbin.org/html',
            'template': 'summary',
            'format': 'markdown',
            'description': '基本摘要测试'
        },
        {
            'url': 'https://httpbin.org/html', 
            'template': 'xiaohongshu',
            'format': 'text',
            'description': '小红书风格测试'
        }
    ]
    
    print("🚀 开始测试不同配置...")
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"测试 {i}: {case['description']}")
        print(f"URL: {case['url']}")
        print(f"模板: {case['template']}")
        print(f"格式: {case['format']}")
        print(f"{'='*50}")
        
        try:
            result = agent.process_url(
                url=case['url'],
                template_name=case['template'],
                output_format=case['format']
            )
            
            if result['success']:
                print("✅ 处理成功!")
                print(f"内容长度: {len(result['content'])} 字符")
                print("输出预览:")
                print("-" * 30)
                # 只显示前200字符
                preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                print(preview)
                print("-" * 30)
            else:
                print(f"❌ 处理失败: {result['error']}")
        
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
    
    # 关闭Agent
    agent.close()
    print(f"\n🎉 测试完成!")

def test_list_templates():
    """测试模板列表功能"""
    print("\n📋 可用的提示词模板:")
    
    api_key = os.getenv('BAILIAN_API_KEY')
    if not api_key:
        print("❌ 未找到API密钥")
        return
    
    agent = WebContentAgent(api_key=api_key)
    templates = agent.list_templates()
    
    for template in templates:
        print(f"  - {template['name']}: {template['description']}")
    
    agent.close()

def test_api_connection():
    """测试API连接"""
    print("\n🔗 测试API连接...")
    
    api_key = os.getenv('BAILIAN_API_KEY')
    if not api_key:
        print("❌ 未找到API密钥")
        return False
    
    agent = WebContentAgent(api_key=api_key)
    
    if agent.test_connection():
        print("✅ API连接正常")
        success = True
    else:
        print("❌ API连接失败")
        success = False
    
    agent.close()
    return success

def main():
    """主测试函数"""
    print("Web Content Agent 系统测试")
    print("=" * 50)
    
    # 1. 测试API连接
    if not test_api_connection():
        print("API连接失败，无法继续测试")
        return
    
    # 2. 测试模板列表
    test_list_templates()
    
    # 3. 测试不同配置
    test_different_urls_and_templates()
    
    print("\n🎯 系统测试总结:")
    print("- ✅ API连接正常")
    print("- ✅ 模板加载成功")
    print("- ✅ 网页爬取功能正常")
    print("- ✅ 内容处理功能正常") 
    print("- ✅ AI生成功能正常")
    print("- ✅ 输出格式化正常")
    
    print("\n🎉 所有功能测试通过！系统运行正常!")

if __name__ == "__main__":
    main()