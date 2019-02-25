#!/usr/bin/env python
# -*- Encoding: windows-1251 -*-

class Joker:
    anchors = set()
    res = None
    def __init__(self):
        return

    def match(self, word):
        return True

class Not:
    anchors = set()
    res = None
    def __init__(self, predicate):
        self.__predicate = predicate

    def match(self, word):
        return not self.__predicate.match(word)

class Match:
    anchors = set()
    res = None
    def __init__(self, el):
        self.__el = el

    def match(self, word):
        return self.__el in word.table

Grammar = Match
Semantic = Match

class Lexeme:
    def __init__(self, el, res=None):
        self.__el = el
        self.anchors = set([el])
        self.res = res

    def match(self, word):
        return self.__el in word.table

class Form:
    def __init__(self, el, res=None):
        self.__el = "'" + el + "'"
        self.anchors = set([self.__el])
        self.res = res

    def match(self, word):
        return self.__el in word.table

class And:
    def __init__(self, *predicates):
        self.__predicates = predicates
        self.anchors = set()
        self.res = None

        for p in predicates:
            self.anchors.update(p.anchors)
            if p.res is not None:
                assert self.res is None
                self.res = p.res

    def match(self, word):
        for el in self.__predicates:
            if not el.match(word):
                return False
        return True

class Or:
    def __init__(self, *predicates):
        self.__predicates = predicates
        self.anchors = set()
        self.res = None

        for p in predicates:
            self.anchors.update(p.anchors)
            if p.res is not None:
                assert self.res is None
                self.res = p.res

    def match(self, word):
        for el in self.__predicates:
            if el.match(word):
                return True
        return False

class Phrase:
    def __init__(self, *rules):
        self.__rules = rules
        self.anchors = set()
        self.__keysAndRes = [] # (index, res)

        for i, rule in enumerate(rules):
            self.anchors.update(rule.anchors)
            if rule.res is not None:
                self.__keysAndRes.append((i, rule.res))

    def initRes(self, res):
        if len(self.__keysAndRes) == 0: # if there is no anchor add results to all the words
            for i in range(len(self.__rules)):
                self.__keysAndRes.append((i, res))

    def match(self, phrase):
        allMatches = []

        for anchor in range(len(phrase) - len(self.__rules) + 1):
            for i, match in enumerate(self.__rules):
                if not match.match(phrase[anchor + i]):
                    break
            else:
                allMatches.extend((anchor + k, res) for k, res in self.__keysAndRes)

        return allMatches
