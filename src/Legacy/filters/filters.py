#!/usr/bin/env python
# -*- Encoding: windows-1251 -*-

import time

class Filter:
    def __init__(self, ruleTable):
        self.__ruleTable = ruleTable
        self.stat = {
            "phrases" : 0,
            "rules" : 0,
            "empty" : 0,
            "matches" : 0,
            "getRulesTime" : 0,
            "matchTime" : 0
        }

        self.__ruleDict = {}

        for i, rule in enumerate(self.__ruleTable):
            for el in rule.anchors:
                self.__ruleDict[el] = self.__ruleDict.get(el, []) + [i]

    def getRules(self, phrase):
        res = set()
        for word in phrase:
            for el in word.table:
                res.update(self.__ruleDict.get(el, []))

        res = list(res)
        res.sort()
        return res

    def getResults(self, phrase):
        self.stat["phrases"] += 1
        ttime = time.time()

        appliableRules = self.getRules(phrase)

        self.stat["getRulesTime"] += time.time() - ttime

        if len(appliableRules) > 0:
            self.stat["rules"] += len(appliableRules)
            ttime = time.time()

            wordsCount = len(phrase)
            matches = [[]] * wordsCount

            for i in appliableRules:
                rule = self.__ruleTable[i]
                match = rule.match(phrase)
                if match:
                    self.stat["matches"] += 1

                    for pos, res in match:
                        assert pos < wordsCount
                        matches[pos] = res

                    break

            self.stat["matchTime"] += time.time() - ttime

            return matches
        else:
            self.stat["empty"] += 1
            return []

def produceRules(inpath):
    import filters_parser

    return filters_parser.produceRules(inpath)
