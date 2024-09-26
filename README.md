# IISD-ELA Publications Search Engine
**Last Updated:** 2024-09-26, **Last Updated By:** Idil Yaktubay (iyaktubay@iisd-ela.org)

## Contents
* [Motivation](#motivation)
* [Usage](#usage)
* [Data Source](#data-source)
* [Contact and Support](#contact-and-support)

## Motivation
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;To help everyone discover IISD-ELA publications, we have compiled an online publications database on Google Sheets and developed a search interface to that database using the open-source Python framework called ```streamlit```. The search interface has been deployed on Streamlit Community Cloud and will soon be embedded into the IISD-ELA website for all users to access.

## Usage
- Click [here](https://iisd-ela-pubs-search-engine.streamlit.app/) to navigate to the IISD-ELA search engine. By default, the search engine will display a catalogue of *all* quality-checked publications in the backend Google Sheet database. 
- The search results can be narrowed down by search tags of interest using the "Search by data type", "Search by environmental issue", "Search by lake", and "Search by author(s)" functions. When multiple of these tags are chosen, the search engine will display publications that match *any* of the tags you selected. 
- The search results can also be filtered using the "Filter by author type", "Publication year start", "Publication year end", and "General search" functions. When these filters are used, the search engine will *only* display publications that meet the selected filter criteria. 
- In addition, the user can search publications by any keyword that may not appear in the publication texts themselves (e.g., "eutrophication", "cyanobacteria") using the "General search" function as most backend records are tagged with additional keywords invisible to the user.
- In all cases, the returned publications will be sorted in alphabetical order and formatted following the APA 7th edition citation rules. 
- To examine the tags associated with each publication, the user can hover above the question mark icons found next to each publication. 

## Data Source
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The publications data for this search engine is pulled directly from a private backend Google Sheet using Google Sheet APIs. For now, the Google Sheet database only contains publications data from 2014-2024. Completing this database to include all IISD-ELA publications is an ongoing effort. Regarding any new publications, the backend database is regularly updated to ensure the search engine is up-to-date with new publications.

## Contact and Support
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;If you encounter any issues or bugs, or would like to receive additional information about this search engine, please contact us at eladata@iisd-ela.org.

