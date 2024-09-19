There are three python programs here (`-h` for usage):

- `./align` aligns words.

- `./check-alignments` checks that the entire dataset is aligned, and
  that there are no out-of-bounds alignment points.

- `./score-alignments` computes alignment error rate.

Besides, the given programs, you can run `IBM_model_one` or `./bidirec_bayesian` as the same way of running `./align`, with no additional parameters needed. It will automatically align the words and create the alignment file.

`mt_hw2_writing` is the writing part of homework2, which describes the motivation, model, and result of the code.