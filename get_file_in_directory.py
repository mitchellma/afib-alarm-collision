import sys, getopt, json, os

# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "synology"))
#
# print (sys.path)

import pandas as pd
import numpy as np
import requests as r
import getpass as gp
import datetime as dt
import synology as syn

shortopts = "hi:o:";
longopts = ["help", "input=", "output="];

def main(argv, shortopts, longopts):
    inputpath = None
    outputfile = None

    try:
        opts, args = getopt.getopt(argv, shortopts, longopts)
    except getopt.GetoptError:
        print('icu_patient_checker.py -i <path to directory> -o <path to output list>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('icu_patient_checker.py -i <path to directory> -o <path to output list>')
            sys.exit()
        elif opt in ("-i", "--input"):
            inputpath = arg
        elif opt in ("-o", "--output"):
            outputfile = arg
        else:
            print('icu_patient_checker.py -i <path to directory> -o <path to database list>')

    if outputfile == None:
        sys.exit('No outputfile specified')
    elif inputpath == None:
        sys.exit('No input specified')

    outputname, output_ext = os.path.splitext(outputfile)
    if (output_ext not in ('.csv', '.xls', '.xlsx')):
        sys.exit('Invalid outputfile')

    # if (input_ext != '.csv'):
    #     sys.exit('Invalid inputpath')

    output = lookupDirectory(inputpath, outputname, output_ext)

    sys.exit(1)

def lookupDirectory (inputpath, outputname, output_ext):
    sid = syn.auth.login()

    outputFrame = pd.DataFrame()

    filepath = "/NSDL_Backup/UCSF_BinFiles_V2/"+inputpath

    json = syn.fileStation.getList(filepath, sid)

    data = json.get("data")

    print(data)

    jsonDF = pd.DataFrame(data.get("files"))
    print(jsonDF)

    writeToFile(jsonDF['name'], outputname+"_names"+output_ext)

    return jsonDF['name']

def writeToFile(entry, path):
    with open(path, 'a+') as f:
        entry.to_csv(f)

if __name__ == "__main__":
    main(sys.argv[1:], shortopts, longopts)
