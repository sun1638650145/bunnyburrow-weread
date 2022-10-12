"""测试检查功能."""
import pytest

from weread import check


class TestCheck(object):
    def test_check(self):
        """测试检查rdata文件的完整性."""
        assert check(rdata_file='tests/assets/怦然心动（精装纪念版）.rdata.zip',
                     verbose=True,
                     info=True) is True

        # 测试rdata文件传递错误.
        with pytest.raises(SystemExit) as pytest_exit:
            check('tests/test_check.py')
        assert pytest_exit.type is SystemExit
        assert pytest_exit.value.code == 1

        # 未找到文件错误.
        with pytest.raises(SystemExit) as pytest_exit:
            check('./book.rdata.zip')
        assert pytest_exit.type is SystemExit
        assert pytest_exit.value.code == 1
