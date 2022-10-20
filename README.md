# EDI2ODX
Extraction of Best DX out of EDI files

# Motivation
Amateur radio VHF-UHF contests generally provide the opportunity to make long distance radio contacts.Many stations are on the air at the same time, several "portable" stations having selected an elevated QTH with decent conditions (antenna and power). QSO's are typically logged electronically into an "EDI" file.

The [DUBUS](http://www.dubus.org/) magazine gathers announcement of interesting radio contacts for scientific investigations. 

This little script extracts the longest distance QSO's from EDI files and generates .xlsx and .txt file according to DUBUS preferred format:

>*Preferred formatting of your report (either TXT or EXCEL) is:*
> 
>*DATE TIME CALL LOCATOR QRB REMARK*
>
>*DATE in format YYYY-MM-DD*
> 
>*TIME (UTC) in format HH:MM*
> 
>*QRB in format xxx km*
> 
>*In case of TXT use TAB as separator.* 

an option is provided to indicate the mode (SSB or CW only) as an additional column

# Installation
1. Clone the project   
`git clone https://github.com/HB9DTX/EDI2ODX.git` or simply copy "edi2odx.py" locally
2. Install the *pandas* library if needed

# Usage
1. Copy one or more EDI file in the current directory
2. (Optional: edit the distance limits for selecting the QSO on the different bands in the first lines of the script)
3. (Optional: select whether the 'MODE' column should be added or not)
4. Run the script
5. Best DXs files are generated in the local directory. The generated file name contains the contest start date, the call and the band as stated in the EDI file (ex: 20221001_HB9XC__432MHz_DXs). .xlsx and .txt are both available


# References
- https://ok2kkw.com/ediformat.htm
- https://www.darc.de/fileadmin/_migrated/content_uploads/EDI_REG1TEST.pdf
- http://www.dubus.org/


# Disclaimer
The script is provided without any warranty. But given the fact that original EDI files remain untouched, the risk that something goes wrong is very low. Worst case: the script doesn't run!

The script has only been tested under Ubuntu / python 3

# License
GNU General Public License: https://opensource.org/licenses/gpl-license
