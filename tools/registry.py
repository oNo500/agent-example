from typing import Dict, List, Callable, Any
import inspect
import json
from functools import wraps
from core.exceptions import ToolExecutionError

class ToolRegistry:
    """工具函数注册和管理"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_descriptions: Dict[str, Dict] = {}
    
    def register(self, func: Callable = None, *, name: str = None, description: str = None):
        """装饰器：注册工具函数
        
        Args:
            func: 要注册的函数
            name: 工具名称，如果不提供则使用函数名
            description: 工具描述，如果不提供则从docstring提取
        """
        def decorator(f: Callable) -> Callable:
            tool_name = name or f.__name__
            
            # 提取函数签名信息
            sig = inspect.signature(f)
            params = {}
            for param_name, param in sig.parameters.items():
                param_info = {
                    "type": param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "Any",
                    "required": param.default == inspect.Parameter.empty,
                    "default": param.default if param.default != inspect.Parameter.empty else None
                }
                params[param_name] = param_info
            
            # 提取返回类型
            return_type = sig.return_annotation.__name__ if sig.return_annotation != inspect.Parameter.empty else "Any"
            
            # 提取描述信息
            tool_description = description or self._extract_description(f)
            
            # 注册工具
            self._tools[tool_name] = f
            self._tool_descriptions[tool_name] = {
                "name": tool_name,
                "description": tool_description,
                "parameters": params,
                "return_type": return_type
            }
            
            @wraps(f)
            def wrapper(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    raise ToolExecutionError(f"Tool '{tool_name}' execution failed: {str(e)}") from e
            
            return wrapper
        
        if func is None:
            return decorator
        else:
            return decorator(func)
    
    def _extract_description(self, func: Callable) -> str:
        """从函数docstring提取描述信息"""
        if func.__doc__:
            lines = func.__doc__.strip().split('\n')
            return lines[0] if lines else ""
        return f"Tool function: {func.__name__}"
    
    def get_tool_descriptions(self) -> List[Dict]:
        """获取所有工具的描述信息，供LLM使用"""
        return list(self._tool_descriptions.values())
    
    def get_tool_descriptions_json(self) -> str:
        """获取工具描述的JSON格式字符串"""
        return json.dumps(self.get_tool_descriptions(), indent=2, ensure_ascii=False)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行指定的工具函数
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具函数参数
            
        Returns:
            工具函数的执行结果
            
        Raises:
            ToolExecutionError: 工具不存在或执行失败
        """
        if tool_name not in self._tools:
            available_tools = list(self._tools.keys())
            raise ToolExecutionError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )
        
        try:
            return self._tools[tool_name](**kwargs)
        except Exception as e:
            raise ToolExecutionError(f"Failed to execute tool '{tool_name}': {str(e)}") from e
    
    def list_tools(self) -> List[str]:
        """列出所有已注册的工具名称"""
        return list(self._tools.keys())
    
    def has_tool(self, tool_name: str) -> bool:
        """检查工具是否已注册"""
        return tool_name in self._tools
    
    def get_tool_info(self, tool_name: str) -> Dict:
        """获取特定工具的详细信息"""
        if tool_name not in self._tool_descriptions:
            raise ToolExecutionError(f"Tool '{tool_name}' not found")
        return self._tool_descriptions[tool_name]

# 创建全局工具注册实例
tool_registry = ToolRegistry()