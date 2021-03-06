.. _kullback-leibler:

***************************
Kullback-Leibler Divergence
***************************

.. _about_kl:

About the function
------------------

Another way of measuring the distribution of environments as a proxy for
phonological relationships is the Kullback-Leibler (KL) measure of the
dissimilarity between probability distributions [Kullback1951]_.
Sounds that are distinct phonemes appear in the same environments, that is,
there are minimal or near-minimal, pairs. Allophones, on the other hand,
have complementary distribution, and never appear in the same environment.
Distributions that are identical have a KL score of 0, and the more
dissimilar two distributions, the higher the KL score. Applied to
phonology, the idea is to calculate the probability of two sounds across
all environments in a corpus, and use KL to measure their dissimilarity.
Scores close to 0 suggest that the two sounds are distinct phonemes,
since they occur in many of the same environments (or else there is
extensive free variation). Higher scores represent higher probabilities
that the two sounds are actually allophones. Since KL scores have no
upper bound, it is up to the user to decide what counts as “high enough”
for two sounds to be allophones (this is unlike the predictability of
distribution measure described in :ref:`predictability_of_distribution`). See [Peperkamp2006]_
for a discussion of how to use Z-Scores to make this discrimination.

As with the predictability of distribution measure in :ref:`predictability_of_distribution`, spurious
allophony is also possible, since many sounds happen to have non-overlapping
distributions. As a simple example, vowels and consonants generally have
high KL scores, because they occur in such different environments.
Individual languages might have cases of accidental complementary
distribution too. For example, in English /h/ occurs only initially and
[ŋ] only occurs finally. However, it is not usual to analyze them as
being in allophones of a single underlying phonemes. Instead, there is
a sense that allophones need to be phonetically similar to some degree,
and /h/ and /ŋ/ are simply too dissimilar.

To deal with this problem, [Peperkamp2006]_ suggest two
“linguistic filters” that can be applied, which can help identify
cases of spurious allophones, such as /h/ and /ŋ/. Their filters do
not straightforwardly apply to CorpusTools, since they use 5-dimensional
vectors to represent sounds, while in CorpusTools most sounds have only
binary features. An alternative filter is used instead, and it is
described below.

It is important to note that this function's usefulness depends on the
level of analysis in your transcriptions. In many cases, corpora are
transcribed at a phonemic level of detail, and KL will not be very
informative. For instance, the IPHOD corpus does not distinguish between
aspirated and unaspirated voiceless stops, so you cannot measure their
KL score.

.. _method_kl:

Method of calculation
---------------------

All calculations were adopted from [Peperkamp2006]_. The variables
involves are as follows: s is a segment, *c* is a context, and *C* is the
set of all contexts. The Kullback-Leibler measure of dissimilarity between
the distributions of two segments is the sum for all contexts of the
entropy of the contexts given the segments:

KL Divergence:

:math:`m_{KL}(s_1,s_2) = \sum_{c \in C} P(c|s_1) log (\frac{P(c|s_1)}{P(c|s_2)})
+ P(c|s_2) log(\frac{P(c|s_2)}{P(c|s_1)})`

The notation *P(c|s)* means the probability of context c given segment s,
and it is calculated as follows:

:math:`P(c|s) = \frac{n(c,s) + 1}{n(s) + N}`

...where *n(c,s)* is the number of occurrences of segments *s* in context *c*.
[Peperkamp2006]_ note that this equal to the number of occurrences
of the sequence *sc*, which suggests that they are only looking at the right
hand environment. This is probably because in their test corpora, they were
looking at allophones conditioned by the following segment. PCT provides
the option to look only at the left-hand environment, only at the right-hand
environment, or at both.

[Peperkamp2006]_ then compare the average entropy values of each segment,
in the pair. The segment with the higher entropy is considered to be a
surface representation (SR), i.e. an allophone, while the other is the
underlying representation (UR). In a results window in PCT, this is given
as “Possible UR.” More formally:

:math:`SR = \max_{SR,UR}[\sum_{c} P(c|s) log \frac{P(c|s)}{P(c)}]`

[Peperkamp2006]_ give two linguistic filters for getting rid of spurious
allophones, which rely on sounds be coded as 5-dimensional vectors. In
PCT, this concept as been adopted to deal with binary features. The aim
of the filter is the same, however. In a results window the column labeled
“spurious allophones” gives the result of applying this filter.

The features of the supposed UR and SR are compared. If they differ by
only one feature, they are considered plausibly close enough to be
allophones, assuming the KL score is high enough for this to be
reasonable (which will depend on the corpus and the user's expectations).
In this case, the “spurious allophones?” results will say ‘No.’

If they differ by more than 1 feature, PCT checks to see if there any
other sounds in the corpus that are closer to the SR than the UR is.
For instance, if /p/ and /s/ are compared in the IPHOD corpus, /p/ is
considered the UR and /s/ is the SR. The two sounds differ by two
features, namely [continuant] and [coronal]. There also exists another
sound, /t/, which differs from /s/ by [continuant], but not by [coronal]
(or any other feature). In other words, /t/ is more similar to /s/ than
/p/ is to /s/. If such an “in-between” sound can be found, then in the
“spurious allophones?” column, the results will say ‘Yes.’

If the two sounds differ by more than 1 feature, but no in-between sound
can be found, then the “spurious allophones?” results will say ‘Maybe.’

Note too that a more direct comparison of the acoustic similarity of
sounds can also be conducted using the functions in :ref:`acoustic_similarity`.

.. kl_gui:

Implementing the Kullback-Leibler Divergence function in the GUI
----------------------------------------------------------------

To implement the KL function in the GUI, select “Analysis” / “Calculate
Kullback-Leibler...” and then follow these steps:

1. Pair of sounds: Click on “Add pair of sounds” to open the “Select
   segment pair” dialogue box. The segment choices that are available
   will automatically correspond to all of the unique transcribed
   characters in your corpus; click on “Consonants” and/or “Vowels”
   to see the options. You can select more than one pair of sounds to
   examine in the same environments; each pair of sounds will be treated
   individually. Selecting more than two sounds at a time will run the
   analysis on all possible pairs of those sounds (e.g., selecting [t],
   [s], and [d] will calculate the KL score for [t]~[s], [s]~[d], and
   [t]~[d]).
2. Contexts: Using KL requires a notion of “context,” and there are three
   options: left, right, or both. Consider the example word [atema]. If
   using the “both” option, then this word consists of these environments:
   [#\_t], [a\_e], [t\_m], [e\_a], and [m\_#]. If the left-side option is chosen,
   then only the left-hand side is used, i.e., the word consists of the
   environments [#\_], [a\_], [t\_], [e\_], and [m\_]. If the right-side option
   is chosen, then the environments in the word are [\_t], [\_e], [\_m], [\_a],
   and [\_#]. Note that the word boundaries don’t count as elements of words,
   but can count as parts of environments.
3. Results: Once all selections have been made, click “Calculate
   Kullback-Leibler.” If you want to start a new results table, click
   that button; if you’ve already done at least one calculation and
   want to add new calculations to the same table, select the button
   with “add to current results table.” Results will appear in a pop-up
   window on screen. Each member of the pair is listed, along with which
   context was selected, the entropy of each segment, the KL score, which
   of the two members of the pair is more likely to be the UR (as described
   above), and PCT’s judgment as to whether this is a possible case of
   spurious allophones based on the featural distance.
4. Output file / Saving results: If you want to save the table of results,
   click on “Save to file” at the bottom of the table. This opens up a
   system dialogue box where the directory and name can be selected.

To return to the function dialogue box with your most recently used
selections, click on “Reopen function dialog.” Otherwise, the results
table can be closed and you will be returned to your corpus view.

An example of calculating the KL scores in the Example corpus, with the
sounds [s], [ʃ], [t], [n], [m], [e], [u] selected (and therefore all
pairwise comparisons thereof calculated), examining only right-hand side
contexts:

The “Select segment pair” dialogue box, within the “Kullback-Leibler”
dialogue box:

.. image:: static/segmentpair.png
   :width: 90%
   :align: center

The “Kullback-Leibler” dialogue box, with pairs of sounds and contexts
selected:

.. image:: static/kldialog.png
   :width: 90%
   :align: center

The resulting table of results:

.. image:: static/klresults.png
   :width: 90%
   :align: center
