#!/usr/bin/env python
# -*- Encoding: windows-1251 -*-

""" Скрипт для обработки (парсинга) файла с описаниями фильтров
(правил разрешения семантической неоднозначности).

Описание фильтров берутся из файла '%(input)s' и записываются в файл '%(output)s'.

Описание каждого правила должно хранится в одной строке
(в строке должно быть не больше одного описания) и удовлетворять следующему формату:
правило
    : описание_контекста ';' описание_результата

описание_контекста
    : описание_контекста '+' сложное_выражение
    | сложное_выражение
сложное_выражение
    : [выражение]                       # выражение не обязательное
    | '[' d1 '..' d2 ']' выражение      # выражение может находиться на расстоянии от d1 до d2 (0 <= d1 <= d2)
выражение
    : выражение '&' выражение           # логическое И, должны выполяняться правое и левое условие
    | выражение '/' выражение           # логическое ИЛИ, слабее по приоритету И
    | '(' выражение ')'                 # группировка выражений
    | ТОКЕН
ТОКЕН - является терминальным символом в разборе, может быть одним из следующего:
    * грамматическое или семантическое значение признака;
    * иметь вид *partOfWord (partOfWord*),
    при этом проверяется что форма слова заканчивается (начинается) с partOfWord;
    * "word" - проверяется на точное совпадение слова с word,
    иначе сравнение производиться с лексеммами слова;
    * @@word - указывает на то, что слово является ключевым
    (т.е. к нему закреплено семантическое описание).
    * "@@word" - слово ключевое, проверка идет на точное совпадение.

описание_результата
    : элемент_результата '||' описание_результата
    | элемент_результата

элемент_результата
    : attribute_name '=' attribute_values

семантические_свойства - строка состоящая из семантических строк,
    в конце строки может приводиться пример ('Ex.: ...');
    на данный момент, примеры удаляются из строки.


Так же, есть ограничения, которые не проверяются, но подразумеваются:
    1) считается, что ключевые слова не могут находиться в опциональной части
    2) несколько слово-форм и лексемы могут всречаться в выражении,
    только если они разделены логическим ИЛИ, и в выражении больше нет других токенов
    (такие правила разбиваются на несколько,
    в которых выражения имеют не более одной форме или лемме).

Про некоторые этапы обработки правила:
    после прочтения описания правила из исходного, строковое описание правила преобразуется
    в несколько правил, которые не содержат выражения с расстояниями или необязательные части
    (таким образом, получается несколько правил с 'фиксированной' длиной).
    При этом добавляется простое правило джокер - оно совпадает с любым словом.

    Далее, происходит токенизация - разбиение строкового описания на токены,
    для каждого элемента разбиения определяется его тип.

    По массиву из токенов, строится несколько массив. Они соответствуют правилам,
    в которых были удалены лишние слово-формы и леммы (см. пункт 2 ограничений).
"""

import codecs
import sys
import os.path
import ply.yacc as yacc
import re

# to reach 'general' module (TODO: this should be somehow avoided...)
sys.path.insert(0, os.path.join('..', '..'))

import general.corpora_defs as corpora_defs

# названия "типов" - эти именна будут писаться в результирующий файл
TYPE_JOKER = 'Joker'
TYPE_NOT = 'Not'
TYPE_GRAMMAR = 'Grammar'
TYPE_SEMANTIC = 'Semantic'
TYPE_LEXEME = 'Lexeme'
TYPE_FORM = 'Form'
TYPE_AND = 'And'
TYPE_OR = 'Or'
TYPE_SENTENCE = 'Phrase'
TYPES = [TYPE_JOKER, TYPE_NOT, TYPE_GRAMMAR, TYPE_SEMANTIC, TYPE_LEXEME, TYPE_FORM, TYPE_AND, TYPE_OR, TYPE_SENTENCE]

class ParseError(ValueError):
    """Class of error raised on parsing."""

def check(condition, info):
    if not condition:
        raise ParseError, info

JOKER = '**'

def RemoveOptionals(rule):
    """ Return a list of lines without square brackets.
    """
    WORDS_SEPARATOR = '+'
    _JOKER_ = ' '.join((JOKER, WORDS_SEPARATOR, ''))
    assert rule.find(JOKER) == -1, "Line contains joker symbol ('%s')" % JOKER

    unresolved = [rule]
    resolved = []
    while len(unresolved) > 0:
        cur = unresolved.pop()
        s, e = cur.find('['), cur.find(']')
        if s == -1:
            check(e == -1, "No appropriate close bracket (']')")
            resolved.append(cur)
            continue

        check(e > s, "Brackets mismatch")
        sub = cur[s+len('['):e] # that is what inside the square brackets
        e += len(']')
        pp = sub.find('..')
        if pp != -1: # if in brakets is a distance
            d0, d1 = int(sub[:pp]), int(sub[pp + len('..'):])
            check(d0 < d1, "Invalid distances") # in fact, d0 <= d1 is acceptable
            FORMAT = cur[:s] + "%s" + cur[e:]
            unresolved.extend(FORMAT % (_JOKER_ * ii) for ii in xrange(d0, d1+1))
        else: # if there is something else
            unresolved.append(cur[:s] + sub + cur[e:]) # optional is explicit
            pl = cur.find(WORDS_SEPARATOR, e)
            if pl != -1: # in case if there is nothing after an 'opt' value
                unresolved.append(cur[:s] + cur[pl+len(WORDS_SEPARATOR):]) # optional is ommited

    return resolved

LITERALS = ('!', '+', '&', '/', '(', ')')

class Tokenizer:
    """ Splits rule's discription into tokens.
    Tokens are printable (repr) objects.
    """

    __TOKENS_SEPARATOR = '#' # вспомогательный символ: нужен для разбиения строки на токены.
    __REPLACES = [(sym, sym.join((__TOKENS_SEPARATOR,) * 2)) for sym in LITERALS]
    __KEYWORD_PREFIX = '@@'

    def tokenize(self, expr):
        assert expr.find(self.__TOKENS_SEPARATOR) == -1 # if this happens, try to change the TOKENS_SEPARATOR
        for pair in self.__REPLACES:
            expr = expr.replace(*pair)

        tokens = []
        for token in expr.split(self.__TOKENS_SEPARATOR):
            token = token.strip()
            if not token:
                continue
            tokens.append(self.__parse(token))

        return tokens

    def __parse(self, token):
        if token in LITERALS:
            return (token, )
        if token == JOKER:
            return (TYPE_JOKER, )
        if corpora_defs.isGrammFeature(token):
            return (TYPE_GRAMMAR, token)
        if corpora_defs.isSemanticFeature(token):
            return (TYPE_SEMANTIC, token)

        token_type = TYPE_LEXEME
        if token.startswith("'"):
            check(token.endswith("'") and token.count("'") == 2, "Inverted commas mismatch (%s)" % token)
            token = token[len("'"):-len("'")]
            token_type = TYPE_FORM

        if token.startswith(self.__KEYWORD_PREFIX):
            return (token_type, token[len(self.__KEYWORD_PREFIX):], True)
        return (token_type, token)

def Simplify(tokens):
    unresolved = [tokens]
    resolved = []
    while len(unresolved) > 0:
        cur = unresolved.pop(0)

        wordCount = 0
        isClear = True
        firstWord = lastWord = 0
        for i, token in enumerate(cur):
            tokenType = token[0]
            if tokenType in (TYPE_LEXEME, TYPE_FORM):
                wordCount += 1
                lastWord = i
                continue
            if tokenType == '/':
                continue
            if tokenType == '+':
                if wordCount > 1:
                    break
                wordCount = 0
                isClear = True
                firstWord = lastWord = i + 1
                continue
            isClear = False

        if wordCount > 1:
            check(isClear, "TOO COMPLEX EXPRESSION")
            check((lastWord - firstWord) == (2 * (wordCount-1)), "Invalid rule discription")
            begin = cur[:firstWord]
            end = cur[lastWord+1:]
            # processing without checks... (we don't check if words interchange with '/')
            unresolved.extend(begin + [cur[w]] + end for w in xrange(firstWord, lastWord+1, 2))
        else:
            resolved.append(cur)
    return resolved

class Token:
    """ Class for interaction between lexer and parser."""
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

class Representer:
    # helper class (used by Lexer): prints strings as is, without quotes
    def __init__(self, strr):
        self.__str = strr

    def __repr__(self):
        return self.__str

class Lexer:
    def __init__(self, tokens, result):
        self.__semPosition = -1

        _tokens = []
        for token in tokens:
            if token[0] in LITERALS:
                _tokens.append(Token(token[0], Operand(token[0])))
                continue
            _tokens.append(Token('TOKEN', Representer(self.__parse(token, result))))

        self.__iter = iter(_tokens)

    def token(self):
        try:
            return self.__iter.next()
        except StopIteration:
            return None

    def __parse(self, token, result):
        if token[0] == TYPE_JOKER:
            return "%s()" % token[0]
        if token[0] in (TYPE_GRAMMAR, TYPE_SEMANTIC):
            return "%s('%s')" % token

        assert token[0] in (TYPE_LEXEME, TYPE_FORM)
        if len(token) == 3:
            return "%s(u'%s', %s)" % (token[0], token[1], result)
        return "%s(u'%s')" % token

class Operand:
    __OP_NAMES = {'&': TYPE_AND, '/': TYPE_OR}

    def __init__(self, op):
        self.op = op
        self.args = []

    def attach(self, left, right=None):
        assert not self.args
        if isinstance(left, Operand) and left.op == self.op:
            self.args.extend(left.args)
        else:
            self.args.append(left)
        if right != None:
            self.args.append(right)

    def __repr__(self):
        if self.op in self.__OP_NAMES.keys():
            return "%s(%s)" % (self.__OP_NAMES[self.op], ', '.join(map(repr, self.args)))
        elif self.op == '!':
            return "%s(%s)" % (TYPE_NOT, ', '.join(map(repr, self.args)))
        return self.op

class SentenceStatement:
    def __init__(self, expr):
        self.args = [expr]

    def append(self, expr):
        self.args.append(expr)

    def __repr__(self):
        return "%s(%s)" % (TYPE_SENTENCE, ', '.join(map(repr, self.args)))

class NotStatement:
    def __init__(self, expr):
        self.args = [expr]

    def append(self, expr):
        self.args.append(expr)

    def __repr__(self):
        return "%s(%s)" % (TYPE_NOT, ', '.join(map(repr, self.args)))

class RuleGrammar:
    tokens = ('TOKEN',)
    literals = LITERALS
    precedence = (
        ('left', '!', '&', '/'),
        )

    def p_statement_expr(self, p):
        """statement : statement '+' expression
                     | expression"""
        if len(p) == 3:
            p[0] = op = p[1]
            assert isinstance(op, NotStatement)
            op.attach(p[2])
        if len(p) == 2:
            p[0] = SentenceStatement(p[1])
        else:
            p[0] = sentence = p[1]
            assert isinstance(sentence, SentenceStatement)
            sentence.append(p[3])

    def p_expression_binop(self, p):
        """expression : '!' expression
                      | expression '&' expression
                      | expression '/' expression
                      | TOKEN"""
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = op = p[1]
            assert isinstance(op, Operand)
            op.attach(p[2])
        else:
            p[0] = op = p[2]
            assert isinstance(op, Operand)
            op.attach(p[1], p[3])

    def p_expression_group(self, p):
        "expression : '(' expression ')'"
        p[0] = p[2]

    def p_error(self, p):
        info = "Syntax error at '%s'" % p.value if p else "Unexpected end of expression"
        check(False, info)

def parseResult(result):
    res = []
    for el in result.split("||"):
        res.append(eval("{'" + el.strip().replace("=", "':").replace("' ", "','") + "}"))
    return res

def produceRules(inpath):
    from rules import Joker, Not, Grammar, Semantic, Lexeme, Form, And, Or, Phrase
    ruleTable = []

    reader = file(inpath, "rb")
    ruleIndex = 0

    tokenizer = Tokenizer()
    parser = yacc.yacc(module = RuleGrammar(), debug = False, write_tables = False)

    for i, line in enumerate(reader):
        lline = line.split(";")
        rule0 = lline[0]
        res = lline[1]

        res = parseResult(res) # список результатов (dict), каждый элемент приписан к одному ключевому слову

        # 'дублируем' правила, содержащие необязательные параметры или расстояния
        #  (таким образом, результируюшие правила имеют фиксированную длину).
        for rule in RemoveOptionals(rule0):
            # построение правил-объектов
            for tokens in Simplify(tokenizer.tokenize(rule)):
                data = str(parser.parse(lexer=Lexer(tokens, res)))
                rule = eval(codecs.getdecoder("windows-1251")(data, "replace")[0])
                rule.initRes(res)
                ruleTable.append(rule)

                ruleIndex += 1

    return ruleTable
