import json
import os
import re
import sys

from pathlib import Path
from time import strftime, strptime
from typing import Dict, List, Union
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile, ZipInfo

from bs4 import BeautifulSoup

from weread import logger


def _generate_meta_inf(epub_file: ZipFile):
    """创建META-INF文件夹并生成当前文件夹下全部文件.

    Args:
        epub_file: ZipFile,
            生成的ePub文件的文件指针.
    """
    # 创建container.xml.
    container_xml = BeautifulSoup(features='xml')
    container = container_xml.new_tag('container', attrs={
        'xmlns': 'urn:oasis:names:tc:opendocument:xmlns:container',
        'version': '1.0',
    })
    container_xml.append(container)
    rootfiles = container_xml.new_tag('rootfiles')
    container.append(rootfiles)
    rootfile = container_xml.new_tag('rootfile', attrs={
        'full-path': 'OEBPS/content.opf',
        'media-type': 'application/oebps-package+xml'
    })
    rootfiles.append(rootfile)

    epub_file.writestr('META-INF/container.xml', container_xml.prettify())

    # 创建com.apple.ibooks.display-options.xml.
    ibooks_xml = BeautifulSoup(features='xml')
    display_options = ibooks_xml.new_tag('display_options')
    ibooks_xml.append(display_options)
    platform = ibooks_xml.new_tag('platform', attrs={'name': '*'})
    display_options.append(platform)
    option = ibooks_xml.new_tag('option', attrs={'name': 'specified-fonts'})
    option.string = 'true'
    platform.append(option)

    epub_file.writestr('META-INF/com.apple.ibooks.display-options.xml',
                       ibooks_xml.prettify())


def _generate_content_opf(book_info: Dict, file_list: List[ZipInfo]) -> str:
    """在OEBPS文件夹下创建content.opf文件.

    References:
        - [开源包格式](http://www.theheratik.net/books/tech-epub/chapter-3/)

    Args:
        book_info: dict,
            书籍的元信息.
        file_list: list of ZipInfo,
            原始数据文件的文件列表.

    Return:
        content.opf文件内容的xml文本.
    """
    content_opf = BeautifulSoup(features='xml')

    # 创建<package>元素.
    package = content_opf.new_tag('package', attrs={
        'xmlns': 'https://www.idpf.org/2007/opf',
        'version': '3.0',
        'unique-identifier': 'weread-book-id',
        'xml:lang': 'en'
    })
    content_opf.append(package)

    # 创建<metadata>元素
    metadata = content_opf.new_tag('metadata', attrs={
        'xmlns:dc': 'https://purl.org/dc/elements/1.1/',
        'xmlns:opf': 'https://www.idpf.org/2007/opf'
    })
    package.append(metadata)
    # 图书ID(ePub文件的唯一ID).
    dc_identifier = content_opf.new_tag('dc:identifier', attrs={
        'id': 'weread-book-id'
    })
    dc_identifier.string = book_info['bookId']
    metadata.append(dc_identifier)
    # 图书标题.
    dc_title = content_opf.new_tag('dc:title')
    dc_title.string = book_info['title']
    metadata.append(dc_title)
    # 图书语言.
    dc_language = content_opf.new_tag('dc:language')
    dc_language.string = 'zh'
    metadata.append(dc_language)
    # 图书作者(可选).
    dc_creator = content_opf.new_tag('dc:creator', attrs={
        'opf:file-as': book_info['author'],
        'opf:role': 'aut'
    })
    dc_creator.string = book_info['author']
    metadata.append(dc_creator)
    # 图书其他贡献人(可选, 比如译者).
    try:
        dc_contributor = content_opf.new_tag('dc:contributor', attrs={
            'opf:role': 'trl'
        })
        dc_contributor.string = book_info['translator']
        metadata.append(dc_contributor)
    except KeyError:
        pass
    # 图书发行日期(可选, 使用ISO8601格式).
    dc_date = content_opf.new_tag('dc:date')
    publish_time = strptime(book_info['publishTime'], '%Y-%m-%d %H:%M:%S')
    dc_date.string = strftime('%Y-%m-%dT%H:%M:%SZ', publish_time)
    metadata.append(dc_date)
    # 图书ISBN(可选).
    dc_source = content_opf.new_tag('dc:source', attrs={'id': 'src-id'})
    dc_source.string = 'urn:isbn:' + book_info['isbn']
    metadata.append(dc_source)
    # 图书出版社(可选).
    dc_publisher = content_opf.new_tag('dc:publisher')
    dc_publisher.string = book_info['publisher']
    metadata.append(dc_publisher)
    # 图书内容描述(可选).
    dc_description = content_opf.new_tag('dc:description')
    dc_description.string = book_info['intro']
    metadata.append(dc_description)
    # meta用于保存自定义属性.
    meta = content_opf.new_tag('meta', attrs={
        'property': 'ibooks:specified-fonts'
    })
    meta.string = 'true'
    metadata.append(meta)

    # 创建<manifest>元素.
    manifest = content_opf.new_tag('manifest')
    package.append(manifest)
    # 遍历原始数据文件的文件列表.
    for file in file_list:
        attrs = {'href': file.filename.replace('html', 'xhtml')}  # 替换原始文本的html格式成xhtml.  # noqa: E501
        if file.filename.startswith('Images/'):
            attrs.update({
                'id': 'image-' + Path(file.filename).name.split('.')[0],
                'media-type': 'image/jpeg'
            })
        elif file.filename.startswith('Styles/'):
            attrs.update({
                'id': 'style-' + Path(file.filename).name.split('.')[0],
                'media-type': 'text/css'
            })
        elif file.filename.startswith('Text/'):
            attrs.update({
                'id': 'text-' + Path(file.filename).name.split('.')[0],
                'media-type': 'application/xhtml+xml'
            })
        else:
            continue
        item = content_opf.new_tag('item', attrs=attrs)
        manifest.append(item)
    # 增加描述封面的xml文件.
    coverage_xml = content_opf.new_tag('item', attrs={
        'href': 'Text/coverage.xml',
        'id': 'text-coverage',
        'media-type': 'application/xhtml+xml'
    })
    manifest.append(coverage_xml)
    # 增加章节描述信息的toc.ncx文件.
    toc_ncx = content_opf.new_tag('item', attrs={
        'href': 'toc.ncx',
        'id': 'ncx',
        'media-type': 'application/x-dtbncx+xml'
    })
    manifest.append(toc_ncx)

    # 创建<spine>元素, 描述ePub文件内容的有序列表.
    spine = content_opf.new_tag('spine', attrs={'toc': 'ncx'})
    package.append(spine)
    itemref = content_opf.new_tag('itemref', attrs={'idref': 'text-coverage'})
    spine.append(itemref)
    for file in file_list:
        if file.filename.startswith('Text/'):
            itemref = content_opf.new_tag('itemref', attrs={
                'idref': 'text-' + Path(file.filename).name.split('.')[0]
            })
            spine.append(itemref)

    # 创建<guide>元素, 指向描述封面的xml文件.
    guide = content_opf.new_tag('guide')
    package.append(guide)
    reference = content_opf.new_tag('reference', attrs={
        'type': 'coverpage',
        'title': book_info['title'],
        'href': 'Text/coverpage.xml'
    })
    guide.append(reference)

    return content_opf.prettify()


def _generate_toc_ncx(chapter_infos: List[Dict],
                      chapter_paths: List[str],
                      book_id: str,
                      book_title: str) -> str:
    """在OEBPS文件夹下创建toc.ncx文件.

    References:
        - [导航文件格式](http://www.theheratik.net/books/tech-epub/chapter-4/)

    Args:
        chapter_infos: list of dict,
            书籍章节的原始信息.
        chapter_paths: list of str,
            章节的保存路径.
        book_id: str,
            图书ID.
        book_title: str,
            图书标题.

    Return:
        toc.ncx文件内容的xml文本.
    """
    toc_ncx = BeautifulSoup(features='xml')
    ncx = toc_ncx.new_tag('ncx', attrs={
        'xmlns': 'https://www.daisy.org/z3986/2005/ncx/',
        'version': '2005-1',
        'xml:lang': 'en',
    })
    toc_ncx.append(ncx)

    # 创建<head>元素.
    head = toc_ncx.new_tag('head')
    ncx.append(head)
    # meta用于存储图书元数据.
    meta = toc_ncx.new_tag('meta', attrs={
        'name': 'dtb:uid',  # 与content.opf中的dc:identifier相同.
        'content': book_id
    })
    head.append(meta)
    meta = toc_ncx.new_tag('meta', attrs={'name': 'dtb:depth', 'content': 1})
    head.append(meta)
    meta = toc_ncx.new_tag('meta', attrs={
        'name': 'dtb:totalPageCount',
        'content': 0
    })
    head.append(meta)
    meta = toc_ncx.new_tag('meta', attrs={
        'name': 'dtb:maxPageNumber',
        'content': 0
    })
    head.append(meta)

    # 创建<docTitle>元素, 包含图书标题.
    doc_title = toc_ncx.new_tag('docTitle')
    ncx.append(doc_title)
    text = toc_ncx.new_tag('text')
    text.string = book_title
    doc_title.append(text)

    # 创建<navMap>元素, 列出每章的标题.
    nav_map = toc_ncx.new_tag('navMap')
    ncx.append(nav_map)
    # 遍历章节信息.
    for i, (chapter_info, chapter_path) in enumerate(zip(chapter_infos, chapter_paths)):  # noqa: E501
        nav_point = toc_ncx.new_tag('navPoint', attrs={
            'id': f'np-{i + 1}',
            'playOrder': i + 1,
        })
        nav_map.append(nav_point)
        nav_label = toc_ncx.new_tag('navLabel')
        nav_point.append(nav_label)
        text = toc_ncx.new_tag('text')
        text.string = chapter_info['title']
        nav_label.append(text)
        content = toc_ncx.new_tag('content', attrs={
            'src': chapter_path.replace('html', 'xhtml')  # 替换原始文本的html格式成xhtml.  # noqa: E501
        })
        nav_point.append(content)

    return toc_ncx.prettify()


def _generate_oebps(rdata_file: Union[str, os.PathLike], epub_file: ZipFile):
    """创建OEBPS文件夹并生成当前文件夹下全部文件.

    Args:
        rdata_file: str or os.PathLike,
            原始数据文件.
        epub_file: ZipFile,
            生成的ePub文件的文件指针.
    """
    # 查看原始数据文件的内容.
    try:
        file_list = ZipFile(rdata_file).infolist()
        file_list.sort(key=lambda x: (re.sub(r'\d+', '', x.filename)))  # 先根据字母, 再根据数字排序.  # noqa: E501
    except BadZipFile:
        logger.error(f'{Path(rdata_file).name}不是一个合法的原始数据文件!')
        sys.exit(1)
    except FileNotFoundError:
        logger.error('请检查你的原始数据文件路径, 未找到原始数据文件!')
        sys.exit(1)

    # 通过content.json生成content.opf.
    try:
        book_info_bytes = ZipFile(rdata_file).read('content.json')
        book_info_json = json.loads(book_info_bytes)
    except KeyError:
        logger.error('没有找到content.json文件, 请检查你的原始数据文件!')
        sys.exit(1)
    content_opf_str = _generate_content_opf(book_info_json, file_list)
    epub_file.writestr('OEBPS/content.opf', content_opf_str)

    # 通过toc.json生成toc.ncx.
    try:
        chapter_infos_bytes = ZipFile(rdata_file).read('toc.json')
        chapter_infos_json = json.loads(chapter_infos_bytes)
    except KeyError:
        logger.error('没有找到toc.json文件, 请检查你的原始数据文件!')
        sys.exit(1)

    # 筛选章节内容的路径.
    chapter_paths = []
    for file in file_list:
        if file.filename.startswith('Text/'):
            chapter_paths.append(file.filename)

    toc_ncx_str = _generate_toc_ncx(chapter_infos_json,
                                    chapter_paths,
                                    book_info_json['bookId'],
                                    book_info_json['title'])
    epub_file.writestr('OEBPS/toc.ncx', toc_ncx_str)


def generate(rdata_file: Union[str, os.PathLike], verbose: bool = False):
    """根据原始数据文件生成ePub文件.

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
            |-- toc.ncx (章节的描述信息)
            |-- Styles (样式表css)
            |-- Text (章节内容xhtml)
            |-- Images (图片文件)

    References:
        - [发布ePub文档](http://www.theheratik.net/books/tech-epub/)

    Args:
        rdata_file: str or os.PathLike,
            原始数据文件.
        verbose: bool, default=False,
            是否展示生成ePub文件的详细信息.
    """
    # 创建ePub文件.
    epub_file_path = str(Path(rdata_file)).split('.')[0] + '.epub'
    epub_file = ZipFile(epub_file_path, 'w', ZIP_DEFLATED)

    # 创建mimetype文件.
    epub_file.writestr('mimetype', 'application/epub+zip')

    # 创建META-INF文件夹.
    _generate_meta_inf(epub_file)

    # 创建OEBPS文件夹.
    _generate_oebps(rdata_file, epub_file)
