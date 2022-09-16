"""微信读书ePub下载工具.

Bunnyburrow Software Project(兔窝镇软件计划)
Copyright 2022 Steve R. Sun. All rights reserved.
"""
__version__ = '0.1a2'

import logging
# 设置系统logger.
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger()

from weread.core import download
from weread.core import generate
