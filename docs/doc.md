# 微信读书ePub下载工具 🔧

[![build](https://github.com/sun1638650145/bunnyburrow-weread/actions/workflows/build.yml/badge.svg)](https://github.com/sun1638650145/bunnyburrow-weread/actions/workflows/build.yml) [![codecov](https://codecov.io/gh/sun1638650145/bunnyburrow-weread/branch/master/graph/badge.svg?token=BGOKZFYKWA)](https://codecov.io/gh/sun1638650145/bunnyburrow-weread)

微信读书ePub下载工具是Bunnyburrow Software Project(兔窝镇软件计划)的第2个组件, 它可以下载您已购买的电子书.

## 安装

仅需要`Python`环境, 在[发布页](https://github.com/sun1638650145/bunnyburrow-weread/releases)下载最新的稳定版`whl`文件安装即可.

```shell
# 安装工具.
# 如果你需要使用headless模式, 需要安装额外的依赖项目`pip install 'weread-0.1a1-py3-none-any.whl[headless]'`.
pip install weread-0.1a1-py3-none-any.whl
# 强烈推荐安装到虚拟环境, 并添加环境变量到shell.
echo alias weread-cli=/path/to/bin/weread-cli >> .zshrc
```

## 使用方法

微信读书ePub下载工具将提供3种灵活的使用方法.

### 1. 使用`weread-cli`命令行工具 💻 

这种方式是最稳定的方式, 但是需要注意你每天最多可以下载`3`本书, 超过`3`本就会被微信读书的服务器监控到异常流量.

```shell
# 扫码登录后, 通过web阅读器下载原始数据文件.
weread-cli download -v 怦然心动
# 检查下载的原始数据文件的完整性.
weread-cli check ./怦然心动（精装纪念版）.rdata.zip
# 生成ePub文件.
weread-cli generate ./怦然心动（精装纪念版）.rdata.zip
```

### 2. 在Python 🐍 脚本中使用

这种方式提供了足够丰富的权限, 你可以根据你的需要设置`headless`或者无痕, 修改默认的延时时间; 注意任意修改参数可能导致不稳定的情况发生.

```python
import asyncio
from weread import check, download, generate

# 扫码登录后, 通过web阅读器下载原始数据文件.
# 脚本中提供更加丰富的功能, 比如设置自定义下载路径, headless和无痕模式.
rdata_filepath = asyncio.run(download('怦然心动',
                                      verbose=True,
                                      info=True,
                                      incognito=False))
# 检查原始数据文件完整性, 并生成ePub文件.
if check(rdata_filepath):
    generate(rdata_filepath, info=True)
```

#### check

检查下载的原始数据文件的完整性.

```python
check(rdata_file, verbose=False, info=False)
```

##### 参数

* **rdata_file**: 字符串或路径, 原始数据文件.
* **verbose**: 布尔类型, 默认为`False`, 是否展示检查`ePub`文件的详细信息.
* **info**: 布尔类型, 默认为`False`, 是否输出提示信息.

##### 返回

检查的情况.

#### *(async)* download

根据图书名称下载原始的数据到本地.

```python
download(name, rdata_file_path=None, headless=False, incognito=True, delay=2, verbose=False, info=False)
```

##### 参数

* **name**: 字符串, 图书的名称.
* **rdata_file_path**: 字符串或路径, 默认为`'./图书名.rdata.zip'`, 原始数据文件保存路径.
* **headless**: 布尔类型, 默认为`False`, 是否为浏览器设置无界面(headless)模式.
* **incognito**: 布尔类型, 默认为`True`, 是否为浏览器设置无痕模式.
* **delay**: 浮点数, 默认为`2`, 设置延时, 用于等待网页加载并模拟人类操作, 可根据网络实际情况进行调整.
* **verbose**: 布尔类型, 默认为`False`, 是否展示下载过程的详细信息.
* **info**: 布尔类型, 默认为`False`, 是否输出提示信息.

##### 返回

原始数据文件保存的绝对路径.

#### generate

根据原始数据文件生成`ePub`文件. 生成的`ePub`文件参照这个目录创建:

```
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
```

```python
generate(rdata_file, verbose=False, info=False)
```

##### 参数

* **rdata_file**: 字符串或路径, 原始数据文件.
* **verbose**: 布尔类型, 默认为`False`, 是否展示生成`ePub`文件的详细信息.
* **info**: 布尔类型, 默认为`False`, 是否输出提示信息.

##### 返回

`ePub`文件的绝对路径.

## 目前已知的问题

目前已知的情况下, 微信读书ePub下载工具很“狂妄”的认为是你能找到的最好的下载工具, 它几乎可以完美的下载原始数据并生成ePub文件; 但是受限作者思维的局限性, 总是会有可以改进的问题.

|      |                           问题                            | 备注 |
| :--: | :-------------------------------------------------------: | :--: |
|  0   | 只能生成使用`<a>`标签的注释, 不能生成通过`vue`实现的注释. |  -   |
|  1   |                            ...                            |  -   |