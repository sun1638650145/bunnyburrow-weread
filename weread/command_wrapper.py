from asyncio import run

from weread import __version__
from weread import download
from weread import logger


def download_command(name: str):
    """下载命令, 根据图书名称下载原始的数据到本地.

    Example:
        ```shell
        weread-cli download 怦然心动
        ```

    Args:
        name: str, 图书的名称.
    """
    run(download(name, info=True))


def help_command(level: str):
    """帮助命令, 用于查看帮助信息.

    Example:
        ```shell
        weread-cli help
        ```

    Args:
        level: {'error', 'info'},
            logger输出的级别.
    """
    _help_msg = """微信读书ePub下载工具

Bunnyburrow Software Project(兔窝镇软件计划)
Copyright 2022 Steve R. Sun. All rights reserved.
-------------------------------------------------
Usage:
  weread-cli download <book_name>
    download: 根据图书名称下载原始的数据到本地.
  weread-cli help
    help, --help, -h: 获取帮助信息.
  weread-cli version
    version, --version, -v: 查看下载工具的版本.
"""
    if level == 'error':
        logger.error(_help_msg)
    else:
        logger.info(_help_msg)


def version_command():
    """查看版本命令.

    Example:
        ```shell
        weread-cli version
        ```
    """
    logger.info('微信读书ePub下载工具 ' + __version__)
