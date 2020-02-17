# pyDERCalc

This repository contains Python script for evaluating the performance of speaker diarization systems in the pyDERCalc.py file along with a demo Jupyter notebook and example files.  It is designed to (a) be give more flexibility on forgiveness collars to be inserted, and anticipates potentially different utterance start collar sizes and utterance end collar sizes, and (b) enable variations to the code to be made more easily to test different things.

pyDERCalc does not permit segments to be excluded (i.e. no unpartitioned evaluations maps (UEM) files), but can otherwise be used to replicate the industry standard diarization evaluation tool ``md-eval.pl`` (Version 22).  That code is part of the NIST scoring toolkit (``sctk-2.4.10``) available at <a href="ftp://jaguar.ncsl.nist.gov/pub/sctk-2.4.10-20151007-1312.tar.bz2">ftp://jaguar.ncsl.nist.gov/pub/sctk-2.4.10-20151007-1312.tar.bz2</a>, and also set out in this repository for easy comparison.  It is described in detail in NIST, “The 2009 (RT-09) rich transcription meeting recognition evaluation plan,” Feb. 2009.

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

The .rttm files are were devised by NIST for the Rich Transcription challenges that ran from 2002 to 2009.  RTTM stands for Rich Transcription Time-marked Files, and are essentially text files setting out each speaker segment on one line.  Each line has either 9 or 10 space-separated entries, which are put into a Python list using getSegs(rttmFile).

Start of ``AMI_20050204-1206_GroundTruth.rttm``:
"SPEAKER AMI_20050204-1206 1 1270.390 4.490 <NA> <NA> FEE029 <NA>
SPEAKER AMI_20050204-1206 1 1275.195 3.070 <NA> <NA> FEE029 <NA>
..."

Start of ``AMI_20050204-1206_DiarTkOutput.rttm``:
"SPEAKER AMI_20050204-1206 1 1270.39 4.50 <NA> <NA> AMI_20050204-1206_spkr_0 <NA>
SPEAKER AMI_20050204-1206 1 1275.19 3.08 <NA> <NA> AMI_20050204-1206_spkr_0 <NA>
..."

The functions ``getSplitSegs(segs)`` and ``iterateSplitSegs(segs)`` are used to find non-overlapping segments that have the same speakers throughout each segment.

The functions ``getComboSplitSegs(segs)`` and ``iterateComboSplitSegs(comboSegs)`` are used to combine the ground truth and diarization system segments to show what speakers are predicted for specific segments by the ground truth files and the diarization system files.

A number of important things can then be obtained from the combined ground truth and diarization system segments ``comboSplitSegs``.  The functions ``getOracleSpkrs(comboSplitSegs)`` and ``getDiarizedSpkrs(comboSplitSegs)`` will obtain the lists of ground truth speakers ``lstOracleSpkrs`` and diarization system speakers ``lstDiarizationSpkrs`` respectively, and they can all be inserted into ``getSpkrTimes(lstOracleSpkrs, lstDiarizedSpkrs, comboSplitSegs)`` to get a dataframe that describes the aggregate ground truth speaker times that map to the diarization speaker times.  The dataframe would look like:

|           | spkr_0 | spkr_1 | spkr_3 | spkr_5 | spkr_6 | spkr_9 |
|-------------------------------------------------------------------
| FEE029 | 194.480 | 13.925 | 12.185 | 14.040 | 2.610 | 7.235 |
| FEE030 | 9.920 | 9.110 | 4.465 | 67.645 | 1.760 | 7.745 |
| MEE031 | 6.445 | 0.570 | 106.655 | 5.105 | 0.000 | 5.020 |
| FEE032 | 9.655 | 1.445 | 4.985 | 7.280 | 0.815 | 138.520 |
-------------------------------------------------------------------

The mapping of ground truth speakers to diarization system speakers using ``getMapSpkrs(lstOracleSpkrs, dfSpkrTimes)`` would look at this dataframe and match the highest values.  

So far, the collar sizes have not been used.  The next step would be to take the input collar sizes, evaluate the segment times to ignore using ``getSegsIgnore(oracleSplitSegs, collars)`` and iterating in ``getNewSegsIgnore(segsIgnore, collars)`` to remove overlaps.  The function ``getRevisedComboSplitSegs(comboSplitSegs, newSegsIgnore)`` would then remove the segment times to ignore from ``comboSplitSegs``.

There are a number of functions that do evaluation.  The starting function ``getTotalTime(segs, countMultipleSpkrs=True)`` will calculate the overall time if ``countMultipleSpeakers`` is set to ``False``, but will double count overlapping time if ``True``. Then the functions ``getMissedTime(segs)``, ``getFalarmTime(segs)`` and ``getErrorTime(segs, mapSpkrs)`` calculate MISS, FALARM and ERROR respectively, before they are all returned at the end using ``getErrors(oracleRttmFile, diarizedRttmFile, collars)``.

There are more unusual functions too, such as ``getCollarSegs(comboSplitSegs, newSegsIgnore)`` and ``getSBDERs(allCollarSegs, mapSpkrs, collars)`` that can calculate the errors in the collars rather than outside.

The function ``getAllErrors(oracleRttmFile, diarizedRttmFile, collars)`` runs the whole process with the least code.
