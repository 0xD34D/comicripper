from ansimarkup import ansiprint as print
import concurrent.futures
from io import BytesIO
from lxml import html
import requests
from PIL import Image

AGENT = 'Mozilla/5.0 (X11; CrOS x86_64 14324.56.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4692.70 Safari/537.36'
HEADERS = {'User-Agent': AGENT}


class ComicBook:

    def __init__(self, url: str, title: str, pageUrls: list[str]):
        self.title = title
        self.url = url
        self.pagesElements = pageUrls
        self.numPages = len(pageUrls)
        self.pages = []

    @classmethod
    def fromUrl(cls, url: str):
        page = requests.get(url, headers=HEADERS)
        tree = html.fromstring(page.content)
        title = tree.find('.//title').text
        # strip off the garbage at the end of the comic book title
        title = ' '.join(title.split()).split(' - Page ')[0].replace(':', ' -')
        pages = tree.xpath('.//div[@id="all"]')[0].xpath('.//img')

        return cls(url, title, pages)

    def fetchPages(self, verbose: bool):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_page = {
                executor.submit(ComicPage.fromComicBook, self, i): i
                for i in range(0, self.numPages)
            }
            for future in concurrent.futures.as_completed(future_to_page):
                self.pages.append(future.result())
                pageNum = future_to_page[future]
                if verbose:
                    print(
                        f'Downloaded page <b,w,>[</b,w,><b,g,>{pageNum+1}</b,g,><b,r,>/</b,r,><b,g,>{self.numPages}</b,g,><b,w,>]</b,w,> of <b><i>{self.title}</i></b>'
                    )
            self.pages.sort(key=lambda x: x.number)


class ComicPage:

    def __init__(self, pageImage, pageName, pageNumber):
        self.name = pageName
        self.number = pageNumber
        self.image = pageImage

    @staticmethod
    def fetchPage(url: str) -> bytes:
        r = requests.get(url, headers=HEADERS)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        with BytesIO() as output:
            img.save(output, quality=50, format='JPEG')
            return output.getvalue()

    @classmethod
    def fromComicBook(cls, comicBook, pageNum):
        pageName = comicBook.pagesElements[pageNum].xpath('@alt')[0]
        pageUrl = comicBook.pagesElements[pageNum].xpath(
            '@data-src')[0].strip()
        page = ComicPage.fetchPage(pageUrl)

        return cls(page, pageName, pageNum)


def fetchComicBookUrls(comicsUrl: str) -> list[str]:
    page = requests.get(comicsUrl)
    tree = html.fromstring(page.content)
    comicUrls = tree.xpath('.//ul[@class="chapters"]/li/h5/a/@href')

    return comicUrls
