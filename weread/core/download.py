import base64
import sys

from io import BytesIO
from typing import Tuple

from PIL import Image
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page
from pyzbar import pyzbar
from qrcode import QRCode

from weread import logger


async def _launch_browser(headless: bool = False,
                          incognito: bool = True) -> Tuple[Browser, Page]:
    """启动浏览器并通过扫码登录账户.

    Args:
        headless: bool, default=False,
            是否设置无界面(headless)模式.
        incognito: bool, default=True,
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

            image = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image))  # 输入解码图片的字节流.

            # 使用pybar提取登录URL, qrcode生成二维码.
            login_url = pyzbar.decode(image)[0].data.decode()
            qr_code = QRCode()
            qr_code.add_data(data=login_url)
            qr_code.print_ascii(invert=False)
        except IndexError:
            logger.error('二维码生成失败, 请重新启动weread-cli.')
            sys.exit(1)

    # 使用头像的导航栏(下拉菜单)判断登录成功.
    await page.waitForSelector('.wr_avatar.navBar_avatar', timeout=0)

    logger.info('登录成功:)')

    return browser, page


async def download(name: str):
    """根据图书名称下载原始的数据到本地.

    Args:
        name: str, 图书的名称.
    """
    # 启动浏览器, 登录账户.
    browser, page = await _launch_browser(headless=False, incognito=True)

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

    await browser.close()
