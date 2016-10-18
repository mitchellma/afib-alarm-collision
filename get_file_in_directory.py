import pandas as pd
import numpy as np
import requests as r
import getpass as gp
import datetime as dt
import sys, getopt, json, os

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

    if (input_ext != '.csv'):
        sys.exit('Invalid inputpath')

    output = lookupDirectory(inputpath, outputfile)
    # 
    # with open('stats.csv', 'a+') as f:
    #     statDF = pd.DataFrame([stats], columns = statsCol)
    #     statDF.to_csv(f)

    sys.exit(1)

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

def lookupDirectory (inputpath, outputname, output_ext):
    sid = synoLogin()

    outputFrame = pd.DataFrame()

        filepath = "/NSDL_Backup/UCSF_BinFiles_V2/"+inputpath

        try:
            //limit to 1000 files for sanity

            fileParam = {"api":"SYNO.FileStation.List", "version":"2", "method":"list", "path":str(filepath), "limit":1000, "sort_by": "name", "sort_direction": "desc", "_sid":str(sid), }

            response = r.get('http://128.218.210.52:5000/webapi/entry.cgi', params=fileParam)

            response.raise_for_status()

            json = response.json()

            jsonDF = pd.read_json(json.get(files))
        print(jsonDF)

        except (ValueError, r.exceptions.HTTPError) as err:
            print(err)
            print(csv)
            print (filepath + " was invalid.")

    # hasAFib = pd.DataFrame([], columns=['hasAFib'])
    # signalQuality = pd.DataFrame([], columns=['signalQuality'])
    #
    # outputFrameBefore = pd.concat([outputFrameBefore, hasAFib, signalQuality], axis = 1)
    #
    # outputFrameAfter = pd.concat([outputFrameAfter, hasAFib, signalQuality], axis = 1)
    #
    # outputFrameDuring = pd.concat([outputFrameDuring, hasAFib, signalQuality], axis = 1)
    #
    # writeToFile(outputFrameBefore, outputname+'_before'+output_ext)
    # # writeToFile(outputFrameAfter, outputname+'_during'+output_ext)
    # writeToFile(outputFrameDuring, outputname+'_during'+output_ext)
