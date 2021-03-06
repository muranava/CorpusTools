#fun times with morphological relatedness
import time
import os
from codecs import open

import corpustools.symbolsim.phono_align as pam
from corpustools.symbolsim.string_similarity import (string_similarity,
                                                    )

from .io import print_freqalt_results

def calc_freq_of_alt(corpus, s1, s2, relator_type, count_what,
                    sequence_type='transcription', output_filename = None,
                    min_rel = None, max_rel = None, phono_align = False,
                    min_pairs_okay = False, from_gui=False, stop_check = None,
                    call_back = None):
    """Returns a double that is a measure of the frequency of
    alternation of two sounds in a given corpus

    Parameters
    ----------
    s1: char
        A sound segment, e.g. 's', 't'
    s2: char
        A sound segment
    relator_type: string
        The type of relator to be used to measure relatedness, e.g.
        'string_similarity'
    sequence_type: string
        The type of segments to be used ('spelling' = roman letters,
        'transcription' = IPA symbols)
    count_what: string
        The type of frequency, either 'type' or 'token'
    max_rel: double
        Filters out all words that are higher than max_rel from a relatedness measure
    min_rel: double
        Filters out all words that are lower than min_rel from a relatedness measure
    phono_align: boolean (1 or 0), optional
        1 means 'only count alternations that are likely phonologically aligned,'
        defaults to not force phonological alignment
    min_pairs_okay: boolean (1 or 0), optional
        1 means allow minimal pairs (e.g. in English, 's' and 't' do not
        alternate in minimal pairs,
        so allowing minimal pairs may skew results)

    Returns
    -------
    double
        The frequency of alternation of two sounds in a given corpus
    """

    list_s1 = list()
    list_s2 = list()
    all_words = set()
    if call_back is not None:
        call_back('Finding instances of segments...')
        call_back(0,len(corpus))
        cur = 0
    for w in corpus:
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            cur += 1
            if cur % 100 == 0:
                call_back(cur)
        tier = getattr(w, sequence_type)
        if s1 in tier:
            list_s1.append(w)
            all_words.add(w.spelling)
        if s2 in tier:
            list_s2.append(w)
            all_words.add(w.spelling)



    if call_back is not None:
        call_back('Calculating string similarities...')
        call_back(0,len(list_s1)*len(list_s2))
        cur = 0
    related_list = list()
    if phono_align:
        al = pam.Aligner(features=corpus.specifier)
    for w1 in list_s1:
        for w2 in list_s2:
            if stop_check is not None and stop_check():
                return
            if call_back is not None:
                cur += 1
                if cur % 10000 == 0:
                    #print(len(related_list))
                    call_back(cur)
            if w1 == w2:
                continue
            ss = string_similarity(corpus, (w1,w2), relator_type,
                                                sequence_type = sequence_type,
                                                count_what = count_what)
            if min_rel is not None and ss[0][-1] < min_rel:
                continue
            if max_rel is not None and ss[0][-1] > max_rel:
                continue
            if not min_pairs_okay:
                if len(w1.transcription) == len(w2.transcription):
                    count_diff = 0
                    for i in range(len(w1.transcription)):
                        if w1.transcription[i] != w2.transcription[i]:
                            count_diff += 1
                            if count_diff > 1:
                                break
                    if count_diff == 1:
                        continue
            if phono_align:
                alignment = al.align(w1.transcription, w2.transcription)
                if not al.morpho_related(alignment, s1, s2):
                    continue

            related_list.append(ss[0])

    words_with_alt = set()
    if call_back is not None:
        call_back('Calculating frequency of alternation...')
        call_back(0,len(related_list))
        cur = 0
    for w1, w2, score in related_list:
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            cur += 1
            if cur % 100 == 0:
                call_back(cur)
        words_with_alt.add(w1.spelling) #Hacks
        words_with_alt.add(w2.spelling)

    #Calculate frequency of alternation using sets to ensure no duplicates (i.e. words with both s1 and s2

    freq_of_alt = len(words_with_alt)/len(all_words)

    if output_filename:
        print_freqalt_results(output_filename, related_list)

    return len(all_words), len(words_with_alt), freq_of_alt
