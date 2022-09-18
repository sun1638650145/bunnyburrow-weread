import base64
import json
import sys
import time

from io import BytesIO
from pathlib import Path
from tempfile import mkstemp
from typing import Tuple
from urllib.error import HTTPError
from urllib.request import urlretrieve
from zipfile import ZIP_DEFLATED, ZipFile

from bs4 import BeautifulSoup
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
    await page.waitForSelector('.wr_avatar.navBar_avatar')

    logger.info('登录成功:)')

    return browser, page


def _download_for_chapter(metadata: dict, rdata_file: ZipFile):
    """下载单个章节的数据, 图片将保存成`Images/原始名称.jpg`,
     文本文件将保存成`Text/章节名-uid.html`, Styles/样式表文件将保存成`Styles/章节名-uid.css`.

    Args:
        metadata: dict,
            章节的元数据组成的字典.
        rdata_file: ZipFile,
            原始数据文件.
    """
    # 获取当前章节的uid.
    uid = metadata['currentChapter']['chapterUid']

    # 获取当前章节的对应文本.
    html = ''
    for page in metadata['chapterContentHtml']:
        html += page
    rdata_file.writestr(f'Text/chapter-{uid}.html', html)

    # 获取当前章节的对应图片, 遍历找到全部图片并保存.
    images = BeautifulSoup(html, features='lxml').find_all('img')
    for image in images:
        image_url = image['data-src']
        image_name = 'Images/' + image_url.split('/')[-1] + '.jpg'
        _, temp_image_path = mkstemp()
        try:
            urlretrieve(url=image_url, filename=temp_image_path)
            rdata_file.write(temp_image_path, image_name)
        except HTTPError as err:
            logger.warning(f'状态码: {err.code}, '
                           f'没有找到图片{image_url}, 你可以选择重新尝试或者无视警告.')


async def download(name: str,
                   headless: bool = False,
                   incognito: bool = True,
                   delay: float = 2.5,
                   verbose: bool = False,
                   info: bool = False) -> Path:
    """根据图书名称下载原始的数据到本地.

    Args:
        name: str,
            图书的名称.
        headless: bool, default=False,
            是否为浏览器设置无界面(headless)模式.
        incognito: bool, default=True,
            是否为浏览器设置无痕模式.
        delay: float, default=2.5,
            设置延时, 用于等待图片加载并模拟人类操作.
        verbose: bool, default=False,
            是否展示下载过程的详细信息.
        info: bool, default=False,
            是否输出提示信息.

    Return:
        原始数据文件的绝对路径.
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

    # 创建保存原始数据文件.
    rdata_file_path = book_metadata['bookInfo']['title'] + '.rdata.zip'
    rdata_file = ZipFile(rdata_file_path, 'w', ZIP_DEFLATED)

    # 遍历每章下载原始数据(包括图片, 样式表和文本).
    chapter_infos = book_metadata['chapterInfos']
    for i, chapter in enumerate(chapter_infos):
        # 在网页中切换章节.
        await page.Jeval('#routerView',
                         '''(elm, uid) => {
                            elm.__vue__.changeChapter({ chapterUid:uid })
                         }''',
                         chapter['chapterUid'])
        time.sleep(delay)  # 用于等待图片加载并模拟人类操作.

        # 获取章节的元数据.
        chapter_metadata = await page.Jeval('#app', '''(elm) => {
            return elm.__vue__.$store.state.reader
        }''')

        # 下载当前章节的数据.
        _download_for_chapter(chapter_metadata, rdata_file)

        if verbose:
            logger.info(f'第{i + 1}章下载完成.')

    if verbose:
        logger.info('-' * 50)

    # 保存书籍的元信息.
    book_info = book_metadata['bookInfo']
    book_info_json = json.dumps(book_info)
    rdata_file.writestr('content.json', book_info_json)

    # 保存书籍的章节描述信息.
    chapter_infos = book_metadata['chapterInfos']
    chapter_infos_json = json.dumps(chapter_infos)
    rdata_file.writestr('toc.json', chapter_infos_json)

    # 保存图书的样式表文件.
    css = book_metadata['chapterContentStyles']
    rdata_file.writestr('Styles/stylesheet.css', css)

    # 保存书籍的封面图片.
    coverpage_url = book_info['cover']
    coverpage_url = coverpage_url.replace('s_', 'o_')  # 修正使用缩略图的问题.
    _, temp_coverpage_path = mkstemp()
    urlretrieve(url=coverpage_url, filename=temp_coverpage_path)
    rdata_file.write(temp_coverpage_path, 'Images/coverpage.jpg')

    await browser.close()

    if info:
        logger.info('成功下载原始数据到本地:)')

    return Path(rdata_file_path).absolute()
