# Afib

## afib_master_generator.py

### Usage: ```python3 afib_master_generator.py -i input_list.csv -o output_list.csv```

* input_list.csv has columns ` 'Patient ID','Admission Date','Discharge Date' `
	* this is the list of mrns of the targeted patient population
* after parsing the input_list, the Synology web api is accessed via html request at ` http://128.218.210.52:5000/webapi/entry.cgi `
* The synology libraries contain methods for logging into the backup server and getting the authentication token to use the web api.
* The web api is then used to dowload ` /NSDL_Backup/UCSF_BinFiles_V2/"+mrn.lstrip('0')+"/Alarms.csv ` Alarm csv with all the alarms for that patient
* The Alarms.csv is then passed to the `searchCSV` method which searches for alarms where the message was Afib, then appends those alarm instances with the mrn, bed, start, end and duration of the afib alarm to an array of alarm instances.
	* To target other types of alarms change `  if entry.get('Message') == 'AFib': ` to the desired alarm string.
	* An alarm row is built for each AFib instance that contains the MRN, Unit Bed, Alarm beginning and end, duration, etc. from the Alarms.csv
	* The bed is important when later trying to pull the telemetry data as the same patient can have multiple beds.
* Patients without Afib alarms return None
* Finally, the alarm matrix is written to a csv ` output_list_master.csv ` containing all of the Afib alarm segments, as well as a csv ` output_list_master_indices.csv ` that lists the patient MRN to the range of indexes in the alarm matrix, and ` missing_patients.txt ` which are MRNs missing Alarm.csv data or are not in the database.

## afib_annotation_generator.py

### Usage: ```python3 afib_annotation_generator.py -l alarm_list.csv -i indices_list.csv -o output_list.csv```

* ` alarm_list.csv ` is the `output_list_master.csv`, and `indices_list.csv` is the ` output_list_master_indices.csv ` from `afib_master_generator.py`.
* For each patient, 10 afib alarm instances not including the first are randomly chosen from the range defined in indices_list.
	* if there are fewer than 10 instances, all of them are selected
* The first alarm instance of all the patients have one minute appended to their beggining and end to provide background for clinical annotation
* The remaining ten alarm instances are truncated to five minutes if they are longer, and then thirty seconds is appended to the beginning and ten seconds to the end to show any lead in or continuation for annotation purposes.
	* The sampling is controlled by ` parseEntry(list_data, index, start_period, end_period): ` where `list_data` is the parsed `alarm_list.csv`, index is a randomly selected index from `indices_list.csv` and `start_period` and `end_period` are `dt.timedelta` some useful durations are defined at the top of the file
* The new timestamped entries are outputed as a csv `output_list_annotation.csv` for adibin files to be generated from.

## icu_patient_checker.py

This file is an earlier annotation generation script that has been deprecated and replaced by `afib_master_generator.py` and `afib_annotation_generator.py`

## get_file_in_directory.py

### Usage: ```python3 get_file_in_directory.py -i remote_path -o directory.txt```

* given some `remote_path` under `/NSDL_Backup/UCSF_BinFiles_V2/` the list of files under that directory are outputed to directory `directory_names.txt`
* useful for debugging and whatnot

## sanity_check.py

### Usage: ```python3 sanity_check.py -c csv_to_check.csv```

* `csv_to_check.csv` is the output from `afib_annotation_generator.py` and checks that the csv time stamps were properly calculated and there are no malformed entries

## run_master_generator.sh and run_annotation_generator.sh

### Usage: ``` bash run_master_generator.sh && run_annotation_generator.sh ```

* these are wrappers to facilitate deleting old data and running the python scripts on generated data between runs.  Filenames/location are platform specific
