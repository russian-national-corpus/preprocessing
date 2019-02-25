# All rights belong to Non-commercial Partnership "Russian National Corpus"
# http://ruscorpora.ru

# editor marks inside a word
EDITOR_BRACKETS = {'[', ']', '<', '>'}

PRETTY_APOSTROPHE = u'\u2019'
APOSTROPHE = u'\''

ACCENTS = {u'\u0300', u'\u0301'}

def quotetext(s):
  if not s:
    return u''
  return s.replace(u'&', u'&amp;') \
        .replace(u'<', u'&lt;') \
        .replace(u'>', u'&gt;')

def quoteattr(s):
  return quotetext(s).replace(u"'", u'&#39;') \
                     .replace(u'"', u'&#34;') \
                     .replace(u'\n', u'&#xA;') \
                     .replace(u'\r', u'&#xD;') \
                     .replace(u'\t', u'&#x9;')
