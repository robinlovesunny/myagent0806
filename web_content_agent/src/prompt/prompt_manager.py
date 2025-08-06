import yaml
import json
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptTemplate:
    """提示词模板类"""
    
    def __init__(self, name: str, description: str, system_prompt: str, 
                 user_prompt: str, parameters: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.parameters = parameters or {}
    
    def format_user_prompt(self, content: str, **kwargs) -> str:
        """格式化用户提示词"""
        format_dict = {'content': content}
        format_dict.update(kwargs)
        format_dict.update(self.parameters)
        
        try:
            return self.user_prompt.format(**format_dict)
        except KeyError as e:
            logger.warning(f"提示词模板格式化失败，缺少参数: {e}")
            return self.user_prompt.replace('{content}', content)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'user_prompt': self.user_prompt,
            'parameters': self.parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """从字典创建模板"""
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            system_prompt=data.get('system_prompt', ''),
            user_prompt=data.get('user_prompt', ''),
            parameters=data.get('parameters', {})
        )


class PromptManager:
    """提示词管理器，负责管理和加载各种风格的提示词模板"""
    
    def __init__(self, templates_dir: str = "config/prompts"):
        self.templates_dir = Path(templates_dir)
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_templates()
    
    def _load_templates(self):
        """从配置目录加载所有模板"""
        if not self.templates_dir.exists():
            logger.warning(f"模板目录不存在: {self.templates_dir}")
            self._create_default_templates()
            return
        
        # 遍历模板目录，加载所有YAML和JSON文件
        for template_file in self.templates_dir.glob("*.yaml"):
            self._load_template_file(template_file)
        
        for template_file in self.templates_dir.glob("*.yml"):
            self._load_template_file(template_file)
        
        for template_file in self.templates_dir.glob("*.json"):
            self._load_template_file(template_file)
        
        if not self.templates:
            logger.info("未找到任何模板文件，创建默认模板")
            self._create_default_templates()
    
    def _load_template_file(self, file_path: Path):
        """加载单个模板文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            template = PromptTemplate.from_dict(data)
            self.templates[template.name] = template
            
            logger.info(f"成功加载模板: {template.name} from {file_path}")
            
        except Exception as e:
            logger.error(f"加载模板文件失败 {file_path}: {str(e)}")
    
    def _create_default_templates(self):
        """创建默认模板"""
        # 确保目录存在
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 小红书风格模板
        xiaohongshu_template = PromptTemplate(
            name="xiaohongshu",
            description="小红书图文风格的内容整理",
            system_prompt="""你是一个专业的内容整理助手，请将网页内容整理成小红书风格的图文内容。

要求：
- 使用活泼生动的语言风格
- 适当添加emoji表情增加趣味性
- 突出重点信息，使用小标题分段
- 保持内容的可读性和吸引力
- 字数控制在500-800字之间
- 采用第一人称视角，更亲切自然
- 适当使用流行词汇和网络用语

格式建议：
- 开头用吸引人的标题或问句
- 正文分为3-5个小段落
- 每段用emoji或小标题开头
- 结尾可以互动提问或总结""",
            user_prompt="请将以下网页内容整理成小红书风格的文案：\n\n{content}",
            parameters={"max_length": 800, "style": "casual"}
        )
        
        # 正式报告风格模板
        formal_template = PromptTemplate(
            name="formal",
            description="正式报告风格的内容整理",
            system_prompt="""你是一个专业的内容分析师，请将网页内容整理成正式的报告格式。

要求：
- 使用客观、专业的语言
- 逻辑清晰，条理分明
- 重点突出，层次分明
- 保持内容的准确性和完整性
- 字数控制在800-1200字
- 使用第三人称客观描述

格式要求：
- 标题：简洁明确
- 概述：总体介绍
- 主要内容：分点详述
- 总结：核心观点汇总""",
            user_prompt="请将以下网页内容整理成正式报告格式：\n\n{content}",
            parameters={"max_length": 1200, "style": "formal"}
        )
        
        # 简洁摘要风格模板
        summary_template = PromptTemplate(
            name="summary",
            description="简洁摘要风格的内容整理",
            system_prompt="""你是一个内容摘要专家，请将网页内容提炼成简洁的摘要。

要求：
- 提取核心要点，去除冗余信息
- 语言精练，表达准确
- 保留关键数据和重要细节
- 字数控制在300-500字
- 采用条目式或段落式结构

重点：
- 主要观点必须准确传达
- 重要数据和结论不可遗漏
- 保持原文的核心意思""",
            user_prompt="请将以下网页内容提炼成简洁摘要：\n\n{content}",
            parameters={"max_length": 500, "style": "summary"}
        )
        
        # 保存默认模板
        self.templates["xiaohongshu"] = xiaohongshu_template
        self.templates["formal"] = formal_template
        self.templates["summary"] = summary_template
        
        # 将默认模板保存到文件
        self._save_template_to_file(xiaohongshu_template)
        self._save_template_to_file(formal_template)
        self._save_template_to_file(summary_template)
    
    def _save_template_to_file(self, template: PromptTemplate):
        """将模板保存到文件"""
        try:
            file_path = self.templates_dir / f"{template.name}.yaml"
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template.to_dict(), f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"模板已保存: {template.name} -> {file_path}")
            
        except Exception as e:
            logger.error(f"保存模板失败: {str(e)}")
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """获取指定模板"""
        template = self.templates.get(template_name)
        if not template:
            logger.warning(f"未找到模板: {template_name}")
            # 返回默认的简洁摘要模板
            return self.templates.get("summary")
        return template
    
    def list_templates(self) -> List[Dict[str, str]]:
        """列出所有可用模板"""
        return [
            {
                'name': name,
                'description': template.description
            }
            for name, template in self.templates.items()
        ]
    
    def add_template(self, template: PromptTemplate, save_to_file: bool = True) -> bool:
        """添加新模板"""
        try:
            self.templates[template.name] = template
            
            if save_to_file:
                self._save_template_to_file(template)
            
            logger.info(f"成功添加模板: {template.name}")
            return True
            
        except Exception as e:
            logger.error(f"添加模板失败: {str(e)}")
            return False
    
    def remove_template(self, template_name: str) -> bool:
        """删除模板"""
        try:
            if template_name in self.templates:
                del self.templates[template_name]
                
                # 删除对应的文件
                file_path = self.templates_dir / f"{template_name}.yaml"
                if file_path.exists():
                    file_path.unlink()
                
                logger.info(f"成功删除模板: {template_name}")
                return True
            else:
                logger.warning(f"模板不存在: {template_name}")
                return False
                
        except Exception as e:
            logger.error(f"删除模板失败: {str(e)}")
            return False
    
    def create_custom_template(self, name: str, description: str, 
                             system_prompt: str, user_prompt: str,
                             parameters: Optional[Dict[str, Any]] = None) -> bool:
        """创建自定义模板"""
        template = PromptTemplate(
            name=name,
            description=description,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parameters=parameters
        )
        
        return self.add_template(template)
    
    def format_prompts(self, template_name: str, content: str, **kwargs) -> tuple[str, str]:
        """
        格式化提示词
        
        Args:
            template_name: 模板名称
            content: 要处理的内容
            **kwargs: 额外的格式化参数
            
        Returns:
            tuple[str, str]: (系统提示词, 用户提示词)
        """
        template = self.get_template(template_name)
        if not template:
            # 使用默认模板
            template = self.templates.get("summary")
            if not template:
                return ("请帮我整理以下内容", f"内容：\n{content}")
        
        system_prompt = template.system_prompt
        user_prompt = template.format_user_prompt(content, **kwargs)
        
        return system_prompt, user_prompt


# 便捷函数
def get_default_prompt_manager() -> PromptManager:
    """获取默认的提示词管理器"""
    return PromptManager()


def format_content_with_template(content: str, template_name: str = "summary", **kwargs) -> tuple[str, str]:
    """
    使用指定模板格式化内容的便捷函数
    
    Args:
        content: 要格式化的内容
        template_name: 模板名称
        **kwargs: 额外参数
        
    Returns:
        tuple[str, str]: (系统提示词, 用户提示词)
    """
    manager = get_default_prompt_manager()
    return manager.format_prompts(template_name, content, **kwargs)