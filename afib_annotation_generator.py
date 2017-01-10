import pandas as pd
import numpy as np
import getpass as gp
import datetime as dt
import sys, getopt, json, os, random

thirtyseconds = dt.timedelta(seconds = 30)
tenseconds = dt.timedelta(seconds = 10)
oneminute = dt.timedelta(minutes = 1)
fiveminutes = dt.timedelta(minutes = 5)

indexCounter = 0;
patientIndexRange = [];

shortopts = "hl:i:o:"
longopts = ["help", "list=" "indices=", "output="]

def main(argv, shortopts, longopts):
    filename = None
    indexfile = None

    try:
        opts, args = getopt.getopt(argv, shortopts, longopts)

    except getopt.GetoptError:
        print('icu_patient_checker.py -i <path to patient list> -o <path to output list>')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('icu_patient_checker.py -i <path to patient list> -o <path to output list>')
            sys.exit()
        elif opt in ("-l", "--list"):
            listfile = arg
        elif opt in ("-i", "--indices"):
            indexfile = arg
        elif opt in ("-o", "--output"):
            outputfile = arg
        else:
            print('icu_patient_checker.py -i <path to patient list> -o <path to database list>')

    if outputfile == None:
        sys.exit('No outputfile specified')
    elif listfile == None:
        sys.exit('No listfile specified')
    elif indexfile == None:
        sys.exit('No indexfile specified')

    outputname, output_ext = os.path.splitext(outputfile)
    if (output_ext not in ('.csv', '.xls', '.xlsx')):
        sys.exit('Invalid outputfile')

    list_data = parseFilename(listfile)

    index_data = parseFilename(indexfile)

    output = lookupEntry(list_data, index_data, outputname, output_ext)

    sys.exit(0)

def parseFilename (filename):

    print("Parsing "+filename)

    csvIn = pd.read_csv(filename, skipinitialspace=True, dtype = str, skip_blank_lines=True)
    csvIn.dropna(how="all", inplace=True)

    try:
            rtn = csvIn.to_dict('records')

    except AttributeError as err:
        print('Malformed CSV, '+ str(err.args))

    return rtn

def lookupEntry (list_data, index_data, outputname, output_ext):

    output = []

    columns = ['MRN', 'CodedUnit', 'CodeStartTime', 'CodeEndTime', 'CodeDuration', 'WaveStartTime', 'WaveEndTime', 'WaveDuration', 'TypeCode', 'HasAlarm', 'Index']

    for item in index_data:
        print("Generating data for "+item.get('MRN'))
        start = int(item.get('startIndex'))
        end = int(item.get('endIndex'))

        if (end - start < 10):
            indices = range(start+1,end)
        else:
            indices = random.sample(range(start+1,end), 10)
        entry = parseEntry(list_data, start, oneminute, oneminute)
        output.append(entry)
        for index in indices:
            entry = parseEntry(list_data, index, thirtyseconds, tenseconds)
            output.append(entry)

    outputFrame = pd.DataFrame.from_records(output, columns = columns)

    writeToFile(outputFrame, outputname+'_annotate'+output_ext)

def parseEntry(list_data, index, start_period, end_period):

    entry = list_data[index]

    entry['WaveStartTime'] = dt.datetime.strptime(entry['CodeStartTime'], "%Y-%m-%d %H:%M:%S") - start_period
    if (int(entry['CodeDuration']) > 300):
        entry['WaveEndTime'] = dt.datetime.strptime(entry['CodeStartTime'], "%Y-%m-%d %H:%M:%S") + fiveminutes + end_period
    else:
        entry['WaveEndTime'] = dt.datetime.strptime(entry['CodeEndTime'], "%Y-%m-%d %H:%M:%S") + end_period

    delta = entry['WaveEndTime'] - entry['WaveStartTime']

    entry['WaveDuration'] = delta.total_seconds()

    entry["Index"] = index

    return entry

def writeToFile(entry, path):
    if (not isinstance(entry, pd.DataFrame)):
        entry = pd.DataFrame(entry)
    with open(path, 'a+') as f:
        entry.to_csv(f)

if __name__ == "__main__":
    main(sys.argv[1:], shortopts, longopts)
