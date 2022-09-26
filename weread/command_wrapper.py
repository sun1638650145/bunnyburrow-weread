from asyncio import run

from weread import __version__
from weread import check, download, generate
from weread import logger


def check_command(rdata_file: str, verbose: bool):
    """检查命令, 检查下载的原始数据文件的完整性.

    Example:
        ```shell
        weread-cli check 怦然心动.rdata.zip
        ```

    Args:
        rdata_file: str,
            原始数据文件.
        verbose: bool,
            是否展示检查ePub文件的详细信息.
    """
    check(rdata_file, verbose, info=True)


def download_command(name: str, verbose: bool):
    """下载命令, 根据图书名称下载原始的数据到本地.

    Example:
        ```shell
        weread-cli download 怦然心动
        ```

    Args:
        name: str, 图书的名称.
        verbose: bool,
            是否展示下载过程的详细信息.
    """
    run(download(name, verbose=verbose, info=True))


def generate_command(rdata_file: str, verbose: bool):
    """生成ePub文件命令, 根据原始数据文件生成ePub文件.

    生成的ePub文件参照这个目录创建:
    ePub 3.x
        |
        |-- mimetype (纯文本`application/epub+zip`)
        |-- META-INF
            |
            |-- container.xml (用于指向元数据文件的位置)
            |-- com.apple.ibooks.display-options.xml (Apple Books的拓展)
        |
        |-- OEBPS
            |
            |-- content.opf (图书的元数据)
            |-- toc.ncx (章节的导航信息)
            |-- Images (图片文件)
            |-- Styles (样式表css)
                |
                |-- stylesheet.css (样式表)
                |
            |-- Text (章节内容xhtml)
                |
                |-- coverpage.xhtml (封面描述文件)
                |-- chapter-{index}.xhtml (章节内容xhtml)

    Example:
        ```shell
        weread-cli generate 怦然心动.rdata.zip
        ```

    Args:
        rdata_file: str,
            原始数据文件.
        verbose: bool,
            是否展示生成ePub文件的详细信息.
    """
    generate(rdata_file, verbose, info=True)


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
  weread-cli check [option] <rdata_file>
    check: 检查下载的原始数据文件的完整性.
      Option:
        --verbose, -v: 展示检查ePub文件的详细信息.
  weread-cli download [option] <book_name>
    download: 根据图书名称下载原始的数据到本地.
      Option:
        --verbose, -v: 展示下载过程的详细信息.
  weread-cli generate [option] <rdata_file>
    generate: 根据原始数据文件生成ePub文件.
      Option:
        --verbose, -v: 展示生成ePub文件的详细信息.
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
