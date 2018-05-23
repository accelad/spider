import asyncio
import hashlib
import os
from urllib.parse import urlparse

import aiohttp


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
    html = await get(url, cache, **kwargs)
    await parse_html(html.decode())


async def parse_html(html):
    """
    数据分析的入口，解析 dom
    """
    print(html)


async def run():
    """
    爬虫执行的入口，构建 url 和 headers（如果需要）
    """
    cs = []
    for i in range(0, 500, 50):
        url = 'https://myanimelist.net/topanime.php?limit={}'.format(i)
        cs.append(fetch(url))

    await asyncio.wait(cs)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()


if __name__ == '__main__':
    main()
