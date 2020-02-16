# pyDERCalc

This repository sets out a Python version of the speaker diarization evaluation code md-eval.pl.  It is designed to (a) be gjve more flexibility on forgiveness collars to be inserted, and anticipates potentially different utterance start collar sizes and utterance end collar sizes, and (b) enable variations to the code to be made more easily to test different things.  It does not permit segments to be excluded (i.e. no UEM files), though that could be achieved if desired by modifying the input ground truth segments and speaker diarization segments files.

