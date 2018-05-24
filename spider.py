import asyncio
import collections
import hashlib
import os
from urllib.parse import urlparse

import aiohttp
from pyquery import PyQuery as pq


class Model:
    """
    数据基类
    暂时只提供类信息的打印功能
    可自行定制 ORM
    """
    def __repr__(self):
        name = self.__class__.__name__
        properties = ('    {}=({})\n'.format(k, v) for k, v in self.__dict__.items())
        s = '\n<{}\n{}>'.format(name, ''.join(properties))
        return s

    @classmethod
    def recursive_iter(cls, iterable):
        """
        递归迭代器，用于迭代嵌套的序列中的 model
        例如：[m1, m2, m3, [m4, m5]] ==> (m1, m2, m3, m4, m5)
        """
        for m in iterable:
            if isinstance(m, cls):
                yield m
            elif isinstance(m, collections.Iterable):
                yield from cls.recursive_iter(m)
            else:
                pass


class Anime(Model):
    """
    存储动画信息
    """
    def __init__(self):
        self.title = ''
        self.image = ''
        self.score = 0
        self.ranked = 0
        self.popularity = 0
        self.members = 0
        self.season = ''
        self.type = ''
        self.studio_or_author = ''
        self.description = ''


async def get(url, cache, **kwargs):
    """
    第一次下载时缓存到文件, 后续则从缓存中读取
    避免重复下载网页，浪费时间
    """
    path = os.path.join('cache', cache)
    # 确保目录存在
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 从缓存获取
    if os.path.exists(path):
        with open(path, 'rb') as f:
            c = f.read()
            return c

    # 从网络获取
    async with aiohttp.ClientSession(**kwargs) as session:
        async with session.get(url) as response:
            content = b''
            with open(path, 'wb') as fd:
                chunk_size = 1024
                while True:
                    chunk = await response.content.read(chunk_size)
                    if len(chunk) > 0:
                        content += chunk
                        fd.write(chunk)
                    else:
                        break

            return content


def cache_for_url(url, ext=None):
    """
    对 url 进行 hash 以得到用于存储的文件名
    """
    if ext is None:
        # 在未指定的情况下尝试从 url 获取后缀名
        # 用于 get 静态资源
        path = urlparse(url)[2]
        # http://www.xxx.com/aaa.png?qqq=bbb
        dot_idx = path.rfind('.')
        # 需要包含后缀的点号
        ext = path[dot_idx-1:]

    name = hashlib.sha256(url.encode('ascii')).hexdigest()
    c = '{}{}'.format(name, ext)
    return c


async def fetch(url, **kwargs):
    cache = cache_for_url(url, '.html')
    page = await get(url, cache, **kwargs)
    return await data_from_page(page)


async def data_from_page(page):
    """
    数据分析的入口，解析 dom
    """
    e = pq(page)
    cells = e('.ranking-list')
    fs = [anime_from_cell(c) for c in cells]

    done, padding = await asyncio.wait(fs)
    rs = (f.result() for f in done)
    return rs


async def anime_from_cell(cell):
    e = pq(cell)
    a = Anime()

    a.ranked = int(e('.rank').text())
    return a


def handle_results(results):
    """
    数据处理的入口，存储、计算等
    """
    # 从 results 中递归取出所有的 Anime
    for a in Anime.recursive_iter(results):
        print(a)


async def run():
    """
    爬虫执行的入口，构建 url 和 headers（如果需要）
    """
    fs = []
    for i in range(0, 500, 50):
        url = 'https://myanimelist.net/topanime.php?limit={}'.format(i)
        f = fetch(url)
        fs.append(f)

    done, padding = await asyncio.wait(fs)
    rs = (f.result() for f in done)
    handle_results(rs)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()


if __name__ == '__main__':
    main()
