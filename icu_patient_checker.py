import pandas as pd
import numpy as np
import requests as r
import getpass as gp
import datetime as dt
import sys, getopt, json, os

shortopts = "hi:o:";
longopts = ["help", "input=", "output="];

statsCol = ('LessThan30Secs', 'moreThan30Secs')
stats = [0, 0];

def main(argv, shortopts, longopts):
    inputfile = None
    outputfile = None

    try:
        opts, args = getopt.getopt(argv, shortopts, longopts)
    except getopt.GetoptError:
        print('icu_patient_checker.py -i <path to patient list> -o <path to output list>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('icu_patient_checker.py -i <path to patient list> -o <path to output list>')
            sys.exit()
        elif opt in ("-i", "--input"):
            inputfile = arg
        elif opt in ("-o", "--output"):
            outputfile = arg
        else:
            print('icu_patient_checker.py -i <path to patient list> -o <path to database list>')

    if outputfile == None:
        sys.exit('No outputfile specified')
    elif inputfile == None:
        sys.exit('No input specified')

    outputname, output_ext = os.path.splitext(outputfile)
    if (output_ext not in ('.csv', '.xls', '.xlsx')):
        sys.exit('Invalid outputfile')

    inputname, input_ext = os.path.splitext(inputfile)
    if (input_ext != '.csv'):
        sys.exit('Invalid inputfile')

    mrn_data = parseFilename(inputfile)

    output = lookupMRN(mrn_data, outputname, output_ext)

    with open('stats.csv', 'a+') as f:
        statDF = pd.DataFrame([stats], columns = statsCol)
        statDF.to_csv(f)

    sys.exit(1)

def parseFilename (filename):
    # csvIn = open(str(filename), 'r')
    csvIn = pd.read_csv(filename, skipinitialspace=True, dtype = str, skip_blank_lines=True)
    csvIn.dropna(how="all", inplace=True)
    # print csvIn
    # csvIn.columns = csvIn.columns.str.replace(' ','')
    try:
            mrnData = csvIn.to_dict('records')
            # print mrnData
    except AttributeError as err:
        print('Malformed CSV, '+ str(err.args))

    return mrnData

def synoLogin():
    try:
        print('Backup Database Login')
        usr = input('Enter Username: ')
        # usr = "MitchellM"
        pwd = gp.getpass(prompt='Enter Password: ')
    except UserWarning as warn:
        print(warn)

    try:
        payloadAuth = {"api":"SYNO.API.Auth", "version":"3", "method":"login", "account":str(usr), "passwd":str(pwd), "session":"FileStation", "format":"cookie"}
        auth = r.get('http://128.218.210.52:5000/webapi/auth.cgi', params=payloadAuth)
        auth.raise_for_status()
        sid = auth.json()['data']['sid']
    except (KeyError, r.exceptions.HTTPError) as err:
        print('Login Failed')
        retry = input('Try again? (Y/N): ')
        if retry in ('Y', 'y', 'yes'):
            return synoLogin()
        else:
            sys.exit(2)
    return sid

def buildRow (alarmRanges):
    df0 = pd.DataFrame([alarmRanges.get('MRN')], columns=['MRN'], dtype=np.uint32)
    df1 = pd.DataFrame([alarmRanges.get('alarmStart')], columns=['CodeTime'], dtype=str)
    df2 = pd.DataFrame([alarmRanges.get('prevBed')], columns=['CodedUnit'], dtype=str)
    df3 = pd.DataFrame([alarmRanges.get('waveStart')], columns=['WaveStartTime'], dtype=str)
    df4 = pd.DataFrame([alarmRanges.get('waveEnd')], columns=['WaveEndTime'], dtype=str)
    df5 = pd.DataFrame([alarmRanges.get('waveDuration')], columns=['Duration'], dtype=np.uint32)
    df6 = pd.DataFrame([alarmRanges.get('TypeCode')], columns=['TypeCode'], dtype=str)
    df7 = pd.DataFrame([alarmRanges.get('HasAlarm')], columns=['HasAlarm'], dtype=np.uint32)

    return pd.concat([df0, df1, df2, df3, df4, df5, df6, df7], axis=1)
    # outputFrame = outputFrame.append(emptyEntry, ignore_index=True)

def lookupMRN (data_list, outputname, output_ext):
    sid = synoLogin()

    # columnsList = ('MRN', 'CodeTime', 'CodedUnit', 'WaveStartTime', 'WaveEndTime', 'Duration', 'TypeCode', 'HasAlarm')

    outputFrameBefore = pd.DataFrame()
    outputFrameAfter = pd.DataFrame()
    outputFrameDuring = pd.DataFrame()

    for patient in data_list:
    # using one for now
    # patient = data_list[0]
        mrn = patient.get('Patient ID')
        admissionDate = patient.get('Admission Date')
        dischargeDate = patient.get('Discharge Date')

        filepath = "/NSDL_Backup/UCSF_BinFiles_V2/"+mrn.lstrip('0')+"/Alarms.csv"

        try:

            fileParam = {"api":"SYNO.FileStation.Download", "version":"2", "method":"download", "path":str(filepath), "mode":"download", "_sid":str(sid)}

            csv = r.get('http://128.218.210.52:5000/webapi/entry.cgi', params=fileParam, stream = True)

            csv.raise_for_status()

            csvDF = pd.read_csv(csv.raw, parse_dates=['AlarmStartTime', 'AlarmEndTime'], date_parser = pd.datetools.to_datetime)

        except (ValueError, r.exceptions.HTTPError) as err:
            print(err)
            print(csv)
            print (filepath + " was invalid.")
            continue

        csvRecords =  csvDF.to_dict('records')

        if (len(csvDF.index) == 0):
            print('Patient ' + mrn.lstrip('0') +' no aFib')
            emptyRow = {'MRN': mrn, 'prevEnd': None, 'currStart': None, 'currEnd': None, 'duration': None, 'waveStart': None, 'waveEnd': None, 'alarmStart': None, 'waveDuration': 0, 'currBed': None, 'prevBed': None,
            'TypeCode': None, 'HasAlarm': 0}
            emptyEntry = buildRow(emptyRow)
            outputFrameBefore = outputFrameBefore.append(emptyEntry, ignore_index=True)
            outputFrameAfter = outputFrameAfter.append(emptyEntry, ignore_index=True)
            outputFrameDuring = outputFrameDuring.append(emptyEntry, ignore_index=True)
        else:
            print('Looking up patient ' + mrn.lstrip('0') +' before')
            csvEntryBefore = searchCSVBefore(mrn, csvRecords)
            outputFrameBefore = outputFrameBefore.append(csvEntryBefore, ignore_index=True)

            # print('Looking up patient ' + mrn.lstrip('0') +' after')
            # csvEntryAfter = searchCSVAfter(mrn, csvRecords)
            # outputFrame = outputFrameAfter.append(csvEntry, ignore_index=True)

            print('Looking up patient ' + mrn.lstrip('0') +' during')
            csvEntryDuring = searchCSVDuring(mrn, csvRecords)
            outputFrameDuring = outputFrameDuring.append(csvEntryDuring, ignore_index=True)

    hasAFib = pd.DataFrame([], columns=['hasAFib'])
    signalQuality = pd.DataFrame([], columns=['signalQuality'])

    outputFrameBefore = pd.concat([outputFrameBefore, hasAFib, signalQuality], axis = 1)

    outputFrameAfter = pd.concat([outputFrameAfter, hasAFib, signalQuality], axis = 1)

    outputFrameDuring = pd.concat([outputFrameDuring, hasAFib, signalQuality], axis = 1)

    writeToFile(outputFrameBefore, outputname+'_before'+output_ext)
    # writeToFile(outputFrameAfter, outputname+'_during'+output_ext)
    writeToFile(outputFrameDuring, outputname+'_during'+output_ext)


def searchCSVBefore (mrn, records):

    # dtypeList = (np.int32, object, object, object, object, np.int32, object, np.int32)
    # colDtype = list(zip(columnsList, dtypeList))
    #
    # empty = np.empty((0,), dtype = colDtype)

    recordFrame = pd.DataFrame()

    alarmRanges = {'MRN': mrn, 'prevEnd': None, 'currStart': None, 'currEnd': dt.datetime.fromtimestamp(0), 'duration': None, 'waveStart': None, 'waveEnd': None, 'alarmStart': None, 'waveDuration': 0, 'currBed': records[0].get('UnitBed'), 'prevBed': None,
    'TypeCode': 'AFib', 'HasAlarm': 1}


    halfhour = dt.timedelta(minutes = 30)
    tenmin = dt.timedelta(minutes = 10)

    for entry in records:
        if entry.get('Message') == 'AFib':

            alarmRanges['prevEnd'] = alarmRanges['currEnd']
            alarmRanges['prevBed'] = alarmRanges['currBed']
            alarmRanges['currBed'] = entry.get('UnitBed')
            alarmRanges['currStart'] = entry.get('AlarmStartTime')
            alarmRanges['currEnd'] = entry.get('AlarmEndTime')
            alarmRanges['duration'] = int(entry.get('Duration'))
            #If the difference is less than 30 secs, we know we are inside a afib time range, else we are at the startpoint of a new range

            timeBetweenWaves = alarmRanges['currStart'] - alarmRanges['prevEnd']

            if (alarmRanges['currBed'] != alarmRanges['prevBed']):
                if (alarmRanges['waveEnd'] == None):
                    alarmRanges['waveEnd'] == alarmRanges['prevEnd']

                    dfEntry = buildRow(alarmRanges)
                    recordFrame = recordFrame.append(dfEntry, ignore_index=True)

                    alarmRanges['waveStart'] = None
                    alarmRanges['waveEnd'] = None
                    alarmRanges['waveDuration'] = 0
                    alarmRanges['alarmStart'] = None

            if (timeBetweenWaves <= dt.timedelta(seconds = 60)):
                stats[0] += 1
                alarmRanges['waveDuration'] = alarmRanges['waveDuration'] +  alarmRanges['duration'] + (alarmRanges['currStart'] - alarmRanges['prevEnd']).total_seconds()
                #if we reach the end of 10 minutes, set the time to be the 10 minute interval
                if ((alarmRanges['waveDuration'] >= 600)and(alarmRanges['waveEnd'] == None)):
                    alarmRanges['waveEnd'] = alarmRanges['alarmStart'] + tenmin
                continue
            else:

                #at the start of next waveform
                stats[1] += 1
                #check if end of waveform is defined, if not set it here
                if ((alarmRanges['waveEnd'] == None)and(alarmRanges['waveDuration']>0)):
                    alarmRanges['waveEnd'] = alarmRanges['prevEnd']

                    #the duration was zero, so we have not yet iterated, so continue


                #If we have a complete waveform range, send it to the data out df

                if ((alarmRanges['waveStart']!=None)and(alarmRanges['waveEnd']!=None)and(alarmRanges['alarmStart']!=None)and(alarmRanges['waveDuration']>0)):

                    dfEntry = buildRow(alarmRanges)

                    recordFrame = recordFrame.append(dfEntry, ignore_index=True)

                    if (timeBetweenWaves <= halfhour):
                        alarmRanges['waveStart'] = alarmRanges['prevEnd']
                    else:
                        alarmRanges['waveStart'] = alarmRanges['currStart'] - halfhour

                    alarmRanges['waveEnd'] = None
                    alarmRanges['waveDuration'] = 0
                    alarmRanges['alarmStart'] = alarmRanges['currStart']
                #If we are starting a new waveform, set the start and alarm time

                if (alarmRanges['waveStart'] == None):
                    alarmRanges['alarmStart'] = alarmRanges['currStart']
                    if (timeBetweenWaves <= halfhour):
                        alarmRanges['waveStart'] = alarmRanges['prevEnd']
                    else:
                        alarmRanges['waveStart'] = alarmRanges['currStart'] - halfhour
                    # continue
                alarmRanges['waveDuration'] = alarmRanges['waveDuration'] +  alarmRanges['duration']

    return recordFrame

def searchCSVDuring (mrn, records):

    # dtypeList = (np.int32, object, object, object, object, np.int32, object, np.int32)
    # colDtype = list(zip(columnsList, dtypeList))
    #
    # empty = np.empty((0,), dtype = colDtype)

    recordFrame = pd.DataFrame()

    alarmRanges = {'MRN': mrn, 'prevEnd': None, 'currStart': None, 'currEnd': dt.datetime.fromtimestamp(0), 'duration': None, 'waveStart': None, 'waveEnd': None, 'alarmStart': None, 'waveDuration': 0, 'currBed': records[0].get('UnitBed'), 'prevBed': None,
    'TypeCode': 'AFib', 'HasAlarm': 1}

    for entry in records:
        if entry.get('Message') == 'AFib':

            alarmRanges['prevEnd'] = alarmRanges['currEnd']
            alarmRanges['prevBed'] = alarmRanges['currBed']
            alarmRanges['currBed'] = entry.get('UnitBed')
            alarmRanges['currStart'] = entry.get('AlarmStartTime')
            alarmRanges['currEnd'] = entry.get('AlarmEndTime')
            alarmRanges['duration'] = int(entry.get('Duration'))
            #If the difference is less than 30 secs, we know we are inside a afib time range, else we are at the startpoint of a new range

            timeBetweenWaves = alarmRanges['currStart'] - alarmRanges['prevEnd']

            if (alarmRanges['currBed'] != alarmRanges['prevBed']):
                if (alarmRanges['waveEnd'] == None):
                    alarmRanges['waveEnd'] == alarmRanges['prevEnd']

                    dfEntry = buildRow(alarmRanges)
                    recordFrame = recordFrame.append(dfEntry, ignore_index=True)

                    alarmRanges['waveStart'] = None
                    alarmRanges['waveEnd'] = None
                    alarmRanges['waveDuration'] = 0
                    alarmRanges['alarmStart'] = None

            if (timeBetweenWaves <= dt.timedelta(minutes = 5)):
                stats[0] += 1
                alarmRanges['waveDuration'] = alarmRanges['waveDuration'] +  alarmRanges['duration'] + (alarmRanges['currStart'] - alarmRanges['prevEnd']).total_seconds()
                continue
            else:

                #at the start of next waveform
                stats[1] += 1
                #check if end of waveform is defined, if not set it here
                if ((alarmRanges['waveEnd'] == None)and(alarmRanges['waveDuration']>0)):
                    alarmRanges['waveEnd'] = alarmRanges['prevEnd']

                    #the duration was zero, so we have not yet iterated, so continue


                #If we have a complete waveform range, send it to the data out df

                if ((alarmRanges['waveStart']!=None)and(alarmRanges['waveEnd']!=None)and(alarmRanges['alarmStart']!=None)and(alarmRanges['waveDuration']>0)):

                    dfEntry = buildRow(alarmRanges)

                    recordFrame = recordFrame.append(dfEntry, ignore_index=True)

                    alarmRanges['waveStart'] = alarmRanges['currStart']
                    alarmRanges['waveEnd'] = None
                    alarmRanges['waveDuration'] = 0
                    alarmRanges['alarmStart'] = alarmRanges['currStart']
                #If we are starting a new waveform, set the start and alarm time

                if (alarmRanges['waveStart'] == None):
                    alarmRanges['alarmStart'] = alarmRanges['currStart']
                    alarmRanges['waveStart'] = alarmRanges['currStart']
                    # continue
                alarmRanges['waveDuration'] = alarmRanges['waveDuration'] +  alarmRanges['duration']

    return recordFrame

def writeToFile(entry, path):
    with open(path, 'a+') as f:
        entry.to_csv(f)

if __name__ == "__main__":
    main(sys.argv[1:], shortopts, longopts)
