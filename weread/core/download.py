import json
import os
import sys
import time

from pathlib import Path
from tempfile import mkstemp
from typing import List, Optional, Tuple, Union
from urllib.error import HTTPError
from urllib.request import urlretrieve
from zipfile import ZIP_DEFLATED, ZipFile

from bs4 import BeautifulSoup
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page

from weread import logger

try:
    import base64
    from io import BytesIO

    from PIL import Image
    from pyzbar import pyzbar
    from qrcode import QRCode
except ModuleNotFoundError:
    logger.warning("如果你需要使用headless模式, 请运行`pip install 'weread[headless]'`"
                   "安装依赖项, 否则请忽略警告.")


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
    browser = await launch(headless=headless, logLevel='ERROR')

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
            await browser.close()
            logger.error('二维码生成失败, 请重新启动.')
            sys.exit(1)

    # 使用头像的导航栏(下拉菜单)判断登录成功.
    await page.waitForSelector('.wr_avatar.navBar_avatar')

    logger.info('登录成功:)')

    return browser, page


def _download_chapter_content(metadata: dict,
                              rdata_file: ZipFile) -> List[str]:
    """下载单个章节的文本数据, 文本文件将保存成`Text/章节名-uid.html`,
    并提取文本中的图片url.

    Args:
        metadata: dict,
            章节的元数据组成的字典.
        rdata_file: ZipFile,
            原始数据文件.

    Return:
        文本中的图片url组成的列表.
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
    image_urls = [image['data-src'] for image in images]

    return image_urls


def _download_images(image_urls: List[str],
                     rdata_file: ZipFile,
                     verbose: bool):
    """根据图片的url下载图书中的全部图片.

    Args:
        image_urls: list of str,
            图片url组成的列表.
        rdata_file: ZipFile,
            原始数据文件.
        verbose: bool,
            是否展示下载过程的详细信息.
    """
    for image_url in image_urls:
        if 'cover' in image_url:
            image_name = 'Images/coverpage.jpg'
        else:
            image_name = 'Images/' + image_url.split('/')[-1] + '.jpg'

        # 下载单张图片到原始数据文件.
        try:
            _, temp_image_path = mkstemp()
            urlretrieve(url=image_url, filename=temp_image_path)
            rdata_file.write(temp_image_path, image_name)
            if verbose:
                logger.info(f'图片{image_name}下载完成.')
        except HTTPError as err:
            logger.warning(f'状态码: {err.code}, '
                           f'没有找到图片{image_url}, 你可以选择重新尝试或者无视警告.')


async def download(name: str,
                   rdata_file_path: Optional[Union[str, os.PathLike]] = None,
                   headless: bool = False,
                   incognito: bool = True,
                   delay: float = 2,
                   verbose: bool = False,
                   info: bool = False) -> Path:
    """根据图书名称下载原始的数据到本地.

    Args:
        name: str,
            图书的名称.
        rdata_file_path: str or os.PathLike, default=None,
            原始数据文件保存路径, 默认为'./图书名.rdata.zip'.
        headless: bool, default=False,
            是否为浏览器设置无界面(headless)模式.
        incognito: bool, default=True,
            是否为浏览器设置无痕模式.
        delay: float, default=2,
            设置延时, 用于等待网页加载并模拟人类操作,
             可根据网络实际情况进行调整.
        verbose: bool, default=False,
            是否展示下载过程的详细信息.
        info: bool, default=False,
            是否输出提示信息.

    Return:
        原始数据文件保存的绝对路径.
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
        await browser.close()
        logger.error(f'没有找到你想要下载的《{name}》, 请检查你是否拥有这本书或书名是否正确!')
        sys.exit(1)

    # 获取图书的元数据.
    book_metadata = await page.Jeval('#app', '''(elm) => {
        return elm.__vue__.$store.state.reader
    }''')

    # 创建保存原始数据文件.
    if not rdata_file_path:
        rdata_file_path = Path(book_metadata['bookInfo']['title'] + '.rdata.zip')  # noqa: E501
    rdata_file = ZipFile(rdata_file_path, 'w', ZIP_DEFLATED)

    # 遍历每章下载原始文本并获取图片地址.
    chapter_infos = book_metadata['chapterInfos']
    image_urls = set()  # 用于保存全部图片的url.
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
        image_urls.update(_download_chapter_content(chapter_metadata, rdata_file))  # noqa: E501

        if verbose:
            logger.info(f'第{i + 1}章文本下载完成.')

    await browser.close()  # 提前关闭浏览器, 此时已不需要控制浏览器.

    # 保存图书的元数据.
    book_info = book_metadata['bookInfo']
    book_info_json = json.dumps(book_info)
    rdata_file.writestr('content.json', book_info_json)
    if verbose:
        logger.info('图书元数据下载完成.')

    # 保存图书的章节描述信息.
    chapter_infos = book_metadata['chapterInfos']
    chapter_infos_json = json.dumps(chapter_infos)
    rdata_file.writestr('toc.json', chapter_infos_json)
    if verbose:
        logger.info('图书的章节描述信息下载完成.')

    # 保存图书的样式表文件.
    css = book_metadata['chapterContentStyles']
    rdata_file.writestr('Styles/stylesheet.css', css)
    if verbose:
        logger.info('图书的样式表文件下载完成.')

    # 保存书籍的封面图片.
    coverpage_url = book_info['cover']
    coverpage_url = coverpage_url.replace('s_', 'o_')  # 修正使用缩略图的问题.
    image_urls.add(coverpage_url)
    _download_images(list(image_urls), rdata_file, verbose)

    if verbose:
        logger.info('-' * 50)

    if info:
        logger.info('成功下载原始数据到本地:)')

    return Path(rdata_file_path).absolute()
