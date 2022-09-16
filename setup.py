from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as fp:
    long_description = fp.read()

setup(
    name='weread',
    version='0.1a2',
    description='微信读书ePub下载工具',
    long_description=long_description,
    long_description_content_type='text/markdown',
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
    install_requires=[
        'beautifulsoup4==4.11.1',
        'pyppeteer==1.0.2',
    ],
    entry_points={
        'console_scripts': [
            'weread-cli = weread.cli:run'
        ]
    },
    extras_require={
        'headless': [
            'pillow==9.2.0',
            'pyzbar==0.1.9',
            'qrcode==7.3.1',
        ]
    },
    python_requires='>=3.8',
)
