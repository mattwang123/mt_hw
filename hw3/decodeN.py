#!/usr/bin/env python
import optparse
import sys
import heapq
import models
from collections import namedtuple, defaultdict

optparser = optparse.OptionParser()
optparser.add_option("-i", "--input", dest="input", default="data/input", help="File containing sentences to translate (default=data/input)")
optparser.add_option("-t", "--translation-model", dest="tm", default="data/tm", help="File containing translation model (default=data/tm)")
optparser.add_option("-l", "--language-model", dest="lm", default="data/lm", help="File containing ARPA-format language model (default=data/lm)")
optparser.add_option("-n", "--num_sentences", dest="num_sents", default=sys.maxsize, type="int", help="Number of sentences to decode (default=no limit)")
optparser.add_option("-k", "--translations-per-phrase", dest="k", default=500, type="int", help="Limit on number of translations to consider per phrase (default=30)")
optparser.add_option("-s", "--stack-size", dest="s", default=1000, type="int", help="Maximum stack size (default=100)")
optparser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Verbose mode (default=off)")
opts = optparser.parse_args()[0]

# Load translation and language models
tm = models.TM(opts.tm, opts.k)
lm = models.LM(opts.lm)
french = [tuple(line.strip().split()) for line in open(opts.input).readlines()[:opts.num_sents]]

# Translate unknown words as-is with probability 1
for word in set(sum(french, ())):
    if (word,) not in tm:
        sys.stderr.write(f"WARNING: '{word}' not in translation model! Using as-is.\n")
        tm[(word,)] = [models.phrase(word, 0.0)]  # Fallback: translate as-is

sys.stderr.write(f"Decoding {opts.input} using Optimal Beam Search...\n")

# Namedtuple to store hypotheses
hypothesis = namedtuple("hypothesis", "logprob, lm_state, predecessor, phrase, future_cost, total_cost")

for f in french:
    # Priority queue (heap) for storing hypotheses
    heap = []
    initial_hypothesis = hypothesis(0.0, lm.begin(), None, None, 0.0, 0.0)
    heapq.heappush(heap, (initial_hypothesis.total_cost, initial_hypothesis))

    # Stack to store hypotheses at each position in the sentence
    stacks = [defaultdict(lambda: None) for _ in range(len(f) + 1)]
    stacks[0][lm.begin()] = initial_hypothesis

    # Histogram to track phrase usage
    histogram = defaultdict(int)

    for i in range(len(f)):
        # Sort hypotheses by total cost and keep only top "opts.s" candidates
        current_stack = sorted(stacks[i].values(), key=lambda h: -h.logprob)[:opts.s]

        for h in current_stack:
            for j in range(i + 1, len(f) + 1):
                if f[i:j] in tm:
                    for phrase in tm[f[i:j]]:
                        # Skip if this phrase has been used excessively
                        if histogram[phrase.english] >= opts.k:
                            continue

                        # Compute log probability and language model state for new hypothesis
                        logprob = h.logprob + phrase.logprob
                        lm_state = h.lm_state
                        for word in phrase.english.split():
                            (lm_state, word_logprob) = lm.score(lm_state, word)
                            logprob += word_logprob
                        logprob += lm.end(lm_state) if j == len(f) else 0.0

                        # Compute future cost estimate as heuristic
                        future_cost = sum(max(phrase.logprob for phrase in tm.get((f_word,), [models.phrase(f_word, 0.0)])) for f_word in f[j:])
                        total_cost = logprob + future_cost

                        new_hypothesis = hypothesis(logprob, lm_state, h, phrase, future_cost, total_cost)

                        # Recombination: Only keep the best hypothesis with the same language model state
                        if lm_state not in stacks[j] or stacks[j][lm_state].logprob < logprob:
                            stacks[j][lm_state] = new_hypothesis

                        # Add the hypothesis to the heap
                        heapq.heappush(heap, (new_hypothesis.total_cost, new_hypothesis))

                        # Update histogram for the phrase
                        histogram[phrase.english] += 1

        # Apply dynamic beam size adjustment based on hypothesis scores
        if current_stack:
            best_logprob = current_stack[0].logprob
            threshold = best_logprob - 15.0  # Keep hypotheses within a wider range of the best score
            stacks[i] = {k: v for k, v in stacks[i].items() if v.logprob >= threshold}

    # Check if the final stack is empty, and handle the empty stack case
    if stacks[-1]:
        winner = max(stacks[-1].values(), key=lambda h: h.logprob)
    else:
        # Word-by-word fallback translation if no valid hypotheses
        sys.stderr.write(f"ERROR: No valid hypotheses for sentence: {' '.join(f)}\n")
        fallback_translation = " ".join(f_word if (f_word,) not in tm else tm[(f_word,)][0].english for f_word in f)
        winner = hypothesis(0.0, lm.begin(), None, models.phrase(fallback_translation, 0.0), 0.0, 0.0)

    def extract_english(h):
        return "" if h.predecessor is None else "%s%s " % (extract_english(h.predecessor), h.phrase.english)

    print(extract_english(winner).strip())

    if opts.verbose:
        def extract_tm_logprob(h):
            return 0.0 if h.predecessor is None else h.phrase.logprob + extract_tm_logprob(h.predecessor)
        tm_logprob = extract_tm_logprob(winner)
        sys.stderr.write(f"LM = {winner.logprob - tm_logprob}, TM = {tm_logprob}, Total = {winner.logprob}\n")
