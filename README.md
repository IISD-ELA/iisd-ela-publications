# IISD-ELA Publications Search Engine
**Last Updated:** 2024-10-28

## Contents
* [Motivation](#motivation)
* [Usage](#usage)
* [Data Source](#data-source)
* [Contact and Support](#contact-and-support)

## Motivation
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;To help everyone discover IISD-ELA publications, we have compiled an online publications database on Google Sheets and developed a search interface to that database using the open-source Python framework called ```streamlit```. The search interface has been deployed on Streamlit Community Cloud and embedded into a the IISD Website for all users to access.

## Usage
- The publications search engine can be accessed via the source [IISD-ELA search engine on Streamlit Community Cloud](https://iisd-ela-pubs-search-engine.streamlit.app/) or an embed on a [Publications page of the IISD website](https://www.iisd.org/ela/researchers/publications/). By default, the search engine will display a catalogue of *all* quality-checked publications in the backend Google Sheet database. 
- The search results can be narrowed down by search tags of interest using the "Search by data types", "Search by environmental issues", "Search by lakes", and "Search by authors" functions. When multiple of these tags are chosen, the search engine will display publications that match *any* of the tags you selected. 
- The search results can also be filtered using the "Filter by author type", "Year start", "Year end", and "General search" functions. When these filters are used, the search engine will *only* display publications that meet the selected or entered filter criteria. 
- In addition, the user can search publications by any keyword that may not appear in the publication texts themselves (e.g., "eutrophication", "cyanobacteria") using the "General search" function as most backend records are tagged with additional keywords that may be included with the publication metadata.
- In all cases, the returned publications will be sorted in alphabetical order and formatted following the APA 7th edition citation rules. 
- To examine the tags associated with each publication, the user can hover above the question mark icons found next to each publication. 

## Data Source
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The publications data for this search engine is pulled directly from a [private backend Google Sheet](https://docs.google.com/spreadsheets/d/1USrhFJ-0ujQhubVdnr3ww-2tHtA90CHvZ7MhE9sewtY/edit?gid=1707056458#gid=1707056458) using Google Sheet APIs. This database is updated on an ongoing basis, in an effort to include all IISD-ELA publications.

## Contact and Support
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;If you encounter any issues or bugs, or would like to receive additional information about this search engine, please contact us at eladata@iisd-ela.org.

