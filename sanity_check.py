import pandas as pd
import numpy as np
import getpass as gp
import datetime as dt
import sys, getopt, json, os, random

shortopts = "hl:c:"
longopts = ["help", "csv="]

def main(argv, shortopts, longopts):

    csvtocheck = None

    try:
        opts, args = getopt.getopt(argv, shortopts, longopts)

    except getopt.GetoptError:
        print('icu_patient_checker.py -i <path to patient list> -o <path to output list>')
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('icu_patient_checker.py -c <csvtocheck>')
            sys.exit()
        elif opt in ("-c", "--csv"):
            csvtocheck = arg
        else:
            print('icu_patient_checker.py -i <path to patient list> -o <path to output list>')

    if csvtocheck == None:
        sys.exit('No outputfile specified')

    data = parseFilename(csvtocheck)

    checkEntry(data)

    sys.exit("Finished checking file.")

def parseFilename (filename):

    print("Parsing "+filename)

    csvIn = pd.read_csv(filename, skipinitialspace=True, dtype = str, skip_blank_lines=True)
    csvIn.dropna(how="all", inplace=True)

    try:
            rtn = csvIn.to_dict('records')

    except AttributeError as err:
        print('Malformed CSV, '+ str(err.args))

    return rtn

def checkEntry (data):
    for entry in data:
        waveStartTime = dt.datetime.strptime(entry["WaveStartTime"], "%Y-%m-%d %H:%M:%S")
        codeStartTime = dt.datetime.strptime(entry["CodeStartTime"], "%Y-%m-%d %H:%M:%S")
        waveEndTime = dt.datetime.strptime(entry["WaveEndTime"], "%Y-%m-%d %H:%M:%S")
        codeEndTime = dt.datetime.strptime(entry["CodeEndTime"], "%Y-%m-%d %H:%M:%S")

        index = entry.get("Index")

        checkTimeRangeSynth(waveStartTime, codeStartTime, waveEndTime, codeEndTime, index)
        checkOverlap(waveStartTime, codeStartTime, waveEndTime, codeEndTime, index)
    return

def checkTimeRangeSynth(waveStartTime, codeStartTime, waveEndTime, codeEndTime, index):
    if ( ((codeStartTime - waveStartTime).total_seconds() != 60) and ((codeStartTime - waveStartTime).total_seconds() != 30) ):
        print("Index "+index+" incorrectly generated start time.")
    if ( ((waveEndTime - codeEndTime).total_seconds() != 60) and ((waveEndTime - codeEndTime).total_seconds() != 10) ):
        if ( ((waveEndTime-codeStartTime).total_seconds() != 310) and ((waveEndTime-codeStartTime).total_seconds() != 360) ):
            print("Index "+index+" incorrect generated end time.")
    if((waveEndTime - waveStartTime).total_seconds() > 420):
        print ("Index "+index+" duration too long.")

def checkOverlap(waveStartTime, codeStartTime, waveEndTime, codeEndTime, index):
    if (waveStartTime == waveEndTime):
        print("Index "+index+ " wave times are the same.")
    if (codeStartTime == codeEndTime):
        print("Index "+index+ " code times are the same.")

if __name__ == "__main__":
    main(sys.argv[1:], shortopts, longopts)
