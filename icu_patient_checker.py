import pandas as pd
import numpy as np
import requests as r
import sys, getopt, json

shortopts = "hi:o:";
longopts = ["help", "input=", "output="];

def main(argv, shortopts, longopts):
    try:
        opts, args = getopt.getopt(argv, shortopts, longopts)
    except getopt.GetoptError:
        print 'icu_patient_checker.py -i <path to patient list> -o <path to database list>'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print 'icu_patient_checker.py -i <path to patient list> -o <path to database list>'
            sys.exit()
        elif opt in ("-i", "--input"):
            inputfile = arg
            mrn_data = parseFilename(inputfile)
            output = lookupMRN(mrn_data)
        else:
            print 'icu_patient_checker.py -i <path to patient list> -o <path to database list>'

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
        print 'Malformed CSV, '+ str(err.args)

    return mrnData

def lookupMRN (data_list):
    # for patient in data_list:
    # using one for now
    patient = data_list[0]
    mrn = patient.get('Patient ID')
    admissionDate = patient.get('Admission Date')
    dischargeDate = patient.get('Discharge Date')

    filepath = "/NSDL_Backup/UCSF_BinFiles_V2/"+mrn.lstrip('0')+"/Alarms.csv"

    # payloadApiInfo = {"api":"SYNO.API.Info", "version":"1", "method":"query", "query":"SYNO.FileStation.Download"}
    # info = r.get('http://128.218.210.52:5000/webapi/query.cgi', params=payloadApiInfo)
    # print info.text

    payloadAuth = {"api":"SYNO.API.Auth", "version":"3", "method":"login", "account":"MitchellM", "passwd":"j!rj'w", "session":"FileStation", "format":"cookie"}
    auth = r.get('http://128.218.210.52:5000/webapi/auth.cgi', params=payloadAuth)
    print auth.json()['data']['sid']

    try:
        fileParam = {"api":"SYNO.FileStation.Download", "version":"2", "method":"download", "path":str(filepath), "mode":"download", "_sid":str(auth.json()['data']['sid'])}
        csv = r.get('http://128.218.210.52:5000/webapi/entry.cgi', params=fileParam, stream = True)
        csvDF = pd.read_csv(csv.raw)
        # csv = csvRequest.text
        # print csvRequest
    except ValueError as err:
        print filepath + " was invalid."

    searchCSV(csvDF.to_dict('records'))

def searchCSV (records):
    #Put network query here, returns a csv
    for entry in records:
        if entry.get('Message') == 'AFib':
            print entry

if __name__ == "__main__":
    main(sys.argv[1:], shortopts, longopts)
