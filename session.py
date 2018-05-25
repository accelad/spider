import hashlib
import os
from urllib.parse import urlparse

from aiohttp import ClientSession


class Session(ClientSession):
    def __init__(self, cache_dir_path='cache', **kwargs):
        super().__init__(**kwargs)
        self.cache_dir_path = cache_dir_path

    async def get(self, url, **kwargs):
        """
        第一次下载时缓存到文件, 后续则从缓存中读取
        避免重复下载网页，浪费时间
        """
        name = hashed_name_for_url(url)
        path = os.path.join(self.cache_dir_path, name)

        # 从缓存获取
        if os.path.exists(path):
            with open(path, 'rb') as f:
                content = f.read()
                # 检验 cache 的完整性
                # 如不完整则需要重新通过网络 get
                if validate_content(content):
                    return content

        # 从网络获取
        async with super().get(url, **kwargs) as r:
            content = await r.content.read()

            # 写入文件前，确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as file:
                    file.write(content)

            return content


def hashed_name_for_url(url):
    """
    对 url 进行 hash 以得到用于缓存的文件名
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
    return name


def validate_content(content):
    """
    主要用于判断是否需要重新通过网络 get
    """
    # 暂且只做个简单的长度判断
    return len(content) > 1024
