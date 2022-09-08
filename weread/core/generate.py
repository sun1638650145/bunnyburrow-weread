import os

from pathlib import Path
from typing import Union
from zipfile import ZIP_DEFLATED, ZipFile


def _generate_meta_inf(epub_file: ZipFile):
    """创建META-INF文件夹并生成当前文件夹下全部文件.

    Args:
        epub_file: ZipFile,
            ePub文件的文件指针.
    """
    container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf"
                  media-type="application/oebps-package+xml" />
    </rootfiles>
</container>'''  # noqa: E501
    ibooks_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<display_options>
    <platform name="*">
        <option name="specified-fonts">true</option>
    </platform>
</display_options>'''

    epub_file.writestr('META-INF/container.xml', container_xml)
    epub_file.writestr('META-INF/com.apple.ibooks.display-options.xml', ibooks_xml)  # noqa: E501


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
            |-- content.opf (图书的元数据出版信息)
            |-- toc.ncx (章节的描述信息)
            |-- Styles (样式表css)
            |-- Text (章节内容xhtml)
            |-- Images (图片文件)

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
