There are three python programs here:

- `decode` translates input sentences from French to English.
- `decode-ext` translates input sentences from French to English with advanced decoder algorithm.
- `compute-model-score` computes the model score of a translated sentence.

You can run `decode` or `decode-ext` with no additional parameters needed. It will automatically translate the input sentences.

These commands work in a pipeline. For example:

    > python decode | python compute-model-score
    > python decode-ext | python compute-model-score

`mt_hw3_writing.tex` and `mt_hw3_writing.pdf` are the writing part of homework3, which describes the motivation, algorithm, and result of the code.