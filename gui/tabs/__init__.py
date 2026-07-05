#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI 标签页模块
"""

from .base_tab import BaseTab
from .txt2img_tab import Txt2ImgTab
from .img2img_tab import Img2ImgTab
from .interrogate_tab import InterrogateTab
from .universal_tab import UniversalTab
from .scene_tab import SceneTab
from .janus_tab import JanusTab

__all__ = [
    'BaseTab',
    'Txt2ImgTab',
    'Img2ImgTab',
    'InterrogateTab',
    'UniversalTab',
    'SceneTab',
    'JanusTab'
]