import asyncio
import hashlib
import os
from urllib.parse import urlparse

from aiohttp import ClientSession
from pyquery import PyQuery as pq

from models import Anime


async def get(url, session):
    """
    第一次下载时缓存到文件, 后续则从缓存中读取
    避免重复下载网页，浪费时间
    """
    cache = cache_for_url(url)

    # 从缓存获取
    if os.path.exists(cache):
        with open(cache, 'rb') as f:
            c = f.read()
            # 检验 cache 的完整性
            # 如不完整则需要重新通过网络 get
            if validate_cache(c):
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
        file_ext = 'html'

    n = hashlib.sha256(url.encode('latin1')).hexdigest()
    name = '{}.{}'.format(n, file_ext)

    p = os.path.join('cache', name)
    return p


def validate_cache(content):
    """
    主要用于判断是否需要重新通过网络 get
    """
    # 暂且只做个简单的长度判断
    return len(content) > 1024


async def fetch(url, session):
    page = await get(url, session)

    e = pq(page)
    cells = e('.ranking-list')

    result = (anime_from_cell(c) for c in cells)
    return result


def anime_from_cell(cell):
    e = pq(cell)
    a = Anime()

    a.rank = int(e('.rank').text())
    a.score = float(e('.score').text())

    te = e('.title')
    a.image = te('img').attr('data-src')
    a.url = te('a').attr('href')

    de = e('.detail')
    a.title = de('a.hoverinfo_trigger').text()

    info = de('.information').text().split('\n')
    a.type = info[0]
    a.time = info[1]
    # 逗号需要手动处理：'1,340,302' => 1340302
    num_str = info[2].split()[0]
    a.members = int(num_str.replace(',', ''))

    return a


async def handle_results(results, session):
    """
    数据处理的入口，存储、计算等
    """
    # 从 results 中递归取出所有的 Anime，然后处理
    tasks = []
    for a in Anime.recursive_iter(results):
        print(a)
        # 保存图片
        t = get(a.image, session)
        tasks.append(t)
        # 下载主页
        t = get(a.url, session)
        tasks.append(t)

    await asyncio.gather(*tasks)


def session_config():
    c = dict(
        # 频繁请求会被服务器拒绝响应
        # 若不及时断开，则会长时间处于等待状态，浪费时间
        # 由于有做缓存，不用担心中断，多次执行程序直到抓取完即可
        read_timeout=5,
        # 如果需要模拟登陆状态，可以直接 copy 浏览器的 cookie
        # hedaers={
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        #                   'AppleWebKit/537.36 (KHTML, like Gecko) '
        #                   'Chrome/62.0.3202.94 Safari/537.36 ',
        #     'Cookie': secret.cookie,
        # },
    )
    return c


async def run():
    """
    爬虫执行的入口，构造 url
    """
    sc = session_config()
    async with ClientSession(**sc) as session:
        url = 'https://myanimelist.net/topanime.php?limit={}'
        tasks = (fetch(url.format(i), session) for i in range(0, 1000, 50))

        rs = await asyncio.gather(*tasks)
        await handle_results(rs, session)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()


if __name__ == '__main__':
    main()
