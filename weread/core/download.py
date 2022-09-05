import base64
import os
import sys
import time

from io import BytesIO
from pathlib import Path
from typing import Tuple

from PIL import Image
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page
from pyzbar import pyzbar
from qrcode import QRCode

from weread import logger


def _generate_qrcode(base64_str: str):
    """生成登录二维码.

    Args:
        base64_str: str,
            使用base64编码的二维码字符串.
    """
    image = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image))  # 输入解码图片的字节流.

    # 使用pybar提取登录URL, qrcode生成二维码.
    login_url = pyzbar.decode(image)[0].data.decode()
    qrcode = QRCode()
    qrcode.add_data(data=login_url)
    qrcode.print_ascii(invert=False)


async def _launch_browser(headless: bool,
                          incognito: bool) -> Tuple[Browser, Page]:
    """启动浏览器并通过扫码登录账户.

    Args:
        headless: bool,
            是否设置无界面(headless)模式.
        incognito: bool,
            是否设置无痕模式.

    Returns:
        启动的浏览器和进行操作的页面.
    """
    browser = await launch(headless=headless)

    # 设置无痕模式.
    if incognito:
        context = await browser.createIncognitoBrowserContext()
        page = await context.newPage()
    else:
        page = await browser.newPage()

    await page.goto('https://weread.qq.com/#login')

    # 在headless模式下, 将在终端显示登录二维码.
    if headless:
        logger.info('请注意二维码只有60s有效时间!')

        element = await page.xpath('//img[@alt="扫码登录"]')
        try:
            image_base64 = await (await element[0].getProperty('src')).jsonValue()  # noqa: E501
            image_base64 = image_base64[22:]  # `data:image/png;base64,`移除头部.

            # 生成二维码.
            _generate_qrcode(image_base64)
        except IndexError:
            logger.error('二维码生成失败, 请重新启动.')
            sys.exit(1)

    # 使用头像的导航栏(下拉菜单)判断登录成功.
    await page.waitForSelector('.wr_avatar.navBar_avatar', timeout=0)

    logger.info('登录成功:)')

    return browser, page


def _download_stylesheet_file(metadata: dict, styles_folder: os.PathLike):
    """下载单个样式表文件, 样式表文件将保存成`章节名-uid.css`.

    Args:
        metadata: dict,
            章节的元数据组成的字典.
        styles_folder: os.PathLike,
            样式表文件夹的路径.
    """
    if not os.path.exists(styles_folder):
        os.makedirs(styles_folder)

    # 获取当前章节的uid和样式表.
    uid = metadata['currentChapter']['chapterUid']
    style_sheets = metadata['chapterContentStyles']

    css_filepath = f'{styles_folder}/chapter-{uid}.css'
    with open(css_filepath, 'w') as fp:
        fp.write(style_sheets)

    logger.info(f'第{uid}章样式表下载完成.')


async def download(name: str,
                   headless: bool = False,
                   incognito: bool = True,
                   delay: int = 3):
    """根据图书名称下载原始的数据到本地.

    Args:
        name: str,
            图书的名称.
        headless: bool, default=False,
            是否为浏览器设置无界面(headless)模式.
        incognito: bool, default=True,
            是否为浏览器设置无痕模式.
        delay: int, default=3,
            设置延时, 用于模拟人类操作.
    """
    # 启动浏览器, 登录账户.
    browser, page = await _launch_browser(headless, incognito)

    # 进入我的书架, 提取图书的URL.
    await page.click('.bookshelf_preview_header_link')
    book_urls = await page.xpath('//a[@class="shelfBook"]')  # //tagname[@attribute='value']  # noqa: E501

    # 查找书籍并进入web阅读器.
    book_url = None
    for url in book_urls:
        if name in await (await url.getProperty('text')).jsonValue():
            book_url = str(await (await url.getProperty('href')).jsonValue())
            await page.goto(book_url)
            break

    if not book_url:
        logger.error(f'没有找到你想要下载的《{name}》, 请检查你是否拥有这本书或书名是否正确!')
        sys.exit(1)

    # 获取图书的元数据.
    book_metadata = await page.Jeval('#app', '''(elm) => {
        return elm.__vue__.$store.state.reader
    }''')

    # 创建保存原始数据的文件夹路径.
    raw_folder = Path(book_metadata['bookInfo']['title'] + '.raw/')
    # images_folder = Path(os.path.join(raw_folder, 'Images'))
    styles_folder = Path(os.path.join(raw_folder, 'Styles'))
    # text_folder = Path(os.path.join(raw_folder, 'Text'))

    # 遍历每章下载原始数据(包括图片, 样式表和文本).
    chapter_infos = book_metadata['chapterInfos']
    for chapter in chapter_infos:  # 章节id不一定从1开始.
        # 在网页中切换章节, 并设置延时, 模拟人类操作.
        await page.Jeval('#routerView',
                         '''(elm, uid) => {
                            elm.__vue__.changeChapter({ chapterUid:uid })
                         }''',
                         chapter['chapterUid'])
        time.sleep(delay)

        # 获取章节的元数据.
        chapter_metadata = await page.Jeval('#app', '''(elm) => {
            return elm.__vue__.$store.state.reader
        }''')

        # 下载当前的章节的样式表.
        _download_stylesheet_file(chapter_metadata, styles_folder)

        logger.info('-' * 50)

    await browser.close()
