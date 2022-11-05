# EDI2ODX
Extraction of Best DX out of EDI files. Plotting QSO statistics and stations position on map 

# Motivation
Amateur radio VHF-UHF contests generally provide the opportunity to make long distance radio contacts.Many stations are on the air at the same time, several "portable" stations having selected an elevated QTH with decent conditions (antenna and power). QSO's are typically logged electronically into an "EDI" file.

The [DUBUS](http://www.dubus.org/) magazine gathers announcement of interesting radio contacts for scientific investigations. 

This script extracts the longest distance QSO's from EDI files and generates .xlsx and .txt file according to DUBUS preferred format:

>*Preferred formatting of your report (either TXT or EXCEL) is:*
> 
>*DATE TIME CALL LOCATOR QRB/MOD REMARK*
>
>*DATE in format YYYY-MM-DD*
> 
>*TIME (UTC) in format HH:MM*
> 
>*QRB in format xxx km*
> 
>*MOD: c for CW, s for SSB, 8 for FT8*
> 
>*In case of TXT use TAB as separator.* 


If wanted, the script can also generate statistics on the QSOs:
- Density probability of the QSO amount over azimuth
- Density probability of the QSB over azimuth
- Display all the contacted station on a map

# Installation
1. Clone the project   
`git clone https://github.com/HB9DTX/EDI2ODX.git` or simply copy "edi2odx.py" locally
2. Install the following python packages if not already installed:
   - *python3-pandas*
   - *numpy*
   - *matplotlib*
   - *math*
   - *geotiler*

# Usage
1. Copy one or more EDI file in the current directory (one file per contest and per activated band)
2. (Optional: edit the distance limits for selecting the QSO on the different bands by editing the "ODX" dictionary in the first lines of the script )
3. (Optional: select whether statistics and map are to be generated: STATSMAP = True/False)
4. Run the script
5. Best DXs files are generated in the local directory for each EDI file available. The generated file name contains the contest start date, the call and the band as stated in the EDI file (ex: 20221001_HB9XC__432MHz_DXs.txt).
6. If statmap is set to True, azimuths and distances histograms plots as wel las a map are generated. They are based on the full log, not only best DX's  
7. If the map boundaries are not suitable (some stations falling outside the map) they can be tweaked by editing MAP_BBOX global variable and running again the script.


# References
- https://ok2kkw.com/ediformat.htm
- https://www.darc.de/fileadmin/_migrated/content_uploads/EDI_REG1TEST.pdf
- http://www.dubus.org/


# Disclaimer
The script is provided without any warranty. But given the fact that original EDI files remain untouched, the risk that something goes wrong is very low. Worst case: the script doesn't run!

The script has only been tested under Ubuntu / python 3

# Licensing
GNU General Public License: https://opensource.org/licenses/gpl-license

maiden.py module credit to: 9V1KG Klaus D Goepel, https://klsin.bpmsg.com, https://github.com/9V1KG/maidenhead
