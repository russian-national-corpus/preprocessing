# coding: utf-8

import collections
from modules.lemmer_lru_cache import LemmerLRUCache
from modules.config import CONFIG
import lemmer
import mystem_wrapper
import semantics


class LemmerHolder(object):
    LANGUAGE_MAPPING = {
        # identity mappings for 2-letter ids
        'hy': 'hy',
        'be': 'be',
        'bg': 'bg',
        'cs': 'cs',
        'fr': 'fr',
        'de': 'de',
        'it': 'it',
        'kz': 'kz',
        'pl': 'pl',
        'pt': 'pt',
        'ro': 'ro',
        'ru': 'ru',
        'es': 'es',
        'ta': 'ta',
        'uk': 'uk',
        'en': 'en',
        'et': 'et',
        # mappings for 3-letter ids
        'arm': 'hy',
        'hy2': 'hy',
        'bel': 'be',
        'bul': 'bg',
        'cze': 'cs',
        'fre': 'fr',
        'ger': 'de',
        'ita': 'it',
        'kaz': 'kz',
        'pol': 'pl',
        'por': 'pt',
        'rum': 'rm',
        'rus': 'ru',
        'spa': 'es',
        'tat': 'ta',
        'ukr': 'uk'
    }

    def __init__(self, in_options, in_default_language):
        self.options = in_options
        self.lemmers_cache =\
            LemmerLRUCache(maxsize=CONFIG['max_cached_lemmers'])
        semdict = semantics.SemanticDictionary(self.options.semdict)
        self.semantics = collections.defaultdict(lambda: semantics.SemanticDictionary(None))
        self.semantics['ru'] = semdict
        self.add_fixlists = collections.defaultdict(lambda: '')
        self.add_fixlists['ru'] = self.options.addpath
        self.del_fixlists = collections.defaultdict(lambda: '')
        self.del_fixlists['ru'] = self.options.delpath
        self.default_language = in_default_language
        self.default_lemmer = self.initialize_new_lemmer(self.default_language)

    def get_lemmer(self, in_language):
        if in_language == self.default_language:
            return self.default_lemmer
        if in_language not in self.lemmers_cache:
            self.lemmers_cache[in_language] = self.initialize_new_lemmer(in_language)
        return self.lemmers_cache[in_language]

    def initialize_new_lemmer(self, in_language):
        mystem_language_id = \
            LemmerHolder.LANGUAGE_MAPPING.get(in_language, None)
        if not mystem_language_id:
            return lemmer.DummyLemmer()
        wrapper = mystem_wrapper.MystemWrapper(language=mystem_language_id)
        return lemmer.Lemmer(
            [mystem_language_id],
            dictionary=self.semantics[mystem_language_id],
            addPath=self.add_fixlists[mystem_language_id],
            delPath=self.del_fixlists[mystem_language_id],
            full=self.options.full,
            mystem=wrapper
        )
