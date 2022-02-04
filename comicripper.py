#!/usr/bin/env python3
import argparse
import concurrent.futures
from io import BytesIO
from lxml import html
import os
from PIL import Image
import requests
import shutil
from zipfile import ZipFile

AGENT = 'Mozilla/5.0 (X11; CrOS x86_64 14324.56.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4692.70 Safari/537.36'
TMP_DIR = '/tmp/comics'
HEADERS = {'User-Agent': AGENT}
VERBOSE = False


class ComicBook:
    headers = HEADERS

    def __init__(self, url, title, pages):
        self.title = title
        self.url = url
        self.pages = pages
        self.numPages = len(pages)

    @classmethod
    def fromUrl(cls, url):
        page = requests.get(url, headers=cls.headers)
        tree = html.fromstring(page.content)
        title = tree.find('.//title').text
        # strip off the garbage at the end of the comic book title
        title = " ".join(title.split()).split(' - Page ')[0].replace(':', ' -')
        pages = tree.xpath('.//div[@id="all"]')[0].xpath('.//img')

        return cls(url, title, pages)


parser = argparse.ArgumentParser(description='Download series of comic books from readcomics.ru.')
parser.add_argument('url', type=str, nargs=1, help='readcomics.ru URL to parse')
parser.add_argument('--overwrite', '-o', action='store_true', default=False, help='overwrite existing files')
parser.add_argument('--single', '-s', action='store_true', default=False, help='process a single comic')
args = parser.parse_args()

def fetch_page(pageNum: int, url: str, tmp_dir: str) -> str:
    file = '%s/%04d.jpg' % (tmp_dir, pageNum)
    r = requests.get(url, headers=HEADERS)
    img = Image.open(BytesIO(r.content))
    img.convert('RGB').save(file, quality=50)

    return file


def fetch_comic(comicBook: ComicBook):
    zipFile = '%s.cbz' % comicBook.title
    if os.path.exists(zipFile) and not args.overwrite:
        print('%s exists, skipping...' % zipFile)
        return
    
    # no pages means no comic book for you!
    if comicBook.numPages <= 0:
        print('Could not find any pages for %s' % comicBook.title)
        exit()

    # create a tmp directory for storing pages
    tmp_dir = os.path.join(TMP_DIR, comicBook.title)
    os.makedirs(tmp_dir)

    # download and zip up the pages
    print('Processing %d pages for %s' % (comicBook.numPages, comicBook.title))

    pagesToZip = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {}
        for i in range(0, comicBook.numPages):
            pageName = comicBook.pages[i].xpath('@alt')[0]
            pageUrl = comicBook.pages[i].xpath('@data-src')[0].strip()
            future_to_url[executor.submit(fetch_page, i + 1, pageUrl, tmp_dir)] = (pageName, pageUrl)
        for future in concurrent.futures.as_completed(future_to_url):
            pageName, pageUrl = future_to_url[future]
            try:
                if VERBOSE: print('Fetched %s from %s' % (pageName, pageUrl))
                pagesToZip.append(future.result())
            except Exception as exc:
                print('%r generated an exception: %s' % (pageUrl, exc))

    print('Zipping pages for %s into %s' % (comicBook.title, zipFile))
    pagesToZip.sort()
    with ZipFile(zipFile, 'w') as cbz:
        for file in pagesToZip:
            if VERBOSE: print('Adding %s to zip' % file)
            cbz.write(file, arcname=os.path.basename(file), compresslevel=9)

    # remove our tmp directory now that we are all done
    shutil.rmtree(tmp_dir)


comicsUrl = args.url[0]
if args.single:
    fetch_comic(comicsUrl)
else:
    page = requests.get(comicsUrl)
    tree = html.fromstring(page.content)
    comicUrls = tree.xpath('.//ul[@class="chapters"]/li/h5/a/@href')
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_comic, ComicBook.fromUrl(comicUrl)): comicUrl for comicUrl in comicUrls}
        for future in concurrent.futures.as_completed(future_to_url):
            comicUrl = future_to_url[future]
            print('%s finished...' % comicUrl)
