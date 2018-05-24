import collections


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
        self.rank = 0
        self.title = ''
        self.url = ''
        self.image = ''
        self.score = 0
        self.type = ''
        self.time = ''
        self.members = 0
