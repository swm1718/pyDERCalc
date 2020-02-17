# pyDERCalc

This repository contains Python script for evaluating the performance of speaker diarization systemsin the pyDERCalc.py file along with a demo Jupyter notebook and example files.  It is designed to (a) be give more flexibility on forgiveness collars to be inserted, and anticipates potentially different utterance start collar sizes and utterance end collar sizes, and (b) enable variations to the code to be made more easily to test different things.

pyDERCalc does not permit segments to be excluded (i.e. no unpartitioned evaluations maps (UEM) files), but can otherwise be used to replicate the industry standard diarization evaluation tool ``md-eval.pl`` (Version 22).  That code is part of the NIST scoring toolkit (``sctk-2.4.10``) available at <ftp://jaguar.ncsl.nist.gov/pub/sctk-2.4.10-20151007-1312.tar.bz2>, and also set out in this repository for easy comparison.  It is described in detail in NIST, “The 2009 (RT-09) rich transcription meeting recognition evaluation plan,” Feb. 2009.

The example ground truth segmentation file ``AMI_20050204-1206_GroundTruth.rttm`` was used in the [ ] NIST Rich Transcription challenge.

The example speaker diarization system segmentation file ``AMI_20050204-1206_DiarTkOutput.rttm`` was generated using DiarTk based on the Mel-frequency cepstral coefficients (MFCCs) file ``AMI_20050204-1206.fea`` available at ``https://github.com/idiap/IBDiarization``.  DiarTk is described in D. Vijayasenan and F. Valente, “DiarTk: An open source toolkit for research in multistream speaker diarization and its application to meetings recordings,” in Proc. Conf. of Int. Speech Commun. Assoc. (INTERSPEECH), 2012, pp. 2170–2173.

## Citation

If using pyDERCalc, please cite this paper:

S. McKnight, A. Hogg, P. Naylor, "Analysis of Phonetic Dependence of Segmentation Errors in Speaker Diarization", EUSIPCO 2020 (submitted).

## Requirements

- Python 3
- NumPy
- Pandas

## How To Use

See ``demo.ipynb`` notebook for examples on how to use pyDERCalc.  The main steps are:

- First ``import pyDERCalc``, which may require the path to be added if saved to a different folder from where the code is run.
- Define the path + filenames of the ground truth segmentation file and the diarization system segmentation file.  They are called oracleRttmFile and diarized
- Use ``mapSpkrs, dfErrors, _ = pyDERCalc.getAllErrors(oracleRttmFile, diarizedRttmFile, collars)`` to go straight to the dictionary of mapped speakers and the dataframe table of errors.
- Other commands can be used and modified for individual steps of the process if so desired.

## Explanation

The .rttm files are were devised by NIST for the Rich Transcription challenges that ran from 2002 to 2009.  RTTM stands for rich transcription time-marked files, and are essentially text files setting out each speaker segment on one line.  Each line has either 9 or 10 space-separated entries, which are put into a Python list using getSegs(rttmFile).

Start of ``AMI_20050204-1206_GroundTruth.rttm``:
"SPEAKER AMI_20050204-1206 1 1270.390 4.490 <NA> <NA> FEE029 <NA>
SPEAKER AMI_20050204-1206 1 1275.195 3.070 <NA> <NA> FEE029 <NA>
..."

Start of ``AMI_20050204-1206_DiarTkOutput.rttm``:
"SPEAKER AMI_20050204-1206 1 1270.39 4.50 <NA> <NA> AMI_20050204-1206_spkr_0 <NA>
SPEAKER AMI_20050204-1206 1 1275.19 3.08 <NA> <NA> AMI_20050204-1206_spkr_0 <NA>
..."

COMPLETE
