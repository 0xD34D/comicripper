import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='Comic Ripper',
    version='0.3',
    scripts=[
        'src/cr',
        'src/ComicBook.py',
    ],
    author="Clark Scheff",
    author_email="clark@scheffsblend.com",
    description="Comic book scraper for comics found on readcomicsonline.ru",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/0xD34D/comicripper",
    packages=setuptools.find_packages(),
    install_requires=[
        'ansimarkup',
        'lxml',
        'pillow',
        'requests',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GPLv3',
        'Operating System :: Linux',
    ],
)
