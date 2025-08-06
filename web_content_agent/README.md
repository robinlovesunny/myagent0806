# Web Content Agent

基于阿里云百炼大模型的网页内容整理系统，能够智能爬取、处理和格式化网页内容，支持多种输出风格。

## 功能特性

- 🕷️ **智能网页爬取**: 支持反爬虫策略，稳定获取网页内容
- 🧠 **AI内容整理**: 基于阿里云百炼大模型，智能理解和整理内容
- 🎨 **多样化风格**: 支持小红书、正式报告、简洁摘要等多种输出风格
- 📄 **多格式输出**: 支持Markdown、HTML、纯文本、JSON等输出格式
- ⚙️ **可定制化**: 支持自定义提示词模板和输出格式
- 🚀 **精简高效**: 轻量级架构设计，部署简单

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

复制环境变量配置文件并设置API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的阿里云百炼API密钥：

```bash
BAILIAN_API_KEY=你的API密钥
```

### 3. 基本使用

```bash
# 基本使用（使用环境变量中的API密钥）
python main.py --url "https://httpbin.org/html"

# 使用命令行参数提供API密钥
python main.py --api-key sk-6fa5c228162647f1942f24244f069cee --url "https://httpbin.org/html"

# 指定输出风格和格式
python main.py --url "https://httpbin.org/html" --template xiaohongshu --format html

# 保存到文件
python main.py --url "https://httpbin.org/html" --output result.md
```

## 使用说明

### 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--api-key` | 必需 | - | 阿里云百炼API密钥 |
| `--url` | 必需 | - | 要处理的网页URL |
| `--template` | 可选 | summary | 提示词模板名称 |
| `--format` | 可选 | markdown | 输出格式 |
| `--model` | 可选 | qwen-max | 使用的模型名称 |
| `--output` | 可选 | - | 输出文件路径 |
| `--log-level` | 可选 | INFO | 日志级别 |

### 可用模板

- `xiaohongshu`: 小红书风格，活泼生动，适合社交媒体
- `formal`: 正式报告风格，客观专业
- `summary`: 简洁摘要风格，提取核心要点

### 可用格式

- `markdown`: Markdown格式（默认）
- `html`: HTML格式，包含样式
- `text`: 纯文本格式
- `json`: JSON格式，包含元数据

## 项目结构

```
web_content_agent/
├── src/                    # 源代码目录
│   ├── crawler/           # 网页爬取模块
│   ├── processor/         # 内容处理模块
│   ├── ai/               # AI客户端模块
│   ├── prompt/           # 提示词管理模块
│   └── formatter/        # 输出格式化模块
├── config/               # 配置文件目录
│   ├── settings.yaml     # 主配置文件
│   └── prompts/          # 提示词模板目录
├── main.py              # 主程序入口
├── requirements.txt     # 依赖列表
└── .env.example        # 环境变量模板
```

## 自定义模板

你可以在 `config/prompts/` 目录下创建自定义的提示词模板文件：

```yaml
name: custom_style
description: 自定义风格的内容整理
system_prompt: |
  你是一个专业的内容整理助手...
user_prompt: 请将以下网页内容整理成自定义风格的文案：

{content}
parameters:
  max_length: 1000
  style: custom
```

## API使用

除了命令行工具，你也可以在代码中直接使用：

```python
from main import WebContentAgent
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 创建Agent实例
agent = WebContentAgent(api_key=os.getenv('BAILIAN_API_KEY'))

# 处理单个URL
result = agent.process_url(
    url="https://httpbin.org/html",
    template_name="xiaohongshu",
    output_format="markdown"
)

if result['success']:
    print(result['content'])
else:
    print(f"处理失败: {result['error']}")

# 关闭资源
agent.close()
```

## 注意事项

1. **API密钥**: 请确保API密钥有效且有足够的调用额度
2. **网络访问**: 确保能够正常访问目标网站和阿里云API服务
3. **内容限制**: 超长内容会被自动截断，建议处理适中长度的网页
4. **频率限制**: 批量处理时注意API调用频率限制

## 故障排除

### 常见问题

1. **API调用失败**
   - 检查API密钥是否正确
   - 检查网络连接
   - 查看日志文件获取详细错误信息

2. **内容提取失败**
   - 目标网站可能有反爬虫机制
   - 网页内容过少或格式特殊
   - 尝试更换User-Agent或添加延迟

3. **输出格式异常**
   - 检查模板文件是否正确
   - 确认输出格式参数有效

## 开发和贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License