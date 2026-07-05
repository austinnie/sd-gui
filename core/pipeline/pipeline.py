# core/pipeline/pipeline.py
"""流水线核心"""

from typing import Dict, Any, Optional, Callable, Type
from .step import PipelineStep, StepContext, StepResult, StepStatus


class Pipeline:
    """流水线 - 包含多个步骤"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: list[PipelineStep] = []
        self.results: Dict[str, StepResult] = {}
        self.current_index = 0
        self._on_progress: Optional[Callable] = None
    
    def add_step(self, step: PipelineStep) -> 'Pipeline':
        """添加步骤（链式调用）"""
        self.steps.append(step)
        return self
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """设置进度回调"""
        self._on_progress = callback
    
    def run(self, context: StepContext) -> Dict[str, StepResult]:
        """运行流水线"""
        self.results = {}
        total = len(self.steps)
        
        for idx, step in enumerate(self.steps):
            self.current_index = idx
            
            if self._on_progress:
                self._on_progress(idx + 1, total, f"正在执行: {step.name}")
            
            try:
                result = step.execute(context)
                self.results[step.name] = result
                context.step_results[step.name] = result
                
                if not result.success:
                    break
                    
            except Exception as e:
                self.results[step.name] = StepResult(
                    status=StepStatus.FAILED,
                    error=str(e)
                )
                break
        
        return self.results
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps]
        }


class PipelineRegistry:
    """流水线注册中心 - 管理所有步骤和预设流水线"""
    
    _instance = None
    _steps: Dict[str, Type[PipelineStep]] = {}
    _pipelines: Dict[str, Dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_step(cls, name: str, step_class: Type[PipelineStep]):
        """注册步骤类型"""
        cls._steps[name] = step_class
    
    @classmethod
    def get_step(cls, name: str) -> Optional[Type[PipelineStep]]:
        return cls._steps.get(name)
    
    @classmethod
    def get_all_steps(cls) -> Dict[str, Type[PipelineStep]]:
        return cls._steps.copy()
    
    @classmethod
    def register_pipeline(cls, name: str, pipeline_config: Dict):
        """注册预设流水线"""
        cls._pipelines[name] = pipeline_config
    
    @classmethod
    def get_pipeline(cls, name: str) -> Optional[Dict]:
        return cls._pipelines.get(name)
    
    @classmethod
    def get_all_pipelines(cls) -> Dict[str, Dict]:
        return cls._pipelines.copy()
    
    @classmethod
    def create_pipeline_from_config(cls, config: Dict) -> Pipeline:
        """从配置创建流水线"""
        pipeline = Pipeline(
            name=config.get("name", "未命名流水线"),
            description=config.get("description", "")
        )
        
        for step_config in config.get("steps", []):
            step_type_name = step_config.get("type")
            step_class = cls.get_step(step_type_name)
            if step_class:
                step = step_class()
                step.set_config(step_config.get("config", {}))
                pipeline.add_step(step)
            else:
                print(f"⚠️ 未找到步骤类型: {step_type_name}")
        
        return pipeline