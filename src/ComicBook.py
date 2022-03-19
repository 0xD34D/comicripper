from io import BytesIO
from lxml import html
import requests
from PIL import Image

AGENT = 'Mozilla/5.0 (X11; CrOS x86_64 14324.56.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4692.70 Safari/537.36'
HEADERS = {'User-Agent': AGENT}


class ComicBook:
    headers = HEADERS

    def __init__(self, url: str, title: str, pages: list[str]):
        self.title = title
        self.url = url
        self.pages = pages
        self.numPages = len(pages)

    @classmethod
    def fromUrl(cls, url: str):
        page = requests.get(url, headers=cls.headers)
        tree = html.fromstring(page.content)
        title = tree.find('.//title').text
        # strip off the garbage at the end of the comic book title
        title = ' '.join(title.split()).split(' - Page ')[0].replace(':', ' -')
        pages = tree.xpath('.//div[@id="all"]')[0].xpath('.//img')

        return cls(url, title, pages)


class ComicPage:
    headers = HEADERS

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
        pageName = comicBook.pages[pageNum].xpath('@alt')[0]
        pageUrl = comicBook.pages[pageNum].xpath('@data-src')[0].strip()
        page = ComicPage.fetchPage(pageUrl)

        return cls(page, pageName, pageNum)


def fetchPages(comicBook: ComicBook) -> list[ComicPage]:
    pages = []
    for i in range(0, comicBook.numPages):
        page = ComicPage.fromComicBook(comicBook, i)
        pages.append(page)
    return pages
