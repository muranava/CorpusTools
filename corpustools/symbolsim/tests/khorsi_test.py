import unittest

import sys
import os
test_dir = os.path.dirname(os.path.abspath(__file__))
corpustools_path = os.path.split(os.path.split(os.path.split(test_dir)[0])[0])[0]
print(corpustools_path)
sys.path.insert(0, corpustools_path)
from corpustools.corpus.tests.lexicon_test import create_unspecified_test_corpus

from corpustools.symbolsim.khorsi import lcs, make_freq_base
from corpustools.symbolsim.string_similarity import string_similarity

class KhorsiTest(unittest.TestCase):
    def setUp(self):
        self.corpus = create_unspecified_test_corpus()

    def test_freq_base_spelling_type(self):
        expected = {'a':16,
                    'e':3,
                    'h':8,
                    'i':10,
                    'm':6,
                    'n':4,
                    'o':4,
                    's':13,
                    'ʃ':1,
                    't':11,
                    'u':4,
                    'total':80}
        freq_base = make_freq_base(self.corpus,'spelling','type')
        self.assertEqual(freq_base,expected)

        freq_base = self.corpus.get_frequency_base('spelling','type')
        self.assertEqual(freq_base,expected)

    def test_freq_base_spelling_token(self):
        expected = {'a':466,
                    'e':118,
                    'h':538,
                    'i':429,
                    'm':156,
                    'n':142,
                    'o':171,
                    's':856,
                    'ʃ':2,
                    't':271,
                    'u':265,
                    'total':3414}
        freq_base = make_freq_base(self.corpus,'spelling','token')
        self.assertEqual(freq_base,expected)

        freq_base = self.corpus.get_frequency_base('spelling','token')
        self.assertEqual(freq_base,expected)

    def test_freq_base_transcription_type(self):
        expected = {'ɑ':16,
                    'e':3,
                    'i':10,
                    'm':6,
                    'n':4,
                    'o':4,
                    's':5,
                    'ʃ':9,
                    't':11,
                    'u':4,
                    'total':72}
        freq_base = make_freq_base(self.corpus,'transcription','type')
        self.assertEqual(freq_base,expected)

        freq_base = self.corpus.get_frequency_base('transcription','type')
        self.assertEqual(freq_base,expected)

    def test_freq_base_transcription_token(self):
        expected = {'ɑ':466,
                    'e':118,
                    'i':429,
                    'm':156,
                    'n':142,
                    'o':171,
                    's':318,
                    'ʃ':540,
                    't':271,
                    'u':265,
                    'total':2876}
        freq_base = make_freq_base(self.corpus,'transcription','token')
        self.assertEqual(freq_base,expected)

        freq_base = self.corpus.get_frequency_base('transcription','token')
        self.assertEqual(freq_base,expected)

    def test_lcs_spelling(self):
        expected = [('atema','atema','atema',''),
                    ('atema','enuta','e','atmatnua'),
                    ('atema','mashomisi','ma','ateshomisi'),
                    ('atema','mata','ma','ateta'),
                    ('atema','nata','at','emana'),
                    ('atema','sasi','a','temassi'),
                    ('atema','shashi','a','temashshi'),
                    ('atema','shisata','at','emashisa'),
                    ('atema','shushoma','ma','ateshusho'),
                    ('atema','ta','t','aemaa'),
                    ('atema','tatomi','at','ematomi'),
                    ('atema','tishenishu','t','aemaishenishu'),
                    ('atema','toni','t','aemaoni'),
                    ('atema','tusa','t','aemausa'),
                    ('atema','ʃi','','atemaʃi'),
                    ('sasi','atema','a','temassi'),
                    ('sasi','enuta','a','ssienut'),
                    ('sasi','mashomisi','as','simhomisi'),
                    ('sasi','mata','a','ssimta'),
                    ('sasi','nata','a','ssinta'),
                    ('sasi','sasi','sasi',''),
                    ('sasi','shashi','as','sishhi'),
                    ('sasi','shisata','sa','sishita'),
                    ('sasi','shushoma','s','asiahushom'),
                    ('sasi','ta','a','ssit'),
                    ('sasi','tatomi','a','ssittomi'),
                    ('sasi','tishenishu','s','asitihenishu'),
                    ('sasi','toni','i','saston'),
                    ('sasi','tusa','sa','situ'),
                    ('sasi','ʃi','i','sasʃ'),
                    ]
        for v in expected:
            calced = lcs(list(v[0]),list(v[1]))
            calced = (sorted(calced[0]),sorted(calced[1]))
            self.assertEqual(calced,(sorted(v[2]),sorted(v[3])))

    def test_lcs_transcription(self):
        expected = [('atema','atema',['ɑ','t','e','m','ɑ'],[]),
                    ('atema','enuta',['e'],['ɑ','t','m','ɑ','t','n','u','ɑ']),
                    ('atema','mashomisi',['m','ɑ'],['ɑ','t','e','ʃ','o','m','i','s','i']),
                    ('atema','mata',['m','ɑ'],['ɑ','t','e','t','ɑ']),
                    ('atema','nata',['ɑ','t'],['e','m','ɑ','n','ɑ']),
                    ('atema','sasi',['ɑ'],['t','e','m','ɑ','s','s','i']),
                    ('atema','shashi',['ɑ'],['t','e','m','ɑ','ʃ','ʃ','i']),
                    ('atema','shisata',['ɑ','t'],['e','m','ɑ','ʃ','i','s','ɑ']),
                    ('atema','shushoma',['m','ɑ'],['ɑ','t','e','ʃ','u','ʃ','o']),
                    ('atema','ta',['t'],['ɑ','e','m','ɑ','ɑ']),
                    ('atema','tatomi',['ɑ','t'],['e','m','ɑ','t','o','m','i']),
                    ('atema','tishenishu',['t'],['ɑ','e','m','ɑ','i','ʃ','e','n','i','ʃ','u']),
                    ('atema','toni',['t'],['ɑ','e','m','ɑ','o','n','i']),
                    ('atema','tusa',['t'],['ɑ','e','m','ɑ','u','s','ɑ']),
                    ('atema','ʃi',[],['ɑ','t','e','m','ɑ','ʃ','i']),
                    ('sasi','atema',['ɑ'],['t','e','m','ɑ','s','s','i']),
                    ('sasi','enuta',['ɑ'],['s','s','i','e','n','u','t']),
                    ('sasi','mashomisi',['s','i'],['s','ɑ','m','ɑ','ʃ','o','m','i']),
                    ('sasi','mata',['ɑ'],['s','s','i','m','t','ɑ']),
                    ('sasi','nata',['ɑ'],['s','s','i','n','t','ɑ']),
                    ('sasi','sasi',['s','ɑ','s','i'],[]),
                    ('sasi','shashi',['ɑ'],['s','s','i','ʃ','ʃ','i']),
                    ('sasi','shisata',['s','ɑ'],['s','i','ʃ','i','t','ɑ']),
                    ('sasi','shushoma',['ɑ'],['s','s','i','ʃ','u','ʃ','o','m']),
                    ('sasi','ta',['ɑ'],['s','s','i','t']),
                    ('sasi','tatomi',['ɑ'],['s','s','i','t','t','o','m','i']),
                    ('sasi','tishenishu',['i'],['s','ɑ','s','t','ʃ','e','n','i','ʃ','u']),
                    ('sasi','toni',['i'],['s','ɑ','s','t','o','n']),
                    ('sasi','tusa',['s','ɑ'],['s','i','t','u']),
                    ('sasi','ʃi',['i'],['s','ɑ','s','ʃ']),
                    ]
        for v in expected:
            x1 = self.corpus[v[0]].transcription
            x2 = self.corpus[v[1]].transcription
            calced = lcs(x1,x2)
            calced = (calced[0],sorted(calced[1]))
            self.assertEqual(calced,(v[2],sorted(v[3])))


    def test_mass_relate_spelling_type(self):
        expected = [(self.corpus.find('atema'),self.corpus.find('atema'),11.0766887),
                    (self.corpus.find('atema'),self.corpus.find('enuta'),-14.09489383),
                    (self.corpus.find('atema'),self.corpus.find('mashomisi'),-18.35890071),
                    (self.corpus.find('atema'),self.corpus.find('mata'),-6.270847817),
                    (self.corpus.find('atema'),self.corpus.find('nata'),-8.494720336),
                    (self.corpus.find('atema'),self.corpus.find('sasi'),-13.57140897),
                    (self.corpus.find('atema'),self.corpus.find('shashi'),-18.17657916),
                    (self.corpus.find('atema'),self.corpus.find('shisata'),-13.51516925),
                    (self.corpus.find('atema'),self.corpus.find('shushoma'),-16.90806783),
                    (self.corpus.find('atema'),self.corpus.find('ta'),-8.717863887),
                    (self.corpus.find('atema'),self.corpus.find('tatomi'),-13.53912249),
                    (self.corpus.find('atema'),self.corpus.find('tishenishu'),-28.78151269),
                    (self.corpus.find('atema'),self.corpus.find('toni'),-15.17933206),
                    (self.corpus.find('atema'),self.corpus.find('tusa'),-13.53067344),
                    (self.corpus.find('atema'),self.corpus.find('ʃi'),-17.53815687),]
        expected.sort(key=lambda t:t[2])
        expected.reverse()
        calced = string_similarity(self.corpus,'atema','khorsi',sequence_type='spelling',count_what = 'type')
        for i, v in enumerate(expected):
            self.assertAlmostEqual(calced[i][2],v[2])

        expected = [(self.corpus.find('sasi'),self.corpus.find('atema'),-13.57140897),
                    (self.corpus.find('sasi'),self.corpus.find('enuta'),-15.36316844),
                    (self.corpus.find('sasi'),self.corpus.find('mashomisi'),-16.92481569),
                    (self.corpus.find('sasi'),self.corpus.find('mata'),-10.28799462),
                    (self.corpus.find('sasi'),self.corpus.find('nata'),-10.69345973),
                    (self.corpus.find('sasi'),self.corpus.find('sasi'),7.323034009),
                    (self.corpus.find('sasi'),self.corpus.find('shashi'),-8.971692634),
                    (self.corpus.find('sasi'),self.corpus.find('shisata'),-10.26267682),
                    (self.corpus.find('sasi'),self.corpus.find('shushoma'),-20.30229654),
                    (self.corpus.find('sasi'),self.corpus.find('ta'),-6.088289546),
                    (self.corpus.find('sasi'),self.corpus.find('tatomi'),-15.73786189),
                    (self.corpus.find('sasi'),self.corpus.find('tishenishu'),-25.52902026),
                    (self.corpus.find('sasi'),self.corpus.find('toni'),-11.13974683),
                    (self.corpus.find('sasi'),self.corpus.find('tusa'),-5.449867265),
                    (self.corpus.find('sasi'),self.corpus.find('ʃi'),-7.54617756),]
        expected.sort(key=lambda t:t[2])
        expected.reverse()
        calced = string_similarity(self.corpus,'sasi','khorsi',sequence_type='spelling',count_what = 'type')
        for i, v in enumerate(expected):
            self.assertAlmostEqual(calced[i][2],v[2])

    def test_mass_relate_spelling_token(self):
        expected = [(self.corpus.find('atema'),self.corpus.find('atema'),12.9671688),
                    (self.corpus.find('atema'),self.corpus.find('enuta'),-16.49795651),
                    (self.corpus.find('atema'),self.corpus.find('mashomisi'),-17.65533907),
                    (self.corpus.find('atema'),self.corpus.find('mata'),-7.337667817),
                    (self.corpus.find('atema'),self.corpus.find('nata'),-9.088485208),
                    (self.corpus.find('atema'),self.corpus.find('sasi'),-13.8251823),
                    (self.corpus.find('atema'),self.corpus.find('shashi'),-17.52074498),
                    (self.corpus.find('atema'),self.corpus.find('shisata'),-12.59737574),
                    (self.corpus.find('atema'),self.corpus.find('shushoma'),-14.82488063),
                    (self.corpus.find('atema'),self.corpus.find('ta'),-9.8915809),
                    (self.corpus.find('atema'),self.corpus.find('tatomi'),-14.6046824),
                    (self.corpus.find('atema'),self.corpus.find('tishenishu'),-27.61147254),
                    (self.corpus.find('atema'),self.corpus.find('toni'),-16.14809881),
                    (self.corpus.find('atema'),self.corpus.find('tusa'),-13.8308605),
                    (self.corpus.find('atema'),self.corpus.find('ʃi'),-22.4838445)]
        expected.sort(key=lambda t:t[2])
        expected.reverse()
        calced = string_similarity(self.corpus,'atema','khorsi',sequence_type='spelling',count_what = 'token')
        for i, v in enumerate(expected):
            self.assertAlmostEqual(calced[i][2],v[2])

        expected = [(self.corpus.find('sasi'),self.corpus.find('atema'),-13.8251823),
                    (self.corpus.find('sasi'),self.corpus.find('enuta'),-14.48366705),
                    (self.corpus.find('sasi'),self.corpus.find('mashomisi'),-16.62778969),
                    (self.corpus.find('sasi'),self.corpus.find('mata'),-10.46022702),
                    (self.corpus.find('sasi'),self.corpus.find('nata'),-10.55425597),
                    (self.corpus.find('sasi'),self.corpus.find('sasi'),6.832376308),
                    (self.corpus.find('sasi'),self.corpus.find('shashi'),-7.235843913),
                    (self.corpus.find('sasi'),self.corpus.find('shisata'),-9.913037922),
                    (self.corpus.find('sasi'),self.corpus.find('shushoma'),-19.77169406),
                    (self.corpus.find('sasi'),self.corpus.find('ta'),-5.382988852),
                    (self.corpus.find('sasi'),self.corpus.find('tatomi'),-16.07045316),
                    (self.corpus.find('sasi'),self.corpus.find('tishenishu'),-24.92713472),
                    (self.corpus.find('sasi'),self.corpus.find('toni'),-11.39132061),
                    (self.corpus.find('sasi'),self.corpus.find('tusa'),-5.172159875),
                    (self.corpus.find('sasi'),self.corpus.find('ʃi'),-10.12650306)]
        expected.sort(key=lambda t:t[2])
        expected.reverse()
        calced = string_similarity(self.corpus,'sasi','khorsi',sequence_type='spelling',count_what = 'token')
        for i, v in enumerate(expected):
            self.assertAlmostEqual(calced[i][2],v[2])

    def test_mass_relate_transcription_type(self):
        expected = [(self.corpus.find('atema'),self.corpus.find('atema'),10.54988612),
                    (self.corpus.find('atema'),self.corpus.find('enuta'),-13.35737022),
                    (self.corpus.find('atema'),self.corpus.find('mashomisi'),-16.64202823),
                    (self.corpus.find('atema'),self.corpus.find('mata'),-5.95476627),
                    (self.corpus.find('atema'),self.corpus.find('nata'),-8.178638789),
                    (self.corpus.find('atema'),self.corpus.find('sasi'),-14.85026877),
                    (self.corpus.find('atema'),self.corpus.find('shashi'),-13.67469544),
                    (self.corpus.find('atema'),self.corpus.find('shisata'),-12.0090178),
                    (self.corpus.find('atema'),self.corpus.find('shushoma'),-12.51154463),
                    (self.corpus.find('atema'),self.corpus.find('ta'),-8.296421824),
                    (self.corpus.find('atema'),self.corpus.find('tatomi'),-13.01231991),
                    (self.corpus.find('atema'),self.corpus.find('tishenishu'),-23.85818691),
                    (self.corpus.find('atema'),self.corpus.find('toni'),-14.54716897),
                    (self.corpus.find('atema'),self.corpus.find('tusa'),-13.85402179),
                    (self.corpus.find('atema'),self.corpus.find('ʃi'),-14.60340869),]
        expected.sort(key=lambda t:t[2])
        expected.reverse()
        calced = string_similarity(self.corpus,'atema','khorsi',sequence_type='transcription',count_what = 'type')
        for i, v in enumerate(expected):
            self.assertAlmostEqual(calced[i][2],v[2])

        expected = [(self.corpus.find('sasi'),self.corpus.find('atema'),-14.85026877),
                    (self.corpus.find('sasi'),self.corpus.find('enuta'),-16.64202823),
                    (self.corpus.find('sasi'),self.corpus.find('mashomisi'),-12.94778139),
                    (self.corpus.find('sasi'),self.corpus.find('mata'),-11.67221494),
                    (self.corpus.find('sasi'),self.corpus.find('nata'),-12.07768004),
                    (self.corpus.find('sasi'),self.corpus.find('sasi'),8.812614836),
                    (self.corpus.find('sasi'),self.corpus.find('shashi'),-11.93742415),
                    (self.corpus.find('sasi'),self.corpus.find('shisata'),-7.90637444),
                    (self.corpus.find('sasi'),self.corpus.find('shushoma'),-18.22899329),
                    (self.corpus.find('sasi'),self.corpus.find('ta'),-7.683230889),
                    (self.corpus.find('sasi'),self.corpus.find('tatomi'),-16.91136117),
                    (self.corpus.find('sasi'),self.corpus.find('tishenishu'),-21.83498509),
                    (self.corpus.find('sasi'),self.corpus.find('toni'),-12.52396715),
                    (self.corpus.find('sasi'),self.corpus.find('tusa'),-5.239146233),
                    (self.corpus.find('sasi'),self.corpus.find('ʃi'),-6.943894326),]
        expected.sort(key=lambda t:t[2])
        expected.reverse()
        calced = string_similarity(self.corpus,'sasi','khorsi',sequence_type='transcription',count_what = 'type')
        for i, v in enumerate(expected):
            self.assertAlmostEqual(calced[i][2],v[2])

    def test_mass_relate_transcription_token(self):
        expected = [(self.corpus.find('atema'),self.corpus.find('atema'),12.10974787),
                    (self.corpus.find('atema'),self.corpus.find('enuta'),-15.29756722),
                    (self.corpus.find('atema'),self.corpus.find('mashomisi'),-16.05808867),
                    (self.corpus.find('atema'),self.corpus.find('mata'),-8.574032654),
                    (self.corpus.find('atema'),self.corpus.find('nata'),-6.823215263),
                    (self.corpus.find('atema'),self.corpus.find('sasi'),-14.77671518),
                    (self.corpus.find('atema'),self.corpus.find('shashi'),-13.71767966),
                    (self.corpus.find('atema'),self.corpus.find('shisata'),-11.34309371),
                    (self.corpus.find('atema'),self.corpus.find('shushoma'),-11.19329949),
                    (self.corpus.find('atema'),self.corpus.find('ta'),-9.205644162),
                    (self.corpus.find('atema'),self.corpus.find('tatomi'),-13.74726148),
                    (self.corpus.find('atema'),self.corpus.find('tishenishu'),-23.12247048),
                    (self.corpus.find('atema'),self.corpus.find('toni'),-15.1191937),
                    (self.corpus.find('atema'),self.corpus.find('tusa'),-13.79217439),
                    (self.corpus.find('atema'),self.corpus.find('ʃi'),-15.68503325),]
        expected.sort(key=lambda t:t[2])
        expected.reverse()
        calced = string_similarity(self.corpus,'atema','khorsi',sequence_type='transcription',count_what = 'token')
        for i, v in enumerate(expected):
            self.assertAlmostEqual(calced[i][2],v[2])

        expected = [(self.corpus.find('sasi'),self.corpus.find('atema'),-14.77671518),
                    (self.corpus.find('sasi'),self.corpus.find('enuta'),-15.43519993),
                    (self.corpus.find('sasi'),self.corpus.find('mashomisi'),-13.96361833),
                    (self.corpus.find('sasi'),self.corpus.find('mata'),-11.58324408),
                    (self.corpus.find('sasi'),self.corpus.find('nata'),-11.67727303),
                    (self.corpus.find('sasi'),self.corpus.find('sasi'),8.126877557),
                    (self.corpus.find('sasi'),self.corpus.find('shashi'),-9.734809346),
                    (self.corpus.find('sasi'),self.corpus.find('shisata'),-7.840021077),
                    (self.corpus.find('sasi'),self.corpus.find('shushoma'),-15.95332831),
                    (self.corpus.find('sasi'),self.corpus.find('ta'),-6.848974285),
                    (self.corpus.find('sasi'),self.corpus.find('tatomi'),-16.85050186),
                    (self.corpus.find('sasi'),self.corpus.find('tishenishu'),-20.51761446),
                    (self.corpus.find('sasi'),self.corpus.find('toni'),-12.51433768),
                    (self.corpus.find('sasi'),self.corpus.find('tusa'),-4.829191506),
                    (self.corpus.find('sasi'),self.corpus.find('ʃi'),-5.994066536),]
        expected.sort(key=lambda t:t[2])
        expected.reverse()
        calced = string_similarity(self.corpus,'sasi','khorsi',sequence_type='transcription',count_what = 'token')
        for i, v in enumerate(expected):
            self.assertAlmostEqual(calced[i][2],v[2])

if __name__ == '__main__':
    unittest.main()
