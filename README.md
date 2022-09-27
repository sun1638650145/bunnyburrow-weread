# 微信读书ePub下载工具 🔧

微信读书ePub下载工具是Bunnyburrow Software Project(兔窝镇软件计划)的第2个组件, 它可以下载您已购买的电子书.

## 声明 ⚠️

为尊重微信读书的合法权益, 本项目禁止开展任何商业行为, 禁止闭源开发. 由您不当使用均与开发者无关!

## 使用方法

微信读书ePub下载工具将提供3种灵活的使用方法.

### 1. 使用`weread-cli`命令行工具 💻 

```shell
# 扫码登录后, 通过web阅读器下载原始数据文件.
weread-cli download -v 怦然心动
# 检查下载的原始数据文件的完整性.
weread-cli check ./怦然心动（精装纪念版）.rdata.zip
# 生成ePub文件.
weread-cli generate ./怦然心动（精装纪念版）.rdata.zip
```

### 2. 在Python 🐍 脚本中使用

```python
import asyncio
from weread import check, download, generate

# 扫码登录后, 通过web阅读器下载原始数据文件.
# 脚本中提供更加丰富的功能, 比如设置headless和无痕模式.
rdata_filepath = asyncio.run(download('怦然心动',
                                      verbose=True,
                                      info=True,
                                      incognito=False))
# 检查原始数据文件完整性, 并生成ePub文件.
if check(rdata_filepath):
    generate(rdata_filepath, info=True)
```

### 3. 在集成的Bunnyburrow中通过图形化界面使用 🧑‍💻 (即将实现)