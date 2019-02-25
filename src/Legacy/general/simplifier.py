# -*- Encoding: utf-8 -*-
import sys

# Внутреннее (упрощенное) представление
def simplify_char_inner(c):
  code = ord(c)
  if code == 0x404:   # Ukrainian ie
    return u"Е"
  elif code == 0x454:
    return u"е"
  elif code == 0x47A: # Round omega
    return u"О"
  elif code == 0x47B:
    return u"о"
  elif code == 0x47C: # Omega with titlo
    return u"\u0460"
  elif code == 0x47D:
    return u"\u0461"
  elif code == 0x407: # Yi
    return u"\u0406"
  elif code == 0x457:
    return u"\u0456"
  elif code == 0x476: # Izhitsa with double grave accent
    return u"\u0474"
  elif code == 0x477:
    return u"\u0475"
  elif code in (0x478, 0xA64A): # Uk
    return u"У"
  elif code in (0x479, 0xA64B, 0xE072):
    return u"у"
  elif code in (0x466, 0x46A, 0xA656, 0xE039): # Little yus
    return u"Я"
  elif code in (0x467, 0x46B, 0xA657, 0xE089):
    return u"я"
  elif code in (0x300, 0x301, 0x302, 0x485, 0x486):
    return u""
  elif code in (0x303, 0x311, 0x483, 0x484, 0x487): # Titlo
    return u"" # Tilde?
  else:
    return c

# Модернизированное представление
def simplify_char_modern(c):
  code = ord(c)
  if code in (0x404, 0x462):   # Ukrainian ie, Yat
    return u"Е"
  elif code in (0x454, 0x463):
    return u"е"
  elif code in (0x47A, 0x460, 0x47C): # Round omega, Omega, Omega with titlo
    return u"О"
  elif code in (0x47B, 0x461, 0x47D):
    return u"о"
  elif code == 0x47E: # Ot
    return u"От"
  elif code == 0x47F:
    return u"от"
  elif code in (0x406, 0x407): # Yi
    return u"И"
  elif code in (0x456, 0x457):
    return u"и"
  elif code in (0x474, 0x476): # Izhitsa, Izhitsa with double grave accent
    return u"И"
  elif code in (0x475, 0x477):
    return u"и"
  elif code in (0x478, 0xA64A): # Uk
    return u"У"
  elif code in (0x479, 0xA64B, 0xE072):
    return u"у"
  elif code in (0x466, 0x46A, 0xA656, 0xE039): # Little yus
    return u"Я"
  elif code in (0x467, 0x46B, 0xA657, 0xE089):
    return u"я"
  elif code == 0x405: # Dze
    return u"З"
  elif code == 0x455:
    return u"з"
  elif code == 0x472: # Fita
    return u"Ф"
  elif code == 0x473:
    return u"ф"
  elif code == 0x46E: # Ksi
    return u"Кс"
  elif code == 0x46F:
    return u"кс"
  elif code == 0x470: # Psi
    return u"Пс"
  elif code == 0x471:
    return u"пс"
  elif code in (0x300, 0x301, 0x302, 0x485, 0x486):
    return u""
  elif code in (0x303, 0x311, 0x483, 0x484, 0x487): # Titlo
    return u""
  else:
    return c


def simplify_inner(s):
  res = u""
  for c in s:
    res += simplify_char_inner(c)
  return res


def simplify_modern(s):
  res = u""
  for c in s:
    res += simplify_char_modern(c)
  if (res.endswith(u"ъ") or res.endswith(u"Ъ")):
    res = res[:-1]
  return res


def main():
  while True:
    l = sys.stdin.readline()
    if not l:
      break
    l = l.rstrip().decode("utf-8")
    print simplify_inner(l).encode("utf-8")
    print simplify_modern(l).encode("utf-8")

if __name__ == "__main__":
  main()
