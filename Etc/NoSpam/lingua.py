#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 1998, 99, 00, 01, 02, 03 Progiciels Bourbeau-Pinard inc.
# Laurent Bourbeau <bourbeau@progiciels-bpi.ca>, 2001.
# François Pinard <pinard@iro.umontreal.ca>, 2001.

"""\
Natural language recognizer.  (experimental version-3)
"""

import re, sys

class Guesser:

    def __init__(self, debug=False):
        self.debug = debug

    def language(self, text):
        """\
Try to detect the natural language of a written text.
From an idea by Dinu C. Gherman <gherman@darwin.in-berlin.de>, 1999-10-21.
"""
        write = sys.stdout.write
        scores = {}
        from . import tools
        for word in tools.find_words(text):
            if self.debug:
                write("Checking: %s\n" % word)
            languages = compiled_hints['words'].get(word)
            if languages:
                for language in languages:
                    scores[language] = scores.get(language, 0) + 10
                    if self.debug:
                        write("%6d %s for word \"%s\"\n"
                                         % (scores[language], language, word))
            for length, submap in compiled_hints['prefixes'].items():
                if len(word) > length*2:
                    languages = submap.get(word[:length])
                    if languages:
                        for language in languages:
                            scores[language] = scores.get(language, 0) + 1
                            if self.debug:
                                write(
                                    "%6d %s for \"%s\", prefix of \"%s\"\n"
                                    % (scores[language], language,
                                       word[:length], word))
            for length, submap in compiled_hints['suffixes'].items():
                if len(word) > length*2:
                    languages = submap.get(word[-length:])
                    if languages:
                        for language in languages:
                            scores[language] = scores.get(language, 0) + 2
                            if self.debug:
                                write(
                                    "%6d %s for \"%s\", suffix of \"%s\"\n"
                                    % (scores[language], language,
                                       word[-length:], word))
        sorted = [(score, language) for language, score in scores.items()]
        sorted.sort()
        sorted.reverse()
        if self.debug:
            for score, language in sorted:
                write("%6d total score for %s\n"
                                 % (score, language))
        language = None
        if len(sorted) == 1:
            if sorted[0][0] > 180:
                languague = sorted[0][1]
        elif len(sorted) > 1:
            if sorted[0][0] > 240 and sorted[0][0] > 3*sorted[1][0]:
                language = sorted[0][1]
            elif sorted[0][0] > 600 and sorted[0][0] > 2*sorted[1][0]:
                language = sorted[0][1]
        if self.debug:
            if language:
                write("Language is %s\n" % language)
            else:
                write("Language is undecided\n")
        return language
 
# Hints for a few languages.

language_hints = {}

language_hints['English'] = {
    'words': ('the', 'this', 'that', 'these', 'those', 'their', 'an', 'there',
 'i', 'he', 'she', 'it', 'we', 'you', 'they', 'them', 'us', 'one',
 'and', 'or', 'not', 'but', 'either', 'neither', 'never', 'nor',
 'of', 'to', 'for', 'at', 'by', 'in', 'from', 'up', 'out', 'with',
 'as', 'so', 'off', 'after', 'before', 'down', 'over', 'under',
 'are', 'is', 'be', 'been', 'was', 'were', 'have', 'had', 'has',
 'do', 'did', 'does', 'must', 'can', 'could', 'should', 'would',
 'my', 'his', 'her', 'him', 'its', 'your', 'yours', 'our', 'ones',
 'what', 'who', 'which', 'whom', 'whose', 'when', 'where', 'why',
 'how', 'however', 'because', 'while', 'although', 'yet', 'yes',
 'all', 'any', 'each', 'both', 'few', 'some', 'several', 'enough',
 'many', 'much', 'more', 'most', 'less', 'than', 'least', 'own',
 'something', 'everything', 'everyone', 'someone', 'every', 'very',
 'none', 'nothing', 'noboby', 'anybody', 'somebody', 'everybody',
 'altogether', 'together', 'nevertheless', 'during', 'still',
 'if', 'then', 'else', 'also', 'again', 'always', 'about', 'such',
 'now', 'here', 'since', 'back', 'across', 'through', 'often'),
    'prefixes': ('un', 'over', 'under', 'fore', 'out', 'thou', 'be', 'mis'),
    'suffixes': ('ing', 'ed', 'ly', 'ity', 'ful', 'ess', 'ght', 'self',
 'ize', 'fy', 'ee', 'or', 'ever', 'ical', 'eous', 'ious', 'ish',
 'ward', 'wards', 'wise', 'day'),
    }

language_hints['French'] = {
    'words': ('le', 'la', 'les', 'un', 'une', 'des', 'uns',
 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses',
 'moi', 'toi', 'lui', 'eux', 'notre', 'votre', 'leur', 'leurs',
 'se', 'ce', 'ces', 'cette', 'cet', 'ceci', 'cela', 'ça',
 'celui', 'celle', 'celles', 'ceux', 'nos', 'vos', 'nôtre', 'vôtre',
 'et', 'ou', 'où', 'en', 'ne', 'ni', 'non', 'pas', 'sans', 'oui',
 'de', 'à', 'par', 'pour', 'avec', 'dans', 'contre', 'sur',
 'mais', 'donc', 'car', 'si', 'alors', 'sinon', 'même', 'comme',
 'qui', 'que', 'quoi', 'dont', 'quand', 'comment', 'pourquoi',
 'avoir', 'ayant', 'eu', 'ai', 'as', 'avons', 'avez', 'ont',
 'avais', 'avait', 'avions', 'aviez', 'avaient',
 'aurai', 'auras', 'aura', 'aurons', 'aurez', 'auront',
 'aurais', 'aurait', 'aurions', 'auriez', 'auraient',
 'aie', 'aient', 'ayons', 'ayez', 'eue', 'eus', 'eurent',
 'être', 'étant', 'été', 'est', 'suis', 'sont', 'sommes', 'êtes',
 'étais', 'était', 'étions', 'étiez', 'étaient',
 'serai', 'seras', 'sera', 'serons', 'serez', 'seront',
 'serais', 'serait', 'serions', 'seriez', 'seraient',
 'plusieurs', 'tous', 'tout', 'toute', 'toutes', 'quelque', 'quelques',
 'certain', 'certains', 'certaine', 'certaines', 'autre', 'autres',
 'chaque', 'chacun', 'chacune', 'aucun', 'aucune', 'personne',
 'quel', 'quels', 'quelle', 'quelles', 'tel', 'tels', 'telle', 'telles',
 'lequel', 'lesquels', 'laquelle', 'quiconque', 'quelconque',
 'peu', 'beaucoup', 'trop', 'environ', 'presque', 'près', 'bien',
 'autant', 'tant', 'assez', 'aussi', 'très', 'moins', 'plus',
 'mieux', 'meilleur', 'pire', 'tellement', 'vraiment', 'encore',
 'avant', 'après', 'ensuite', 'durant', 'pendant', 'malgré', 'déjà',
 'dessus', 'dessous', 'sous', 'devant', 'derrière', 'dedans', 'vers',
 'toujours', 'jamais', 'parfois', 'souvent', 'ici', 'maintenant',
 'enfin', 'voici', 'voilà', 'afin', 'depuis', 'puis', 'puisque',
 'cependant', 'lorsque',  'quoique', 'toutefois', 'néanmoins',
 'surtout', 'dehors', 'hors', 'quant', 'dès', 'tard', 'tôt'),
    'prefixes': ('l\'', 'd\'', 's\'', 'n\'', 'c\'', 'j\'', 'm\'', 't\'',
 'dé', 'pré', 'contr', 'mal'),
    'suffixes': ('é', 'ée', 'ées', 'ant', 'ants', 'antes',
 'aient', 'iez', 'ont', 'rai', 'rais', 'rait', 'rions',
 'ement', 'ifier', 'iser', 'aux', 'eux', 'euse', 'euses',
 'eur', 'eurs', 'eures', 'rice', 'rices', 'ique', 'iques',
 'isme', 'iste', 'istes', 'tude', 'ive', 'nal', '-ci', '-là'),
    }

language_hints['German'] = {
    'words': ('ich', 'mein', 'mir', 'mich', 'meiner', 'meine', 'meinen',
 'meinem', 'du', 'dein', 'dir', 'dich', 'deiner', 'deine',
 'ihr', 'ihrer', 'ihre', 'ihnen',
 'er', 'seiner', 'ihm', 'ihn', 'sie', 'sich', 'es',
 'wir', 'unser', 'uns', 'unsere', 'euer', 'euch', 'eure',
 'der', 'die', 'das', 'dessen', 'derer', 'denen', 'den', 'dem',
 'ein', 'eines', 'einem', 'einen', 'eine', 'einer', 'eins',
 'dieser', 'diese', 'dieses', 'kein', 'keine', 'keinen',
 'habe', 'haben', 'hast', 'habt', 'sein', 'ist', 'bin',
 'werden', 'wirst', 'wird', 'würde',
 'willst', 'wollen', 'wollt', 'muß', 'mußt', 'müssen', 'müßt',
 'kann', 'kannst', 'können', 'könnt',
 'wo', 'wem', 'wer', 'wen', 'wohin', 'woher', 'wenn',
 'welcher', 'welche', 'welches', 'nicht', 'nichts', 'kein',
 'ab', 'auch', 'aus', 'auf', 'von', 'nach', 'zu', 'bei',
 'gegenüber', 'seit', 'mit', 'durch', 'gegen', 'um', 'entlang',
 'für', 'ohne', 'bis', 'über', 'aber', 'denn', 'und', 'oder',
 'sondern', 'zuerst', 'dann', 'neben', 'über', 'unter', 'vor',
 'zwischen', 'damit', 'ehe', 'bevor'),
    'prefixes': ('dar', 'da', 'wor', 'wo', 'ge', 'ver', 'vor', 'zu', 'miß'
 'auf', 'für', 'bei', 'gut', 'los', 'über', 'haup', 'nahe', 'voll',
 'daran', 'durch', 'entlang', 'gegen', 'gleich', 'mit', 'weg', 'zer',
 'ein', 'zwei', 'drei', 'fünf', 'sechs', 'sieben', 'acht', 'neun'),
    'suffixes': ('ete', 'etest', 'eten', 'etet', 'dem', 'tung', 'heim',
 'zeug', 'ß'),
    }

language_hints['Spanish'] = {
    'words': ('el', 'la', 'las', 'los', 'lo', 'un', 'uno', 'una', 'unos',
 'de', 'del', 'me', 'te', 'se', 'nos', 'os', 'ahí', 'así', 'aquí',
 'yo', 'tú', 'él', 'ellos', 'usted', 'ustedes', 'allí', 'allá',
 'nosotros', 'nosotras', 'nuestro', 'nuestra', 'nuestros', 'nuestras',
 'vosotros', 'vosotras', 'vuestro', 'vuestra', 'vuestros', 'vuestras',
 'cuyo', 'cuya', 'cuyos', 'cuyas', 'suyo', 'suya', 'suyos', 'suyas',
 'mi', 'mí', 'mis', 'mismo', 'mismos', 'mismas', 'tu', 'su', 'sus',
 'ese', 'esa', 'eso', 'ése', 'ésa', 'ésas', 'ésos',
 'este', 'esta', 'esto', 'éste', 'ésta', 'éstas', 'éstos', 'aquel',
 'aquella', 'aquello', 'aquél', 'aquélla', 'aquéllas', 'aquéllos',
 'y', 'u', 'o', 'no', 'sin', 'nada', 'nadie', 'nunca', 'jamás',
 'pero', 'sino', 'pues', 'porque', 'adonde', 'donde', 'dónde',
 'de', 'a', 'con', 'en', 'por', 'para', 'contra', 'dentro', 'hacia',
 'sí', 'si', 'sino', 'entonces', 'cuando', 'cuándo', 'mientras',
 'que', 'qué', 'quien', 'quién', 'quienes', 'quiénes', 'cual', 'cuál',
 'cómo', 'como', 'cuanto', 'alrededor', 'acerca', 'ahora', 'desde',
 'varios', 'varias', 'todo', 'todos', 'toda', 'todas', 'sólo', 'sobre',
 'algún', 'alguna', 'algunas', 'alguno', 'algunos', 'algo', 'alguien',
 'ningún', 'ninguna', 'ninguno', 'tal', 'tales', 'cierta', 'cierto',
 'otro', 'otra', 'otros', 'otras', 'cada', 'quienquiera', 'cualquiera',
 'poco', 'pocos', 'poca', 'pocas', 'más', 'muy', 'casi', 'cerca',
 'mucho', 'muchos', 'mucha', 'muchas', 'tras', 'atrás', 'detrás',
 'después', 'demasiado', 'demasiados', 'demasiadas', 'hasta',
 'menos', 'mejor', 'peor', 'tan', 'tanto', 'tanta', 'tantos', 'tantas',
 'ya', 'además', 'todavía', 'aún', 'aunque', 'también', 'según', 'fin',
 'antes', 'ante', 'adelante', 'bastante', 'delante', 'durante',
 'obstante', 'siempre', 'veces', 'luego', 'afuera', 'fuera', 'tarde',
 'abajo', 'debajo', 'bajo', 'pronto', 'dentro', 'adentro', 'salvo',
 'ser', 'siendo', 'sido',
 'soy', 'eres', 'es', 'somos', 'sois', 'son',
 'era', 'eras', 'éramos', 'erais', 'eran',
 'fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron',
 'seré', 'serás', 'será', 'seremos', 'seréis', 'serán',
 'sería', 'serías', 'seríamos', 'seríais', 'serían',
 'seas', 'seáis', 'sé', 'sea', 'seamos', 'sed', 'sean',
 'fuere', 'fueres', 'fuéremos', 'fuereis', 'fueren',
 'estar', 'estando', 'estado',
 'estoy', 'estás', 'está', 'estamos', 'estáis', 'están',
 'estaba', 'estabas', 'estábamos', 'estabais', 'estaban', 'estuve',
 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron',
 'estaré', 'estarás', 'estará', 'estaremos', 'estaréis', 'estarán',
 'estaría', 'estarías', 'estaríamos', 'estaríais', 'estarían',
 'haber', 'habiendo', 'habido',
 'he', 'has', 'ha', 'hemos', 'habéis', 'han',
 'había', 'habías', 'habíamos', 'habíais', 'habían',
 'hube', 'hubiste', 'hubo', 'hubimos', 'hubisteis', 'hubieron',
 'habré', 'habrás', 'habrá', 'habremos', 'habréis', 'habrán',
 'habría', 'habrías', 'habríamos', 'habríais', 'habrían',
 'tener', 'teniendo', 'tenido', 'tengo', 'tenido', 'tiene', 'tienen',
 'tuve', 'tuvo'),
    'prefixes': ('des', 'contra'),
    'suffixes': ('áis', 'éis', 'án', 'ás', 'ía', 'ías', 'íais', 'ían', 'ó',
 'ón', 'mos', 'ado', 'ando', 'ido', 'iendo', 'aron', 'eron',
 'ico', 'ica', 'ido', 'ida', 'imo', 'ima', 'iso', 'isa', 'ivo', 'iva',
 'ero', 'era', 'oro', 'ora', 'orio', 'oria', 'oso', 'osa',
 'ura', 'uras', 'anza', 'iones', 'ento', 'encia', 'mente',
 'dad'),
    }

def compile_language_hints(language_hints):
    compiled_hints = {}
    compiled_words = compiled_hints['words'] = {}
    compiled_prefixes = compiled_hints['prefixes'] = {}
    compiled_suffixes = compiled_hints['suffixes'] = {}
    for language, map in language_hints.items():
        for word in map['words']:
            languages = compiled_words.get(word) or ()
            if language not in languages:
                compiled_words[word] = languages + (language,)
        for prefix in map['prefixes']:
            submap = compiled_prefixes.get(len(prefix))
            if submap is None:
                submap = compiled_prefixes[len(prefix)] = {}
            languages = submap.get(prefix) or ()
            if language not in languages:
                submap[prefix] = languages + (language,)
        for suffix in map['suffixes']:
            submap = compiled_suffixes.get(len(suffix))
            if submap is None:
                submap = compiled_suffixes[len(suffix)] = {}
            languages = submap.get(suffix) or ()
            if language not in languages:
                submap[suffix] = languages + (language,)
    return compiled_hints

compiled_hints = compile_language_hints(language_hints)

del language_hints, compile_language_hints
