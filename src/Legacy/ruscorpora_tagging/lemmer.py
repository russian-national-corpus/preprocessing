# -*- Encoding: utf-8 -*-

# All rights belong to Non-commercial Partnership "Russian National Corpus"
# http://ruscorpora.ru

import sys
import re
import codecs
from collections import deque
import itertools

import semantics
import mystem_wrapper
import token_transformation


to_encoding = codecs.getencoder("utf-8")
from_encoding = codecs.getdecoder("utf-8")


_Translate = {
    u'indet': u'indef',
    u'part': u'gen2',
    u'irreg': u'',
    u'dual': u'du',
    u'predic-1p-sg': u'perf',
    u'inpraes': u'gNotpast',
    u'praed': u'PRAEDIC',
    u'loc': u'loc2',
    u'abl': u'loc',
    u'predic-1p-pl': u'imperf',
    u'det': u'def',
    u'abbr': u'contr',
    u'dist': u'anom',
    u'impers': u'',
    u'geo': u'topon',
    u'obsol': u'oldused',
    u'parenth': u'PARENTH',
}


_good_grams = {
    u"S", u"A", u"NUM", u"ANUM", u"V", u"ADV", u"PRAEDIC", u"PARENTH",

    u"SPRO", u"APRO", u"PRAEDICPRO", u"ADVPRO",
    u"PR", u"CONJ", u"PART", u"INTJ", u"COM",

    u"nom", u"voc", u"gen", u"gen2", u"dat",
    u"acc", u"acc2", u"ins", u"loc", u"loc2", u"adnum",

    u"indic", u"imper", u"imper2", u"inf", u"partcp", u"ger",
    u"poss", u"comp", u"comp2",
    u"supr", u"plen", u"brev",
    u"praes", u"fut", u"praet", u"aor", u"perf", u"imperf",
    u"tran", u"intr",
    u"sg", u"pl",
    u"1p", u"2p", u"3p",
    u"famn", u"persn", u"patrn",
    u"m", u"f", u"n", u"mf",
    u"act", u"pass", u"med",
    u"anim", u"inan",
    u"pf", u"ipf",

    u"d_flex", u"d_type", u"d_refltype", u"d_refl",
    u"d_part", u"d_contr", u"d_num", u"d_gend", u"d_pref",

    u"norm", u"ciph", u"anom", u"distort", u"bastard",
    u"INIT", u"abbr", u"0",
    u"diallex",
    u"topon",
    u"NONLEX", u"obsc"
}


_CapitalFeatures = {"famn", "persn", "patrn", "topon"}
_DoNotRemoveDuplicates = {"famn", "persn", "patrn", "topon"}

NUMBER_RE = re.compile(ur'-?\d+(?:[.,]\d+)?$')


class Lemmer:
    def __init__(self,
                 langs=[],
                 dictionary=None,
                 addPath="",
                 delPath="",
                 full=False,
                 addLang=False,
                 reallyAdd=False,
                 mystem=None):
        self.langs = langs
        self.dictionary = dictionary
        self.full = full
        self.addLang = addLang
        self.reallyAdd = reallyAdd

        self.Add = {}
        if addPath:
            f = codecs.getreader("utf-8")(file(addPath, "rb"))
            for l in f:
                x = l.replace(u"<ana", "@") \
                     .replace("lex=", "") \
                     .replace("gr=", "") \
                     .replace("/>", "") \
                     .replace(">", "") \
                     .replace("\"", " ") \
                     .replace("=", ",") \
                     .rstrip() \
                     .split("@")
                form = x[0].strip()
                if form not in self.Add:
                    self.Add[form] = []
                for el in x[1:]:
                    s = el.lstrip().rstrip().split()
                    lemma = s[0]
                    gramm = s[1]
                    (head, _, tail) = gramm.partition("(")
                    head = head.split(",")
                    category = head[0]
                    head = set(head)
                    head.discard("")
                    tail = (tail.partition(")")[0]).split("|")
                    res = []
                    for tl in tail:
                        s = set(tl.split(","))
                        s.discard("")
                        res.append(
                            self.createAttrs("", lemma, category, head, s)
                        )
                    self.Add[form].append((lemma, res, 'ru', 'disamb'))
            f.close()

        self.Del = set()
        self.DelPatterns = []
        if delPath:
            f = codecs.getreader("utf-8")(file(delPath, "rb"))
            for l in f:
                x = l.rstrip().split()
                if x[0].endswith("*"):
                    self.DelPatterns.append(
                        (x[0][:-1], x[1], set(x[2].split(',')))
                    )
                else:
                    self.Del.add(tuple(x[0:3]))
            f.close()
        self.mystem = mystem if mystem else mystem_wrapper.MystemWrapper()

    def Reset(self):
        self.mystem.mystem_process.terminate()

    def parse_tokens_context_aware(self, in_tokens, languageFilter=[]):
        is_enclosed = lambda lhs, rhs: rhs[0] <= lhs[0] and lhs[1] <= rhs[1]
        transformed_tokens = []
        transformation_sequences = []
        for token in in_tokens:
            transformed_token, transformation_sequence = \
                token_transformation.transform_token(token)
            transformed_tokens.append(transformed_token)
            transformation_sequences.append(transformation_sequence)
        token_regions = []
        last_position = 0
        for token in transformed_tokens:
            token_regions.append((last_position, last_position + len(token)))
            last_position += len(token) + 1  # 1 for a whitespace

        parsed_tokens = self.mystem.analyze_tokens(transformed_tokens)

        result = []
        for result_slot in in_tokens:
            result.append([])

        last_position = 0
        for parsed_token in parsed_tokens:
            assert 'text' in parsed_token
            token_text = parsed_token['text']
            range_begin, range_end = \
                last_position, last_position + len(token_text)
            token_indices = \
                [index for index in xrange(len(token_regions))
                 if is_enclosed((range_begin, range_end), token_regions[index])]
            if token_indices:
                token_index = token_indices[0]
                token_region_begin, token_region_end = token_regions[token_index]
                relative_region = (range_begin - token_region_begin, range_end - token_region_begin)
                processed_parse_map = self.__process_parse(parsed_token)
                assert (0, 1) in processed_parse_map, 'Invalid parse'
                processed_parse = processed_parse_map[(0, 1)]
                detransformed_token_region, detransformed_token_text = \
                    token_transformation.detransform_token(transformation_sequences[token_index],
                                                           relative_region)
                # if it's not explicitly present in the input and doesn't have a parse as well,
                # it's treated as garbage
                if detransformed_token_text in in_tokens \
                        or self.__has_meaningful_parse(processed_parse) \
                        or re.findall('\w+', detransformed_token_text, re.UNICODE):
                    result[token_index].append((detransformed_token_region, processed_parse))
            last_position += len(token_text)
        return result

    def __get_token_special_symbols_map(self, in_token):
        special_symbol_map = {}
        for special_symbol in Lemmer.SPECIAL_SYMBOLS:
            symbol_indices = [index for index, symbol in enumerate(token) \
                              if symbol == special_symbol]
            if symbol_indices:
                special_symbol_map[special_symbol] = symbol_indices
        return special_symbol_map

    def __has_meaningful_parse(self, in_parses_list):
        for lemma, parses, language, disamb in in_parses_list:
            for parse in parses:
                if parse[0] != 'NONLEX':
                    return True
        return False

    def __process_parse(self, in_parsed_token, languageFilter=[]):
        result = {}

        fixlist_applied = False
        word = in_parsed_token['text'].strip()
        analyses = in_parsed_token.get('analysis', [])
        if not len(word):
            result = {(0, 1): [('?', [('NONLEX', '', '')], 'ru', 'nodisamb')]}
        elif NUMBER_RE.match(word):
            result = {(0, 1): [(word, [('NUM,ciph', '', '')], 'ru', 'disamb')]}
        else:
            lword = word.lower()
            # the table is a dict: (start, end) -> [(lemma, [(gramm, sem, semall)], language)]
            table = {}
            # check if this word has its own special morphological analysis
            temp = self.Add.get(lword, None)
            if temp != None:
                if self.reallyAdd:
                    for el in temp:
                        table[(0, 1)] = table.get((0, 1), []) + [(el[0], el[1], 'ru', 'disamb')]
                else:
                    return {(0, 1): temp}
            else:
                temp = self.Add.get("+" + lword, None)
                if temp != None:
                    for el in temp:
                        table[(0, 1)] = table.get((0, 1), []) + [(el[0], el[1], 'ru', 'disamb')]
            minNormFirst = maxNormLast = None
            for ana_id, ana in zip(itertools.count(), analyses):
                disamb = 'disamb' if not ana_id else 'nodisamb'
                # mystem-powered Lemmer works with exactly one language 
                language = self.langs[0]
                if len(languageFilter) and language not in languageFilter:
                    continue

                # we force mystem to never do tokenization by itself
                first = 0
                last = 1
                lemma = ana['lex']
                unglued_grammars = self.__parse_glued_grammar(ana['gr'])
                lexical_feature = unglued_grammars[0].split('=')[0].split(',')
                form_feature =[grammar.split('=')[1].split(',') for grammar in unglued_grammars]
                head, tail = lexical_feature[:], form_feature[:]

                if not head:
                    head = ['']
                if not tail:
                    tail = ['']

                head = _toLatin(head)
                if word[0].isupper() and not set(head).isdisjoint(_CapitalFeatures):
                    lemma = lemma[0].upper() + lemma[1:]

                ana_bastardness = ana.get('qual', '') == 'bastard'
                if ana_bastardness:
                    head.append("bastard")
                else:
                    head.append("norm")

                category = head[0]
                llemma = lemma.lower()
                if (word, lemma, category) in self.Del \
                    or (lword, llemma, category) in self.Del:
                    fixlist_applied = True
                    continue
                to_delete = False
                lexical_feature_set = \
                    set([_Translate[feature] if feature in _Translate else feature \
                         for feature in lexical_feature])
                for (del_pattern, del_lemma, del_category) in self.DelPatterns:
                    if del_lemma in (lemma, llemma) and \
                         del_category.issubset(set(lexical_feature_set)) and \
                         (word.startswith(del_pattern) or lword.startswith(del_pattern)):
                        to_delete = True
                        break
                if to_delete:
                    fixlist_applied = True
                    continue

                gramm = [] # all grammatic attributes for this lemma
                for i in xrange(len(tail)):
                    t = _toLatin(tail[i])
                    tail[i] = t
                    gramm.extend(t)

                if language == "ru":
                    if "bastard" in head and "PARENTH" in head:
                        continue
                    if self.full: # m + f => mf
                        m = []
                        f = []
                        rest = []
                        for el in tail:
                            if "m" in el:
                                m.append(frozenset([e for e in el if e != "m"]))
                            elif "f" in el:
                                f.append(frozenset([e for e in el if e != "f"]))
                            else:
                                rest.append(el)
                        if set(m) == set(f):
                            tail = [list(e) + ["mf"] for e in m] + rest

                    add = []
                    gramms = frozenset(gramm)
                    if gramms.issuperset({"nom", "gen", "dat", "acc", "ins", "loc"}) \
                       and not gramms.issuperset({"m", "f"}):
                        if self.full:
                            add.append("0")
                        else:
                            add = None
                            gramm = [self.createAttrs(word, lemma, category, head, ["0"], language)]
                    if add != None:
                        gramm = []
                        for el in tail:
                            gramm.append(self.createAttrs(word, lemma, category, head, el + add, language))

                else: # other language
                    gramm = []
                    for el in tail:
                        gr = set(head[1:] + el)
                        gr.discard("")
                        if language in ("en", "ge"):
                            gr.discard("brev")
                            gr.discard("awkw")
                        if language == "ge":
                            if "PR" in gr:
                                gr.discard("dat")
                                gr.discard("gen")
                                gr.discard("acc")
                        if language == "uk" and "gNotpast" in gr:
                            gr.discard("gNotpast")
                            gr.add("fut")
                        gr = list(gr)
                        gr.sort()
                        gr = [category] + gr
                        gramm.append((",".join(gr), "", ""))

                if first == 0 and 1 < last and not ana_bastardness and language == "ru":
                    for rng in table.keys():
                        if rng[1] < last:
                            del table[rng]
                if (first, last) in table:
                    table[(first, last)].append((lemma, gramm, language, disamb))
                else:
                    table[(first, last)] = [(lemma, gramm, language, disamb)]
                if not ana_bastardness and language == "ru":
                    if minNormFirst == None:
                        minNormFirst, maxNormLast = first, last
                    elif first <= minNormFirst and last >= maxNormLast:
                        minNormFirst = first
                        maxNormLast = last

            if not table:
                result = \
                {
                    (0, 1): [(word, [('NONLEX', '', '')], 'ru', 'nodisamb')],
                    'fixlist_applied': str(fixlist_applied)
                }
            else:
                complete_parse_builder = SegmentCoveringParseBuilder()
                # parse segment covering is now made by mystem
                complete_parse = table # complete_parse_builder.buildCompleteParse(word, table)
                # some parts of a compound word are not parsed (rejected or something),
                # falling back to a single 'NONLEX' part
                if not complete_parse:
                    result = {(0, 1): [(word, [('NONLEX', '', '')], 'ru', 'nodisamb')]}
                else:
                    complete_parse = self._removeDuplicates(complete_parse)
                    result = complete_parse
        return result

    def __parse_glued_grammar(self, in_grammar):
        feature_parts = in_grammar.split('=')
        lex_feature = feature_parts[0]
        form_feature = feature_parts[1] if 1 < len(feature_parts) else ''
        form_feature_groups = []

        while form_feature:
            form_head, _, form_tail = form_feature.partition('(')
            if form_head:
                form_feature_groups.append([form_head.strip(',')])
            or_group, _, new_form_tail = form_tail.partition(')')
            or_group = filter(lambda token: len(token), or_group.split('|'))
            if or_group:
                form_feature_groups.append(or_group)
            form_feature = new_form_tail.strip(',')

        result = ['%s=%s' % (lex_feature, ','.join(distinct_form_feature))
                  for distinct_form_feature in itertools.product(*form_feature_groups)]
        if not result:
            result = [lex_feature]
        return result

    def _grammsSets(self, gramms):
        return [(set(gramm.split(",")), set(sem.split(",")), set(sem2.split(",")))
                for (gramm, sem, sem2) in gramms]

    def _isSubset(self, gramms1, gramms2):
        gramms1 = self._grammsSets(gramms1)
        gramms2 = self._grammsSets(gramms2)
        for gramm1 in gramms1:
            isIncluded = False
            for gramm2 in gramms2:
                if gramm1[0].issubset(gramm2[0]) and gramm1[1].issubset(gramm2[1]) and gramm1[2].issubset(gramm2[2]):
                    isIncluded = True
                    break
            if not isIncluded:
                return False
        return True

    def _removeDuplicates(self, table):
        newTable = {}
        for rng in table:
            newAnas = []
            discardIndices = set()
            for i in xrange(len(table[rng])):
                lemma_i, gramms_i, language_i, disamb_i = table[rng][i]
                toRemove = False
                for j in xrange(len(table[rng])):
                    if i == j or j in discardIndices:
                        continue
                    lemma_j, gramms_j, language_j, disamb_j = table[rng][j]
                    if lemma_i == lemma_j and language_i == language_j:
                        if _DoNotRemoveDuplicates.isdisjoint(gramms_j[0]) and self._isSubset(gramms_i, gramms_j):
                            toRemove = True
                            break
                if not toRemove:
                    newAnas.append((lemma_i, gramms_i, language_i, disamb_i))
                else:
                    discardIndices.add(i)
            if len(newAnas) > 0:
                newTable[rng] = newAnas
        return newTable

    def prefixCount(word, prefix):
        if word.startswith(prefix):
            return 1 + prefixCount(word[len(prefix):], prefix)
        return 0

    def createAttrs(self, word, lemma, category, head, tail, language=None):
        def prefixCount(word, prefix):
            if word.startswith(prefix):
                return 1 + prefixCount(word[len(prefix):], prefix)
            return 0

        gramm = list(_fixGramm(category, head, tail))
        if language=="ru" and "imper" in gramm and (word.endswith(u"мте") or word.endswith(u"мтесь")):
            gramm[gramm.index("imper")] = "imper2"
        # comp -> comp2 for words with true prefix "по"
        if language=="ru" and "comp" in gramm and prefixCount(word, u"по") > prefixCount(lemma, u"по"):
            subword = word[2:]
            subanalyses = self.mystem.analyze_token(subword)['analysis']
            for ana in subanalyses:
                ana_first, ana_last = 0, 1
                ana_bastardness = ana.get('qual', '') == 'bastard'
                if ana_first == 0 and ana_last == 1 and not ana_bastardness:
                    form_feature, lexical_feature = [features.split(',')
                                                     for features in ana['gr'].split('=')]
                    subhead = _toLatin(lexical_feature)
                    subtail = set()
                    for ff in form_feature:
                        subtail |= set(_toLatin(ff))
                    if "comp" in subhead or "comp" in subtail:
                        gramm[gramm.index("comp")] = "comp2"
                        break

        if self.addLang and language != None:
            gramm.append(language)
        entry = self.dictionary.get((category + ":" + lemma).lower())
        if entry:
            sem = ""
            semall = ""

            primary_semantics = semantics._semantic_filter(entry.primary_features, category, gramm)
            secondary_semantics = semantics._semantic_filter(entry.secondary_features, category, gramm)

            if primary_semantics:
                sem = " ".join(primary_semantics)
            if secondary_semantics:
                semall = " ".join(secondary_semantics)

            return (",".join(gramm), sem, semall)
        else:
            return (",".join(gramm), "", "")


# given a set of parsed word segments, finds a connected sequence
# of segments with maximal individual length
class SegmentCoveringParseBuilder(object):
    def relative_position(self, in_first, in_second):
        # segments are supposed to be sorted at the input
        if in_second[0] > in_first[1]:
            return 'NOT_ADJACENT'
        if in_first[0] == in_second[0] and in_first[1] <= in_second[1]:
            return 'FIRST_ENCLOSED_BY_SECOND'
        if in_first[0] <= in_second[0] and in_second[1] <= in_first[1]:
            return 'SECOND_ENCLOSED_BY_FIRST'
        if in_second[0] == in_first[1] and in_first[1] < in_second[1]:
            return 'ADJACENT'
        if in_first[0] < in_second[0] and in_second[0] < in_first[1] and in_first[1] < in_second[1]:
            return 'INTERSECTED'

    # building a parse for the entire input phrase by combining partial parses
    def buildCompleteParse(self, in_word, in_parse_table):
        atomic_parts_number = len(re.split('\-+|\'', in_word))

        result_parse = {}
        segments = sorted(in_parse_table.keys())
        # adding fake intervals to make sure we have a connected sequence of intervals
        # from the start to the beginning of the word
        segments = [(0, 0)] + segments + [(atomic_parts_number, atomic_parts_number)]

        result_segments = deque([])
        segment_index = 0
        while segment_index != len(segments):
            interval = segments[segment_index]
            if not len(result_segments):
                result_segments.append(interval)
                segment_index += 1
                continue
            last_interval = result_segments[-1]
            rel_pos = self.relative_position(last_interval, interval)
            if rel_pos == 'FIRST_ENCLOSED_BY_SECOND':
                result_segments.pop()
                result_segments.append(interval)
            elif rel_pos == 'ADJACENT' and interval[0] != interval[1]:
                result_segments.append(interval)
            elif rel_pos == 'NOT_ADJACENT':
                return None
            segment_index += 1

        for result_segment in result_segments:
            result_parse[result_segment] = in_parse_table[result_segment]
        return result_parse


def _toLatin(gramms):
    res = []
    for el in gramms:
        res.append(_Translate.get(el, el))
    return res


def _fixGramm(category, head, tail):
    gramm = set(head)
    gramm.update(tail)

    if "gNotpast" in gramm:
        if "pf" in gramm and "ger" not in gramm:
            gramm.add("fut")
        else:
            gramm.add("praes")

    if {"A", "partcp"}.intersection(gramm) and not {"brev", "supr", "comp"}.intersection(gramm):
        gramm.add("plen")

    if ("V" in gramm) and not ("pass" in gramm):
        gramm.add("act")

    if ("V" in gramm) and not {"imper", "inf", "partcp", "ger"}.intersection(gramm):
        gramm.add("indic")

    if ("obsc" in gramm) and not ("norm" in gramm):
        gramm.discard("obsc")

    if ("S" in gramm) and ("brev" in gramm):
        gramm.discard("brev")

    if "anom" in gramm:
        gramm.discard("norm")

    if ("ADV" in gramm or category == "ADV") and ("PRAEDIC" in gramm or category == "PRAEDIC"):
        gramm.discard("ADV")
        if category == "ADV":
            category = "PRAEDIC"

    if ("ADV" in gramm or category == "ADV") and ("PARENTH" in gramm or category == "PARENTH"):
        gramm.discard("ADV")
        if category == "ADV":
            category = "PARENTH"

    gramm.discard(category)
    gramm.discard("")
    gramm = list(gramm)
    gramm = list(_good_grams.intersection(gramm))
    gramm.sort()
    gramm = [category] + gramm
    if gramm == ["bastard"] or gramm == []:
        gramm.append("NONLEX")
    return gramm


def _badGramms(path):
    out = codecs.getwriter("utf-8")(file(path, "wb"), 'xmlcharrefreplace')
    for (key, val) in _Translate.items():
        if val not in _good_grams:
            out.write("%s;%s;\n" % (key, val))
    out.close()


def main():
    # debug only
    out = codecs.getwriter("utf-8")(sys.stdout, 'xmlcharrefreplace')

    out.write("...\n")
    lemm = Lemmer(langs=['ru'])
    out.write(">\n")

    while True:
        l = sys.stdin.readline()
        if not l:
            break
        ul = codecs.getdecoder("utf-8")(l, "replace")[0]
        parses = lemm.parse_tokens_context_aware(ul.split())
        for token_parses in parses:
            for parse_range, parse_list in token_parses:
                print parse_range
                #for el in parse_list:
                #    out.write("        ")
                #    for ell in el:
                #        out.write("%s " % ell)
                #    out.write("\n")


class DummyLemmer(object):
    def parse_tokens_context_aware(self, in_tokens, in_language_filter=[]):
        result = map(lambda token: [((0, len(token)), [(token, [('NONLEX', '', '')], 'ru', 'nodisamb')])], in_tokens)
        return result

    def Reset(self):
        pass


if __name__ == "__main__":
    main()
