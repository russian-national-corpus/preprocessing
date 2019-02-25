from cachetools import LRUCache


class LemmerLRUCache(LRUCache):
    def __init__(self, maxsize, missing=None, getsizeof=None, evict=None):
        LRUCache.__init__(self, maxsize, missing, getsizeof)
        self.__evict = evict

    def popitem(self):
        key, val = LRUCache.popitem(self)
        val.Reset()
        return key, val
