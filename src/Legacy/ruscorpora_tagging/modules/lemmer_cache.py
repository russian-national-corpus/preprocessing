class LemmerCache(dict):
    def __init__(self, in_max_length = 500000):
        self.__max_len = in_max_length

    def put(self, (key, value)):
        if len(self.storage) < self.max_len:
            self.storage[key] = value

    def __setitem__(self, key, value):
        if self.__len__() < self.__max_len:
            dict.__setitem__(self, key, value)
