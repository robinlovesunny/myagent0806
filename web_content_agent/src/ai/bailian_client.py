import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class BailianConfig:
    """百炼API配置"""
    api_key: str
    endpoint: Optional[str] = None
    model: str = "qwen-max"
    max_retries: int = 3
    timeout: int = 60
    temperature: float = 0.7
    max_tokens: int = 2000


class BailianClient:
    """阿里云百炼大模型客户端"""
    
    def __init__(self, config: BailianConfig):
        self.config = config
        self.session = self._create_session()
        
        # API端点设置
        if config.endpoint:
            self.base_url = config.endpoint.rstrip('/')
        else:
            self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        
        # 验证配置
        self._validate_config()
    
    def _create_session(self) -> requests.Session:
        """创建带重试策略的HTTP会话"""
        session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=self.config.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置请求头
        session.headers.update({
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        return session
    
    def _validate_config(self):
        """验证配置有效性"""
        if not self.config.api_key:
            raise ValueError("API密钥不能为空")
        
        if not self.config.model:
            raise ValueError("模型名称不能为空")
    
    def generate_text(self, system_prompt: str, user_prompt: str, 
                     **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
        """
        生成文本内容
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            **kwargs: 其他参数覆盖
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (是否成功, 生成的文本, 响应元数据)
        """
        try:
            # 构建请求参数
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": user_prompt
            })
            
            # 合并参数
            params = {
                "model": self.config.model,
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "top_p": kwargs.get("top_p", 0.8),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
                }
            }
            
            logger.info(f"发送请求到百炼API，模型: {self.config.model}")
            
            # 发起请求
            response = self._make_request("/services/aigc/text-generation/generation", params)
            
            if not response:
                return False, "API请求失败", {}
            
            # 解析响应
            success, text, metadata = self._parse_response(response)
            
            if success:
                logger.info(f"文本生成成功，长度: {len(text)}")
            else:
                logger.error(f"文本生成失败: {text}")
            
            return success, text, metadata
            
        except Exception as e:
            error_msg = f"文本生成异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def generate_text_stream(self, system_prompt: str, user_prompt: str,
                           callback=None, **kwargs):
        """
        流式生成文本内容
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            callback: 回调函数，接收生成的文本片段
            **kwargs: 其他参数
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "top_p": kwargs.get("top_p", 0.8),
                "stream": True,
                "incremental_output": True
            }
            
            logger.info(f"开始流式生成，模型: {self.config.model}")
            
            # 流式请求
            response = self.session.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                json=params,
                timeout=self.config.timeout,
                stream=True
            )
            
            response.raise_for_status()
            
            full_text = ""
            
            # 处理流式响应
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data_str = line[6:]  # 移除"data: "前缀
                    
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        if "output" in data and "text" in data["output"]:
                            chunk_text = data["output"]["text"]
                            full_text = chunk_text  # 百炼API返回的是累积文本
                            
                            if callback:
                                callback(chunk_text)
                        
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"流式生成完成，总长度: {len(full_text)}")
            return True, full_text, {"stream": True}
            
        except Exception as e:
            error_msg = f"流式生成异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, {}
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[requests.Response]:
        """发起API请求"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            response = self.session.post(
                url,
                json=params,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应状态码: {e.response.status_code}")
                logger.error(f"响应内容: {e.response.text}")
            return None
        
        except Exception as e:
            logger.error(f"请求异常: {str(e)}")
            return None
    
    def _parse_response(self, response: requests.Response) -> Tuple[bool, str, Dict[str, Any]]:
        """解析API响应"""
        try:
            data = response.json()
            
            # 提取响应元数据
            metadata = {
                "status_code": response.status_code,
                "request_id": data.get("request_id", ""),
                "model": self.config.model
            }
            
            # 检查是否有输出
            if "output" not in data:
                return False, "响应中无output字段", metadata
            
            output = data["output"]
            
            # 提取生成的文本
            if "text" in output:
                text = output["text"].strip()
                
                # 添加使用信息到元数据
                if "usage" in data:
                    usage = data["usage"]
                    metadata.update({
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    })
                
                return True, text, metadata
            else:
                return False, "响应输出中无文本内容", metadata
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            return False, f"响应解析失败: {str(e)}", {"status_code": response.status_code}
        
        except Exception as e:
            logger.error(f"响应处理异常: {str(e)}")
            return False, f"响应处理异常: {str(e)}", {"status_code": response.status_code}
    
    def test_connection(self) -> Tuple[bool, str]:
        """测试API连接"""
        try:
            success, text, metadata = self.generate_text(
                system_prompt="你是一个测试助手。",
                user_prompt="请回复：连接成功",
                max_tokens=50
            )
            
            if success and "连接成功" in text:
                return True, "API连接正常"
            elif success:
                return True, f"API连接正常，响应: {text[:100]}"
            else:
                return False, f"API连接失败: {text}"
                
        except Exception as e:
            return False, f"连接测试异常: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表（这是一个示例方法，实际需要根据百炼API文档实现）"""
        # 百炼常用模型
        return [
            "qwen-max",
            "qwen-max-1201", 
            "qwen-plus",
            "qwen-turbo",
            "qwen-max-longcontext"
        ]
    
    def estimate_tokens(self, text: str) -> int:
        """估算文本token数量（简单估算）"""
        # 简单估算：中文按字符数，英文按单词数*1.3
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        other_chars = len(text) - chinese_chars
        english_words = len(text.split())
        
        return int(chinese_chars + english_words * 1.3)
    
    def close(self):
        """关闭客户端"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 便捷函数
def create_bailian_client(api_key: str, model: str = "qwen-max", 
                         endpoint: Optional[str] = None, **kwargs) -> BailianClient:
    """
    创建百炼客户端的便捷函数
    
    Args:
        api_key: API密钥
        model: 模型名称
        endpoint: API端点
        **kwargs: 其他配置参数
        
    Returns:
        BailianClient: 百炼客户端实例
    """
    config = BailianConfig(
        api_key=api_key,
        endpoint=endpoint,
        model=model,
        **kwargs
    )
    
    return BailianClient(config)


def generate_content(api_key: str, system_prompt: str, user_prompt: str,
                    model: str = "qwen-max", **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """
    生成内容的便捷函数
    
    Args:
        api_key: API密钥
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        model: 模型名称
        **kwargs: 其他参数
        
    Returns:
        Tuple[bool, str, Dict[str, Any]]: (是否成功, 生成内容, 元数据)
    """
    with create_bailian_client(api_key, model) as client:
        return client.generate_text(system_prompt, user_prompt, **kwargs)