import pandas as pd
import numpy as np
import requests as r
import getpass as gp
import datetime as dt
import sys, getopt, json

shortopts = "hi:o:";
longopts = ["help", "input=", "output="];

def main(argv, shortopts, longopts):
    try:
        opts, args = getopt.getopt(argv, shortopts, longopts)
    except getopt.GetoptError:
        print('icu_patient_checker.py -i <path to patient list> -o <path to database list>')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('icu_patient_checker.py -i <path to patient list> -o <path to database list>')
            sys.exit()
        elif opt in ("-i", "--input"):
            inputfile = arg
            mrn_data = parseFilename(inputfile)
            output = lookupMRN(mrn_data)
        else:
            print('icu_patient_checker.py -i <path to patient list> -o <path to database list>')

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
        pwd = gp.getpass(prompt='Enter Password: ')
    except UserWarning as warn:
        print(warn)

    try:
        payloadAuth = {"api":"SYNO.API.Auth", "version":"3", "method":"login", "account":str(usr), "passwd":str(pwd), "session":"FileStation", "format":"cookie"}
        auth = r.get('http://128.218.210.52:5000/webapi/auth.cgi', params=payloadAuth)
        print (auth.json())
        sid = auth.json()['data']['sid']
    except KeyError as err:
        print('Login Failed')
        retry = input('Try again? (Y/N): ')
        if retry in ('Y', 'y', 'yes'):
            return synoLogin()
        else:
            sys.exit(2)
    return sid

def lookupMRN (data_list):
    sid = synoLogin()
    # for patient in data_list:
    # using one for now
    patient = data_list[0]
    mrn = patient.get('Patient ID')
    admissionDate = patient.get('Admission Date')
    dischargeDate = patient.get('Discharge Date')

    filepath = "/NSDL_Backup/UCSF_BinFiles_V2/"+mrn.lstrip('0')+"/Alarms.csv"

    try:
        fileParam = {"api":"SYNO.FileStation.Download", "version":"2", "method":"download", "path":str(filepath), "mode":"download", "_sid":str(sid)}
        csv = r.get('http://128.218.210.52:5000/webapi/entry.cgi', params=fileParam, stream = True)
        csvDF = pd.read_csv(csv.raw, parse_dates=['AlarmStartTime', 'AlarmEndTime'], date_parser = pd.datetools.to_datetime)
        # csv = csvRequest.text
        # print csvRequest
    except ValueError as err:
        print (filepath + " was invalid.")
        return

    searchCSV(csvDF.to_dict('records'))

def searchCSV (records):
    # print(records[0])
    startTimeRange = None
    endTimeRange = None

    def setTimeRange(entry):
        nonlocal startTimeRange
        nonlocal endTimeRange

        if startTimeRange is None:
            startTimeRange = entry.get('AlarmStartTime').to_datetime() - dt.timedelta(minutes=30)
        if endTimeRange is None:
            endTimeRange = entry.get('AlarmEndTime').to_datetime() + dt.timedelta(minutes=30)

    for entry in records:
        if entry.get('Message') == 'AFib':
            print (entry)
            setTimeRange(entry)
            print(startTimeRange)
            print(endTimeRange)
            return



if __name__ == "__main__":
    main(sys.argv[1:], shortopts, longopts)
