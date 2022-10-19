# EDI2ODX
Extraction of Best DX out of EDI files

# Motivation
Amateur radio VHF-UHF generally provide the opportunity to make long distance radio contacts, because many stations are on the air at the same time, several "portable" stations having selected an elevated QTH with decent conditions (antenna and power). QSO's are typically logged electronically into an "EDI" file.

The DUBUS magazine gathers announcement of interesting radio contacts for scientific investigations. 

This little script extracts the longest distance QSO's from EDI files and generates .xlsx and .txt file according to DUBUS preferred format:

*Preferred formatting of your report (either TXT or EXCEL) is:
DATE TIME CALL LOCATOR QRB REMARK

DATE in format YYYY-MM-DD
TIME (UTC) in format HH:MM
QRB in format xxx km
In case of TXT use TAB as separator.* 



# Installation
1. Clone the project or simply copy "edi2odx.py" locally
2. Install the *pandas* library if it is not already installed

# Usage
1. Copy any number of EDI file in the current directory
2. optional: edit the distance limits for selecting the QSO on the different bands
3. Run the script
4. .xlsx and .txt files are generated in the local directory 