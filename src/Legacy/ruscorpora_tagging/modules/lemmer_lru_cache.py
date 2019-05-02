from cachetools import LRUCache


class LemmerLRUCache(LRUCache):
    def __init__(self, maxsize, getsizeof=None, evict=None):
        LRUCache.__init__(self, maxsize, getsizeof)
        self.__evict = evict

    def popitem(self):
        key, val = LRUCache.popitem(self)
        val.Reset()
        return key, val
