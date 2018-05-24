import asyncio
import hashlib
import os
from urllib.parse import urlparse

import aiohttp
from pyquery import PyQuery as pq

from models import Anime


async def get(session, url):
    """
    第一次下载时缓存到文件, 后续则从缓存中读取
    避免重复下载网页，浪费时间
    """
    cache = cache_for_url(url)

    # 从缓存获取
    if os.path.exists(cache):
        with open(cache, 'rb') as f:
            c = f.read()
            return c

    # 从网络获取
    async with session.get(url) as response:
        # 写入文件前，确保目录存在
        os.makedirs(os.path.dirname(cache), exist_ok=True)

        content = b''
        with open(cache, 'wb') as file:
            chunk_size = 1024
            while True:
                chunk = await response.content.read(chunk_size)
                if len(chunk) > 0:
                    content += chunk
                    file.write(chunk)
                else:
                    break

            return content


def cache_for_url(url):
    """
    对 url 进行 hash 以得到用于缓存的文件路径
    """
    # 尝试从 url 获取后缀名
    path = urlparse(url)[2]
    if '.' in path:
        # http://www.xxx.com/aaa.png?qqq=bbb
        file_ext = path.split('.')[1]
    else:
        # http://www.xxx.com/index?qqq=bbb
        # 姑且不考虑其他没后缀的情况
        file_ext = '.html'

    n = hashlib.sha256(url.encode('ascii')).hexdigest()
    name = '{}.{}'.format(n, file_ext)

    p = os.path.join('cache', name)
    return p


async def fetch(session, url):
    page = await get(session, url)
    rs = await results_from_page(page)
    return rs


async def results_from_page(page):
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
    async with aiohttp.ClientSession() as session:
        fs = []
        for i in range(0, 500, 50):
            url = 'https://myanimelist.net/topanime.php?limit={}'.format(i)
            f = fetch(session, url)
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
