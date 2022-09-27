import json
import os
import sys

from pathlib import Path
from typing import Union
from zipfile import BadZipFile, ZipFile

from bs4 import BeautifulSoup

from weread import logger


def check(rdata_file: Union[str, os.PathLike],
          verbose: bool = False,
          info: bool = False) -> bool:
    """检查下载的原始数据文件的完整性.

    Args:
        rdata_file: str or os.PathLike,
            原始数据文件.
        verbose: bool, default=False,
            是否展示检查ePub文件的详细信息.
        info: bool, default=False,
            是否输出提示信息.

    Return:
        检查的情况.
    """
    # 查看rdata文件的内容.
    try:
        file_list = ZipFile(rdata_file).infolist()
        image_list = []
        text_list = []

        for file in file_list:
            if file.filename.startswith('Images/'):
                image_list.append(file.filename)
            elif file.filename.startswith('Text/'):
                text_list.append(file.filename)
    except BadZipFile:
        logger.error(f'{Path(rdata_file).name} 不是一个合法的rdata文件!')
        sys.exit(1)
    except FileNotFoundError:
        logger.error('请检查你的rdata文件路径, 未找到rdata文件!')
        sys.exit(1)

    image_set = set()
    status = True

    # 提取图书章节数据, 检查文本完整性.
    chapter_infos = json.loads(ZipFile(rdata_file).read('toc.json'))
    for chapter in chapter_infos:
        chapter_file = f'Text/chapter-{chapter["chapterUid"]}.html'
        if chapter_file not in text_list and verbose:
            logger.warning(f'文件 {chapter_file} 未找到!')
            status = False
        else:
            # 添加当前章节的对应图片.
            html = ZipFile(rdata_file).read(chapter_file)
            images = BeautifulSoup(html, features='lxml').find_all('img')
            for image in images:
                image_set.add(image['data-src'].split('/')[-1])

    # 检查图片完整性.
    image_set.add('coverpage')  # 添加封面文件.
    for image in image_set:
        if f'Images/{image}.jpg' not in image_list and verbose:
            logger.warning(f'图片 Images/{image}.jpg 未找到!')
            status = False

    if verbose:
        logger.info('-' * 50)

    if info and status:
        logger.info('下载的原始数据文件完整:)')
    elif info and not status:
        logger.info('下载的原始数据文件有缺失, 请使用`download`命令重新下载.')

    return status
