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


class Anime(Model):
    """
    存储动画信息
    """
    def __init__(self):
        super().__init__()
        self.rank = 0
        self.title = ''
        self.url = ''
        self.image = ''
        self.score = 0
        self.type = ''
        self.time = ''
        self.members = 0
