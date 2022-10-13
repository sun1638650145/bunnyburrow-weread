"""测试生成ePub文件功能."""
import pytest

from weread import generate


class TestGenerate(object):
    def test_generate(self):
        """测试生成ePub文件."""
        assert generate(rdata_file='tests/assets/怦然心动（精装纪念版）.rdata.zip',
                        verbose=True,
                        info=True)

        # 测试rdata文件传递错误.
        with pytest.raises(SystemExit) as pytest_exit:
            generate('tests/README.md')
        assert pytest_exit.type is SystemExit
        assert pytest_exit.value.code == 1

        # 未找到文件错误.
        with pytest.raises(SystemExit) as pytest_exit:
            generate('./book.rdata.zip')
        assert pytest_exit.type is SystemExit
        assert pytest_exit.value.code == 1
