# gui/tabs/__init__.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .base_tab import BaseTab
from .txt2img import Txt2ImgTab
from .img2img_tab import Img2ImgTab

from .universal_tab import UniversalTab
from .scene_tab import SceneTab
from .janus_tab import JanusTab
from .grid_test_tab import GridTestTab
from .pipeline_tab import PipelineTab
from .lora_manager import LoraManagerTab
from .chat_tab import ChatTab

from .interrogate import InterrogateTab

__all__ = [
    'BaseTab',
    'Txt2ImgTab',
    'Img2ImgTab',
    'InterrogateTab',
    'UniversalTab',
    'SceneTab',
    'JanusTab',
    'GridTestTab',
    'PipelineTab',
    'LoraManagerTab',
    'ChatTab',
]