rm -f output_master.csv
rm -f output_master_indices.csv
rm -f missing_data.txt
python3 afib_master_generator.py -i PatientList_ischemicstroke-AFib.csv -o output.csv
