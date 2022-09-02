from setuptools import setup, find_packages

setup(
    name='weread',
    version='0.1a0',
    description='微信读书ePub下载工具',
    author='Steve R. Sun',
    author_email='s1638650145@gmail.com',
    url='www.sunruiqi.com',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    license='Non-free Software',
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'weread-cli = weread.cli:run'
        ]
    },
)
