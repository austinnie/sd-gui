# core/pipeline/step.py
"""流水线步骤基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from enum import Enum
from PIL import Image
import json


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """步骤执行结果"""
    status: StepStatus
    output_image: Optional[Image.Image] = None
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        return self.status == StepStatus.SUCCESS


@dataclass
class StepContext:
    """步骤执行上下文 - 在流水线中传递"""
    input_image: Image.Image
    input_path: str
    output_dir: str
    global_config: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    current_step_index: int = 0
    
    def get_previous_result(self, step_name: str) -> Optional[StepResult]:
        """获取之前步骤的结果"""
        return self.step_results.get(step_name)
    
    def get_previous_image(self, step_name: str) -> Optional[Image.Image]:
        """获取之前步骤的输出图片"""
        result = self.get_previous_result(step_name)
        return result.output_image if result else None


class PipelineStep(ABC):
    """流水线步骤基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._config: Dict[str, Any] = {}
    
    @abstractmethod
    def execute(self, context: StepContext) -> StepResult:
        """执行步骤"""
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置参数 schema（供 UI 生成表单）"""
        return {}
    
    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        self._config = config
    
    def get_config(self) -> Dict[str, Any]:
        return self._config
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "config": self._config,
            "type": self.__class__.__name__
        }