import pandas as pd
import numpy as np
import requests as r
# import getpass as gp
import time
import datetime as dt
import sys, getopt, json, os
import synology as syn

indexCounter = 0
patientIndexRange = []

total = 0

shortopts = "hi:o:"
longopts = ["help", "input=", "output="]

def main(argv, shortopts, longopts):
    inputfile = None
    outputfile = None

    try:
        opts, args = getopt.getopt(argv, shortopts, longopts)
    except getopt.GetoptError:
        print('alarm_stats.py -i <path to patient list> -o <path to output list>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('alarm_stats.py -i <path to patient list> -o <path to output list>')
            sys.exit()
        elif opt in ("-i", "--input"):
            inputfile = arg
        elif opt in ("-o", "--output"):
            outputfile = arg
        else:
            print('alarm_stats.py -i <path to patient list> -o <path to database list>')

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

    mrn_data = parseInputCSV(inputfile)

    lookupAlarmsByMRNs(mrn_data, outputname, output_ext)

    sys.exit(1)

def parseInputCSV (filename):

    csvIn = pd.read_csv(filename, skipinitialspace=True, dtype = str, skip_blank_lines=True)
    csvIn.dropna(how="all", inplace=True)

    try:
            mrnData = csvIn.to_dict('records')

    except AttributeError as err:
        print('Malformed CSV, '+ str(err.args))

    return mrnData

# def buildRow (alarmRanges):

#     df0 = pd.DataFrame([alarmRanges.get('MRN')], columns=['MRN'], dtype=np.uint32)
#     df1 = pd.DataFrame([alarmRanges.get('currBed')], columns=['CodedUnit'], dtype=str)
#     df2 = pd.DataFrame([alarmRanges.get('alarmStart')], columns=['CodeStartTime'], dtype=str)
#     df3 = pd.DataFrame([alarmRanges.get('alarmEnd')], columns=['CodeEndTime'], dtype=str)
#     df4 = pd.DataFrame([alarmRanges.get('duration')], columns=['CodeDuration'], dtype=np.uint32)
#     df5 = pd.DataFrame([alarmRanges.get('waveStart')], columns=['WaveStartTime'], dtype=str)
#     df6 = pd.DataFrame([alarmRanges.get('waveEnd')], columns=['WaveEndTime'], dtype=str)
#     df7 = pd.DataFrame([alarmRanges.get('waveDuration')], columns=['WaveDuration'], dtype=np.uint32)
#     df8 = pd.DataFrame([alarmRanges.get('TypeCode')], columns=['TypeCode'], dtype=str)
#     df9 = pd.DataFrame([alarmRanges.get('HasAlarm')], columns=['HasAlarm'], dtype=np.uint32)

#     return pd.concat([df0, df1, df2, df3, df4, df5, df6, df7, df8, df9], axis=1)

def lookupAlarmsByMRNs (data_list, outputname, output_ext):
    auth = syn.auth()
    print('Logging into Synology')
    sid = auth.login()

    filestation = syn.fileStation()

    # outputFrame = pd.DataFrame()

    outputMissingList = []

    afibDatabase = {}

    # parserToPOSIX = lambda dateString: time.mktime(dt.datetime.strptime(dateString, "%m/%d/%Y %H:%M:%S %p").timetuple())

    for patient in data_list:

        mrn = patient.get('Patient ID')

        print ('Getting data for '+mrn.lstrip('0'))

        admissionDate = patient.get('Admission Date')
        dischargeDate = patient.get('Discharge Date')

        filepath = "/Temporary Backup Folders/HuLab_Primary_BackUp/NSDL_Backup/UCSF_BinFiles_V2/"+mrn.lstrip('0')+"/Alarms.csv"
        # filepath = "/Temporary Backup Folders/HuLab_Primary_BackUp/NSDL_Backup/UCSF_BinFiles_V2"

        try:

            print ('downloading alarms csv')

            alarmsCSV = filestation.downloadFile(filepath, sid)

            # fileParam = {"api":"SYNO.FileStation.Download", "version":"2", "method":"download", "path":str(filepath), "mode":"download", "_sid":str(sid)}

            # headers = {"Accept-Encoding":"identity"}

            # csv = r.get('http://128.218.209.79:5000/webapi/entry.cgi', params=fileParam, headers = headers, stream = True)

            # csv.raise_for_status()

            print('parsing csv')
            csvDF = pd.read_csv(alarmsCSV.raw, parse_dates=['AlarmStartTime', 'AlarmEndTime'], infer_datetime_format=True)

        except (ValueError, r.exceptions.HTTPError) as err:
            print(err)
            # print(csvDF)
            print (filepath + " was invalid.")
            outputMissingList.append({"MRN":mrn})
            continue

        if (len(csvDF.index) == 0):
            print('Patient ' + mrn.lstrip('0') +' no Alarm.csv')
            outputMissingList.append({"MRN":mrn})
            continue
        else:
            csvRecords =  csvDF.to_dict('records')

            if (len(csvRecords) == 0):
                print("Patient"+ mrn.lstrip('0') +' empty Alarm.csv' )
                outputMissingList.append({"MRN":mrn})
                continue

            print('Generating alarm stats for ' + mrn.lstrip('0'))
            afibInstances = searchCSV(mrn, csvRecords)
            # outputFrame = outputFrame.append(csvEntry, ignore_index=True)

            afibDatabase[mrn] = afibInstances

    # writeToFile(outputFrame, outputname+'_master'+output_ext)

    # patientIndexFrame = pd.DataFrame(patientIndexRange, columns=["MRN","startIndex","endIndex"])

    # writeToFile(patientIndexFrame, outputname+'_master_indices'+output_ext)

    # writeToTxt(outputMissingList, "missing_data.txt")

    statisticsGenerator(afibDatabase, outputname)

    auth.logout(sid)

def searchCSV (mrn, records):

    global indexCounter
    global patientIndexRange

    # recordFrame = pd.DataFrame()

    # alarmRanges = {'MRN': mrn, 'currBed': None, 'alarmStart': None, 'alarmEnd': None, 'duration': None, 'waveStart': None, 'waveEnd': None, 'waveDuration': 0, 'TypeCode': 'AFib', 'HasAlarm': 0}

    # currIndex = indexCounter

    alarmsBuffer = {}

    afibInstances = {}

    # currentAfib = None

    for entry in records:
        # print (entry)

        alarmName = entry.get('Message')

        if alarmName != 'AFib':
            alarmsBuffer[alarmName] = entry

        elif entry.get('Message') == 'AFib':

            concurrentAlarms = []

            alarmStart = entry.get('AlarmStartTime')
            alarmEnd = entry.get('AlarmEndTime')
            # alarmRanges['duration'] = int(entry.get('Duration'))
            # alarmRanges['waveStart'] = entry.get('AlarmStartTime')
            # alarmRanges['waveEnd'] = entry.get('AlarmEndTime')
            # alarmRanges['waveDuration'] = int(entry.get('Duration'))
            # alarmRanges['HasAlarm'] = 1

            for alarm in alarmsBuffer.keys():
                if alarmsBuffer.get(alarm).get('AlarmEndTime') >= alarmStart:

                    concurrentAlarms.append(alarm)

            concurrentAlarmsStr = repr(concurrentAlarms)
            # print(concurrentAlarmsStr)
            if concurrentAlarmsStr in afibInstances.keys():
                
                afibInstances[concurrentAlarmsStr].append(entry)
            
            else:
                afibInstances[concurrentAlarmsStr] = [entry]
                # print (entry)

    # if(alarmRanges['HasAlarm'] == 0):
    #     print(mrn + " no AFib Alarm Found")
    #     return None

    # patientIndexRange.append({"MRN":mrn, "startIndex":currIndex, "endIndex":indexCounter} , "total":indexCounter-currIndex)

    return afibInstances

def statisticsGenerator(afibData, outputPath):
    global total
    totalAlarmTypes = {}

    for mrn in afibData.keys():
        alarmData = afibData.get(mrn)

        for alarmType in alarmData.keys():
            length = len(alarmData[alarmType])
            if alarmType in totalAlarmTypes.keys():
                totalAlarmTypes[alarmType] += length
            else:
                totalAlarmTypes[alarmType] = length
            total += length

    print (totalAlarmTypes)
    print (total)

    alarmsAsList = list(totalAlarmTypes.items())

    alarmsAsList.insert(0, ('Total', total))
    df = pd.DataFrame(alarmsAsList, columns=["Overlapping Alarms", "Occurances"])

    writeToCSV(df, outputPath)

def writeToCSV(entry, path):
    if (not isinstance(entry, pd.DataFrame)):
        entry = pd.DataFrame(entry)
    with open(path, 'w+') as f:
        entry.to_csv(f)

# def writeToTxt(entry, path):
#     df = pd.DataFrame(entry)
#     with open(path, 'a+') as f:
#         df.to_csv(path_or_buf=f, sep='\r', line_terminator="\n", header=False, index=False, index_label=False)

if __name__ == "__main__":
    main(sys.argv[1:], shortopts, longopts)
