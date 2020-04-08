# These are functions used in the calculation of speaker diarization error rates (DERs)

import time
class Timer:
    def __init__(self):
        self.time = time.time()

    def lap(self, name):
        now = time.time()
        print(f"{name} {now - self.time}")
        self.time = now

def getSegs(rttmFile, oracle):
    """
    This function gets the segment start times, segment end times, segment durations and identified/allocated speakers
    from an RTTM file and returns it as a list of segments.  Used for obtaining both ground truth segments and
    speaker diarization system segments.

    Inputs:
    -rttmFile: path + filename of RTTM file in standard NIST format, form "AMI_20050204-1206.rttm"

    Outputs:
    - segs: list of segments in form "[[start time 1, end time 1, duration 1, speaker 1], [...]]"
    """
    import sys
    segs = []
    try:
        with open(str(rttmFile), "r") as f:
            for line in f:
                type, file, chnl, tbeg, tdur, ortho, stype, name, conf = line.split()
                if oracle:
                    segs.append({'tbeg': float(tbeg), 'tend': round(float(tbeg) + float(tdur), 3),
                                 'name': {'oname': [name], 'dname': []}})
                else:
                    segs.append({'tbeg': float(tbeg), 'tend': round(float(tbeg) + float(tdur), 3),
                                 'name': {'oname': [], 'dname': [name]}})
        return segs
    except Exception as e:
        print("You must use RTTM files in the right format.")
        print(e)
        sys.exit(1)


def countOverlaps(array):
    """
    This function takes a segments list and counts how many rows overlap with the next row.  Used in iterative
    functions to determine when to stop.

    Input:
    - array: list of segments, form "[[start time 1, end time 1, duration 1, speaker 1], [...]]"

    Outputs:
    - count: single number showing number of consecutive row overlaps
    """
    count = 0
    for i in range(len(array) - 1):
        if len(array[i]) == 2:
            if array[i][1] > array[i+1][0]:
                count += 1
        else:
            if array[i]['tend'] > array[i+1]['tbeg']:
                count += 1
    return count

def getSplitSegs(segs):
    """
    This function iterates over the segments once and splits out the speakers so that each new segment only has a constant
    number of speakers.  When used in iterateSplitSegs(segs), the iteration is done until countOverlaps(array) is equal
    to 0.

    Inputs:
    - segs: list of segments, form "[[start time 1, end time 1, duration 1, speaker 1], [...]]"

    Outputs:
    - splitSegs: revised list of segments that over one pass splits consecutive overlapping rows into multiple rows with
                 a constant number of speakers in each segment
    """

    events = []
    for index, seg in enumerate(segs):
        events.append({'time': seg['tbeg'], 'type': 'beg', 'seg': index})
        events.append({'time': seg['tend'], 'type': 'end', 'seg': index})

    events.sort(key=lambda e: e['time'])

    splitSegs = []
    active_segs = set()
    last_event = None
    for event in events:
        seg_index = event['seg']

        if active_segs:
            beg_time = last_event['time']
            end_time = event['time']
            splitSegs.append({'tbeg': beg_time, 'tend': end_time,
                              'name': {name_type: sum([segs[x]['name'][name_type] for x in active_segs], []) for
                                       name_type in ['oname', 'dname']}})

        if event['type'] == 'beg':
            active_segs.add(seg_index)

        if event['type'] == 'end':
            active_segs.remove(seg_index)

        last_event = event

    return splitSegs

def getSpkrs(comboSplitSegs, name_type):
    """
    This function returns the list of ground truth speakers.

    Inputs:
    - comboSplitSegs: list of ground truth and diarization segments after all iterations have reduced it to
                      non-overlapping segments with a constant number of speakers in each segment

    Outputs:
    - lstOracleSpkrs: list of ground truth speakers, form: "['FEE029', 'FEE030', 'MEE031', 'FEE032']"
    """

    lstSpkrs =list(set(sum([x['name'][name_type] for x in comboSplitSegs], [])))
    lstSpkrs.sort(key=lambda x:x[-2:])

    return lstSpkrs


def getSpkrTimes(lstOracleSpkrs, lstDiarizedSpkrs, comboSplitSegs):
    """
    This function returns a dataframe that matches the ground truth speaker times with the diarization
    system times.

    Inputs:
    - lstOracleSpkrs: list of ground truth speakers, form: "['FEE029', 'FEE030', 'MEE031', 'FEE032']"
    - lstDiarizedSpkrs: list of diarization system speakers,
                           form: "['AMI_20050204-1206_spkr_0', 'AMI_20050204-1206_spkr_1', 'AMI_20050204-1206_spkr_3',
                        'AMI_20050204-1206_spkr_5', 'AMI_20050204-1206_spkr_6', 'AMI_20050204-1206_spkr_9']"
    - comboSplitSegs: list of ground truth and diarization segments after all iterations have reduced it to
                      non-overlapping segments with a constant number of speakers in each segment

    Outputs:
    - dfSpkrTimes: a Pandas dataframe size len(lstOracleSpkrs) x len(lstDiarizedSpeakrs) that shows how the
                   ground truth and diarization system times match, form:
                   "        spkr_0	spkr_1	spkr_3	spkr_5	spkr_6	spkr_9
                    FEE029	194.480	13.925	12.185	14.040	2.610	7.235
                    FEE030	9.920	9.110	4.465	67.645	1.760	7.745
                    MEE031	6.445	0.570	106.655	5.105	0.000	5.020
                    FEE032	9.655	1.445	4.985	7.280	0.815	138.520"
    """
    import numpy as np
    import pandas as pd

    spkrTimes = np.zeros((len(lstOracleSpkrs), len(lstDiarizedSpkrs)))
    for row in comboSplitSegs:
        for OracleSpkr in row['name']['oname']:
            for DiarizedSpkr in row['name']['dname']:
                spkrTimes[lstOracleSpkrs.index(OracleSpkr)][lstDiarizedSpkrs.index(DiarizedSpkr)] += round(row['tend'] - row['tbeg'], 3)

    dfSpkrTimes = pd.DataFrame(spkrTimes, index=lstOracleSpkrs, columns=lstDiarizedSpkrs)
    return dfSpkrTimes


def getMapSpkrs(lstOracleSpkrs, dfSpkrTimes):
    """
    This function maps ground truth speakers to diarization system speakers on the assumption that
    the maximum time overlaps in dfSpkrTimes reflect the intended mapping.

    Inputs:
    - lstOracleSpkrs: list of ground truth speakers, form: "['FEE029', 'FEE030', 'MEE031', 'FEE032']"
    - dfSpkrTimes: a Pandas dataframe size len(lstOracleSpkrs) x len(lstDiarizedSpeakrs) that shows how the
                   ground truth and diarization system times match, form:
                   "        spkr_0	spkr_1	spkr_3	spkr_5	spkr_6	spkr_9
                    FEE029	194.480	13.925	12.185	14.040	2.610	7.235
                    FEE030	9.920	9.110	4.465	67.645	1.760	7.745
                    MEE031	6.445	0.570	106.655	5.105	0.000	5.020
                    FEE032	9.655	1.445	4.985	7.280	0.815	138.520"

    Outputs:
    - mapSpkrs: a dictionary that with the ground truth speakers as the key and their values as a 1 x 3 list showing
                the mapped speaker, the mapped speaker time and the percentage of time correctly mapped to that speaker,
                form: "{'FEE029': ['AMI_20050204-1206_spkr_0', 194.48, 79.6],
                        'FEE030': ['AMI_20050204-1206_spkr_5', 67.645, 67.2],
                        'MEE031': ['AMI_20050204-1206_spkr_3', 106.655, 86.2],
                        'FEE032': ['AMI_20050204-1206_spkr_9', 138.52, 85.1]}"
    """
    mapSpkrs = {}

    for spkr in lstOracleSpkrs:
        dSpkr = dfSpkrTimes.loc[spkr].idxmax()
        topTime = dfSpkrTimes.loc[spkr].max()
        sumTime = sum(dfSpkrTimes.loc[spkr])
        mapSpkrs[spkr] = [dSpkr, round(topTime, 3), round(100*topTime/sumTime, 1)]

    return mapSpkrs


def getSegsIgnore(oracleSplitSegs, collars):
    """
    This function returns a list of the segment times to ignore based on the input collar sizes.  Note that
    each collar defined as a start collar size and an end collar size, though both can be the same.

    Inputs:
    - oracleSplitSegs: ground truth segments all iterations have reduced it to non-overlapping segments with a
                       constant number of speakers in each segment 
    - collars: list of start collar sizes and end collar sizes in seconds, form "[0.25, 0.25]"

    Outputs:
    - segsIgnore: the list of segment times to ignore, form: "[[1270.14, 1270.64], [1274.63, 1275.88], ...]"
    """
    import numpy as np
    segsIgnore = []
    for index, collar in enumerate(collars):
        segsIgnore.append([])
        for row in oracleSplitSegs:
            segsIgnore[index].append([row['tbeg'] - collar[0], row['tbeg'] + collar[1]])
            segsIgnore[index].append([row['tend'] - collar[0], row['tend'] + collar[1]])
    return segsIgnore



def getNewSegsIgnore(segsIgnore, collars):
    """
    This function removes the overlaps in segsIgnore.

    Inputs:
    - segsIgnore: the list of segments to ignore, form: "[[1270.14, 1270.64], [1274.63, 1275.88], ...]"
    - collars: list of start collar sizes and end collar sizes in seconds, form "[0.25, 0.25]"

    Outputs:
    - count: the number of iterations needed to reduce overlaps to 0
    - newSegsIgnore: the revised list of segments to ignore, form: "[[1270.14, 1270.64], [1274.63, 1275.88], ..."
    """

    newSegsIgnore = [[] for i in range(len(collars))]
    for collar_index, collar in enumerate(collars):

        events = []
        for index, seg in enumerate(segsIgnore[collar_index]):
            events.append({'time': seg[0], 'type': 'beg', 'index': index})
            events.append({'time': seg[1], 'type': 'end', 'index': index})

        events.sort(key=lambda e: e['time'])

        active_segs = set()
        last_event = None
        for event in events:

            if event['type'] == 'beg':
                if len(active_segs) == 0:
                    last_event = event
                active_segs.add(event['index'])

            if event['type'] == 'end':
                active_segs.remove(event['index'])
                if len(active_segs) == 0:
                    beg_time = last_event['time']
                    end_time = event['time']
                    newSegsIgnore[collar_index].append([beg_time, end_time])

    return newSegsIgnore


def getRevisedComboSplitSegs(comboSplitSegs, newSegsIgnore):
    """
    This function removes the segments to ignore from the non-overlapping list of ground truth and diarization
    segments.

    Inputs:
    - comboSplitSegs: list of ground truth and diarization segments after all iterations have reduced it to
                      non-overlapping segments with a constant number of speakers in each segment
    - newSegsIgnore: the non-overlapping list of segments to ignore, form: "[[1270.14, 1270.64], [1274.63, 1275.88], ..."

    Outputs:
    - segs: the revised list of ground truth and diarization segments after removing segments within the collars
    """
    segs = comboSplitSegs.copy()
    newRows = []

    for row in newSegsIgnore:
        for j in range(len(segs)):
            if row[0] <= segs[j]['tbeg'] and row[1] >= segs[j]['tend']:
                segs[j] = {'tbeg': 0, 'tend': 0, 'name': {'oname': [], 'dname': []}}
            elif row[0] <= segs[j]['tbeg'] and row[1] > segs[j]['tbeg'] and row[1] < segs[j]['tend']:
                segs[j] = {'tbeg': row[1], 'tend': segs[j]['tend'], 'name': segs[j]['name']}
            elif row[0] > segs[j]['tbeg'] and row[0] < segs[j]['tend'] and row[1] >= segs[j]['tend']:
                segs[j] = {'tbeg': segs[j]['tbeg'], 'tend': row[0], 'name': segs[j]['name']}
            elif row[0] > segs[j]['tbeg'] and row[0] < segs[j]['tend'] and row[1] < segs[j]['tend']:
                segs[j] = {'tbeg': segs[j]['tbeg'], 'tend': row[0], 'name': segs[j]['name']}
                newRows.append({'tbeg': row[1], 'tend': segs[j]['tend'], 'name': segs[j]['name']})

    segs = segs + newRows
    segs.sort(key=lambda x:x['tbeg'])

    for i in reversed(range(len(segs))):
        if segs[i] == {'tbeg': 0, 'tend': 0, 'name': {'oname': [], 'dname': []}}:
            del segs[i]

    return segs


def getTotalTime(segs, countMultipleSpkrs=True):
    """
    This function counts the overall ground truth time after removing the collars.  An option allows overlapping
    speaker time to be double counted or not.

    Inputs:
    - segs: the list of ground truth and diarization segments after removing segments within the collars
    - countMultipleSpeakers: a Boolean option to double count overlapping ground truth speaker time (i.e. all time
                             spoken by ground truth speakers v. time in which ground truth speakers are speaking),
                             default "True"

    Outputs:
    - time: aggregate ground truth speaker time in seconds, form: "408.565" (multiple on) or "400.01" (multiple off)
    """
    time = 0
    for row in segs:
        if countMultipleSpkrs == False:
            time += row['tend'] - row['tbeg']
        else:
            time += (row['tend'] - row['tbeg']) * len(row['name']['oname'])
    #time = round(time, 3)
    return time


def getMissedTime(segs):
    """
    This function calculates the aggregate time missed by the speaker diarization system.

    Inputs:
    - segs: the list of ground truth and diarization segments after removing segments within the collars

    Outputs:
    - missedTime: aggregate time missed by the speaker diarization system in seconds, form: "8.555"
    """
    missedTime = 0
    for row in segs:
        # No speaker identified
        if row['name']['oname'] != [] and row['name']['dname'] == []:
            missedTime += row['tend'] - row['tbeg']
        # More than one oracle speaker mapped to only one speaker
        if len(row['name']['oname']) > 1:
            missedTime += (len(row['name']['oname'])-1) * (row['tend'] - row['tbeg'])

    #round(missedTime, 3)
    return missedTime


def getFalarmTime(segs):
    """
    This function calculates the aggregate false alarm time generated by the speaker diarization system.

    Inputs:
    - segs: the list of ground truth and diarization segments after removing segments within the collars

    Outputs:
    - falarmTime: the aggregate false alarm time generated by the speaker diarization system in seconds, form: "0"
    """
    falarmTime = 0
    for row in segs:
        if row['name']['oname'] == [] and row['name']['dname'] != []:
            falarmTime += row['tend'] - row['tbeg']
    #falarmTime = round(falarmTime, 3)
    return falarmTime


def getErrorTime(segs, mapSpkrs):
    """
    This function calculates the speaker error time generated by the speaker diarization system.  This involves
    iterating over all ground truth speakers identified for the relevant segment and then, if none of those speakers
    are mapped to the speaker diarization system speaker, that time will be counted as error time.

    Inputs:
    - segs: the list of ground truth and diarization segments after removing segments within the collars
    - mapSpkrs: a dictionary that with the ground truth speakers as the key and their values as a 1 x 3 list showing
                the mapped speaker, the mapped speaker time and the percentage of time correctly mapped to that speaker,
                form: "{'FEE029': ['AMI_20050204-1206_spkr_0', 194.48, 79.6],
                        'FEE030': ['AMI_20050204-1206_spkr_5', 67.645, 67.2],
                        'MEE031': ['AMI_20050204-1206_spkr_3', 106.655, 86.2],
                        'FEE032': ['AMI_20050204-1206_spkr_9', 138.52, 85.1]}" 

    Outputs:
    - errorTime: the aggregate speaker error time generated by the speaker diarization system in seconds, form: "27.37"
    """
    errorTime = 0
    for row in segs:
        # Ignore rows where no speakers identified by either ground truth and diarization system
        if row['name']['oname'] != [] and row['name']['dname'] != []:
            hit = False
            # Look at all ground truth speakers identified
            for i in range(len(row['name']['oname'])):
                # If any of the ground truth speakers are mapped to the diarization system speaker, then there is no error
                if mapSpkrs[row['name']['oname'][i]][0] in row['name']['dname']:
                    hit = True
            # If none of the ground truth speakers are mapped to the diarization system speaker, then there is an error
            # and the time is added to errorTime
            if hit == False:
                errorTime += row['tend'] - row['tbeg']
    #errorTime = round(errorTime, 3)
    return errorTime


def getCollarSegs(comboSplitSegs, newSegsIgnore):
    """
    This function reverses the usual approach to forgiveness collars - instead of taking the segments outside the
    collars, this function returns the segments within the collars.

    Inputs:
    - comboSplitSegs: list of ground truth and diarization segments after all iterations have reduced it to
                      non-overlapping segments with a constant number of speakers in each segment
    - newSegsIgnore: the non-overlapping list of segments to ignore, form: "[[1270.14, 1270.64], [1274.63, 1275.88], ..."

    Outputs:
    - collarSegs: list of segments within the collars, form: "[[1270.35, 1270.45], [1275.084, 1275.184], ...]"
    """
    segs = comboSplitSegs.copy()
    collarSegs = []

    # Using newSegsIgnore as before, but this time taking the portions within them
    for row in newSegsIgnore:
        for j in range(len(segs)):
            if row[0] <= segs[j]['tbeg'] and row[1] >= segs[j]['tend']:
                collarSegs.append(segs[j])
            elif row[0] <= segs[j]['tbeg'] and row[1] > segs[j]['tbeg'] and row[1] < segs[j]['tend']:
                collarSegs.append({'tbeg': segs[j]['tbeg'], 'tend': row[1], 'name': segs[j]['name']})
            elif row[0] > segs[j]['tbeg'] and row[0] < segs[j]['tend'] and row[1] >= segs[j]['tend']:
                collarSegs.append({'tbeg': row[0], 'tend': segs[j]['tend'], 'name': segs[j]['name']})
            elif row[0] > segs[j]['tbeg'] and row[0] < segs[j]['tend'] and row[1] < segs[j]['tend']:
                collarSegs.append({'tbeg': row[0], 'tend': row[1], 'name': segs[j]['name']})

    collarSegs.sort(key=lambda x:x['tbeg'])
    return collarSegs


def getErrors(revisedComboSplitSegs, mapSpkrs, collars):
    """
    This function returns a list of lists of all the errors and a dataframe.

    Inputs:
    - revisedComboSplitSegs: list of ground truth and diarization segments after all iterations have reduced it to
                             non-overlapping segments with a constant number of speakers in each segment
    - mapSpkrs: a dictionary that with the ground truth speakers as the key and their values as a 1 x 3 list showing
                the mapped speaker, the mapped speaker time and the percentage of time correctly mapped to that speaker,
                form: "{'FEE029': ['AMI_20050204-1206_spkr_0', 194.48, 79.6],
                        'FEE030': ['AMI_20050204-1206_spkr_5', 67.645, 67.2],
                        'MEE031': ['AMI_20050204-1206_spkr_3', 106.655, 86.2],
                        'FEE032': ['AMI_20050204-1206_spkr_9', 138.52, 85.1]}"
    - collars: list of start collar sizes and end collar sizes in seconds, form "[0.25, 0.25]"

    Outputs:
    - matErrors: a list of lists of the errors, form: "[[20.15	0.91	8.09	29.14],
                                                        [18.40	0.46	7.63	26.48],
                                                        [16.86	0.32	7.16	24.34],
                                                        [15.46	0.28	6.72	22.45],
                                                        [14.16	0.24	6.37	20.78],
                                                        [13.12	0.22	6.05	19.39]]"
    - dfErrors: a dataframe of the errors, form: "	            MISS	FALARM	ERROR	DER
                                                    [0, 0]	    20.15	0.91	8.09	29.14
                                                    [50, 50]	18.40	0.46	7.63	26.48
                                                    [100, 100]	16.86	0.32	7.16	24.34
                                                    [150, 150]	15.46	0.28	6.72	22.45
                                                    [200, 200]	14.16	0.24	6.37	20.78
                                                    [250, 250]	13.12	0.22	6.05	19.39"
    """
    import pandas as pd
    matErrors = []
    for index, collar in enumerate(collars):
        totalTime = getTotalTime(revisedComboSplitSegs[index], True)
        missedTime = getMissedTime(revisedComboSplitSegs[index])
        falarmTime = getFalarmTime(revisedComboSplitSegs[index])
        errorTime = getErrorTime(revisedComboSplitSegs[index], mapSpkrs)
        matErrors.append([round(100*missedTime/totalTime, 2),\
                          round(100*falarmTime/totalTime, 2),\
                         round(100*errorTime/totalTime, 2),\
                          round(100*(missedTime + falarmTime + errorTime)/totalTime, 2)])

    dfErrors = pd.DataFrame(matErrors, index=["[{:.0f}, {:.0f}]".format(collar[0]*1000, collar[1]*1000) for collar in collars],\
                            columns=["MISS (%)", "FALARM (%)", "ERROR (%)", "DER (%)"])
    dfErrors.index.name = "Collars [-ms, +ms]"

    return matErrors, dfErrors


def getSBDERs(allCollarSegs, mapSpkrs, collars):
    """
    This function returns the errors generated by the speaker diarization system within the collars.  The final figure "SBDER"
    is the segment boundary diarization error rate.

    Inputs:
    - allCollarSegs: the list of segments within the collars
    - a dictionary that with the ground truth speakers as the key and their values as a 1 x 3 list showing
                the mapped speaker, the mapped speaker time and the percentage of time correctly mapped to that speaker,
                form: "{'FEE029': ['AMI_20050204-1206_spkr_0', 194.48, 79.6],
                        'FEE030': ['AMI_20050204-1206_spkr_5', 67.645, 67.2],
                        'MEE031': ['AMI_20050204-1206_spkr_3', 106.655, 86.2],
                        'FEE032': ['AMI_20050204-1206_spkr_9', 138.52, 85.1]}"
    - collars: list of start collar sizes and end collar sizes in seconds, form "[0.25, 0.25]"

    Outputs:
    - matSBDERs: a list of lists of the errors, form: "[[43.94	7.00	14.24	65.18],
                                                        [42.19	4.88	14.29	61.36],
                                                        [40.76	3.68	14.09	58.54],
                                                        [39.64	3.07	13.66	56.36],
                                                        [38.39	2.69	13.35	54.43]]"
    - dfSBDERs: a dataframe of the errors, form: "	            MISS	FALARM	ERROR	DER
                                                    [50, 50]	43.94	7.00	14.24	65.18
                                                    [100, 100]	42.19	4.88	14.29	61.36
                                                    [150, 150]	40.76	3.68	14.09	58.54
                                                    [200, 200]	39.64	3.07	13.66	56.36
                                                    [250, 250]	38.39	2.69	13.35	54.43"
    """
    import pandas as pd
    matSBDERs = []
    for index, collar in enumerate(collars):
        if collar[0] != 0 and collar[1] != 0: # Meaningless to do this if no collar
            totalTime = getTotalTime(allCollarSegs[index], True)
            missedTime = getMissedTime(allCollarSegs[index])
            falarmTime = getFalarmTime(allCollarSegs[index])
            errorTime = getErrorTime(allCollarSegs[index], mapSpkrs)
            matSBDERs.append([round(100*missedTime/totalTime, 2),\
                             round(100*falarmTime/totalTime, 2),\
                             round(100*errorTime/totalTime, 2),\
                             round(100*(missedTime + falarmTime + errorTime)/totalTime, 2)])
    
    dfSBDERs = pd.DataFrame(matSBDERs, index=["[{:.0f}, {:.0f}]".format(collar[0]*1000, collar[1]*1000) for collar in collars[1:]],\
                            columns=["MISS (%)", "FALARM (%)", "ERROR (%)", "SBDER (%)"])
    dfSBDERs.index.name = "Collars [-ms, +ms]"
    
    return matSBDERs, dfSBDERs


def getAllErrors(oracleRttmFile, diarizedRttmFile, collars):
    """
    Single function that takes the input RTTM files and list of collars and gives the errors dataframe as well as the
    segment boundary errors dataframe.

    Inputs:
    - oracleRttmFile: path to and filename of ground truth RTTM file, form: "inputs/AMI_20050204-1206.rttm"
    - diarizedRttmFile: path to and filename of speaker diarization generated RTTM file, form: "results/AMI_20050204-1206.rttm"
    - collars: list of start collar sizes and end collar sizes in seconds, form "[0.25, 0.25]"
    Outputs:
    - dfErrors: a dataframe of the errors, form: "	            MISS	FALARM	ERROR	DER
                                                    [0, 0]	    20.15	0.91	8.09	29.14
                                                    [50, 50]	18.40	0.46	7.63	26.48
                                                    [100, 100]	16.86	0.32	7.16	24.34
                                                    [150, 150]	15.46	0.28	6.72	22.45
                                                    [200, 200]	14.16	0.24	6.37	20.78
                                                    [250, 250]	13.12	0.22	6.05	19.39"
    - dfSBDERs: a dataframe of the errors, form: "	            MISS	FALARM	ERROR	DER
                                                    [50, 50]	43.94	7.00	14.24	65.18
                                                    [100, 100]	42.19	4.88	14.29	61.36
                                                    [150, 150]	40.76	3.68	14.09	58.54
                                                    [200, 200]	39.64	3.07	13.66	56.36
                                                    [250, 250]	38.39	2.69	13.35	54.43"
    
    """

    import pandas as pd
    oracleSegs = getSegs(oracleRttmFile, True)
    diarizedSegs = getSegs(diarizedRttmFile, False)

    oracleSplitSegs = getSplitSegs(oracleSegs)
    diarizedSplitSegs = getSplitSegs(diarizedSegs)

    comboSegs = oracleSplitSegs + diarizedSplitSegs
    comboSegs.sort(key=lambda x:x['tbeg'])

    comboSplitSegs = getSplitSegs(comboSegs)

    dfComboSplitSegs = pd.DataFrame(comboSplitSegs, columns=["Start Time", "End Time", "Oracle Speaker(s)", "Diarized Speaker(s)"])

    lstOracleSpkrs = getSpkrs(comboSplitSegs, 'oname')
    lstDiarizedSpkrs = getSpkrs(comboSplitSegs, 'dname')
    dfSpkrTimes = getSpkrTimes(lstOracleSpkrs, lstDiarizedSpkrs, comboSplitSegs)
    mapSpkrs = getMapSpkrs(lstOracleSpkrs, dfSpkrTimes)

    segsIgnore = getSegsIgnore(oracleSplitSegs, collars)
    newSegsIgnore = getNewSegsIgnore(segsIgnore, collars)

    revisedComboSplitSegs = []
    for index, collar in enumerate(collars):
        revisedComboSplitSegs.append(getRevisedComboSplitSegs(comboSplitSegs, newSegsIgnore[index]))

    matErrors, dfErrors = getErrors(revisedComboSplitSegs, mapSpkrs, collars)
    
    allCollarSegs = []
    for index, collar in enumerate(collars):
        allCollarSegs.append(getCollarSegs(comboSplitSegs, newSegsIgnore[index]))
    
    matSBDERs, dfSBDERs = getSBDERs(allCollarSegs, mapSpkrs, collars)
    
    return mapSpkrs, dfErrors, dfSBDERs
