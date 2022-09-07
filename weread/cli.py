import sys
from typing import Dict, List

from weread import __version__
from weread import logger
from weread.command_wrapper import (
    download_command,
    help_command,
    version_command
)


def _parse_args(args: List) -> Dict:
    """解析命令行参数.

    Args:
        args: list of str,
            命令行的参数.

    Return:
        命令行解析后的参数元数据字典.
    """
    if len(args) < 2:  # 没有参数.
        help_command('error')
        sys.exit(127)
    else:
        args = args[1:]

        metadata = {}
        try:
            if args[0] == 'download':
                if args[1] in ('--verbose', '-v'):
                    metadata.update({
                        'download': {
                            'name': args[2],
                            'verbose': True
                        }
                    })
                else:
                    metadata.update({
                        'download': {
                            'name': args[1],
                            'verbose': False
                        }
                    })
            elif args[0] in ('help', '--help', '-h'):
                metadata.update({'help': True})
            elif args[0] in ('version', '--version', '-v'):
                metadata.update({'version': __version__})
            else:
                metadata.update({'other': True})
        except IndexError:
            logger.error('缺少必要的参数, 请检查你填写的参数!')
            sys.exit(2)

        return metadata


def run():
    """启动命令行工具."""
    meta_data = _parse_args(sys.argv)
    for command, params in meta_data.items():
        if command == 'download':
            download_command(params['name'], params['verbose'])
        elif command == 'help':
            help_command('info')
        elif command == 'version':
            version_command()
        else:
            help_command('error')
            sys.exit(127)
