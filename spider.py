import asyncio
from itertools import chain

from pyquery import PyQuery as pq

from models import Anime
from session import Session


async def animes_from_url(url, session):
    page = await session.get(url)

    e = pq(page)
    cells = e('.ranking-list')

    ans = (anime_from_cell(c) for c in cells)
    return ans


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


async def save_image(animes, session):
    tasks = []
    for a in animes:
        print(a)

        url = a.image
        t = session.get(url)
        tasks.append(t)

    await asyncio.wait(tasks)


async def run(**kwargs):
    """
    爬虫执行的入口，构造 url
    """
    async with Session(**kwargs) as session:
        url = 'https://myanimelist.net/topanime.php?limit={}'
        tasks = (animes_from_url(url.format(i), session) for i in range(0, 1000, 50))

        rs = await asyncio.gather(*tasks)
        animes = chain(*rs)

        await save_image(animes, session)


def main():
    config = dict(
        # 缓存目录路径
        cache_dir_path='cache',
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

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(**config))
    loop.close()


if __name__ == '__main__':
    main()
