# Code purpose: Backend code for IISD-ELA Publications Search Engine
# Link to search engine: https://iisd-ela-pubs-search-engine.streamlit.app/
# Author: Idil Yaktubay (iyaktubay@iisd-ela.org)

# Last Updated: 09-26-2024
# Last Updated by: Idil Yaktubay


# Import required modules
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd


# Set page layout to wide to occupy more of the display
st.set_page_config(layout="wide")


# Connect to Google Sheet containing publications data
conn = st.connection("gsheets", type=GSheetsConnection)
all_data = conn.read(worksheet="Publications") 
authors_data = conn.read(worksheet="Current_IISD-ELA_Authors")


# Filter for approved rows and rows added by data team
data = all_data[all_data['approved'].isin(['Yes', 'Not applicable'])]


# Python reads year data as float point numbers
# So, convert float to integer (2016.0 -> 2016) 
# and then convert integer to string (2016 -> "2016")
data['year'] = data['year'].astype(int).astype(str)


# For records with a single lake tag, Python reads
# lake tags as float point numbers (bad)
# So, convert all lake tags to string
data['lake_tags'] = data['lake_tags'].astype(str)


# Store all data type tags in a list
data_types = sorted(['Physical Limnology',
                      'Zooplankton',
                      'Hydrology',
                      'Meteorology',
                      'Fish',
                      'Chemistry',
                      'Algae'])
data_types.append('Other')


# Store all environmental issue tags in a list
env_issues = sorted(['Acid Rain',
                      'Algal Blooms',
                      'Climate Change',
                      'Drugs',
                      'Mercury',
                      'Oil Spills',
                      'Plastics'])
env_issues.append('Other')
                    


# Store all author type tags in a list
# DO **NOT**!! Change the order of the values in this list
# You can change the values themselves if needed, but 
# do not change the order!
rel_to_iisd_ela = ['<select a filter>',
                    'Current IISD-ELA researchers',
                    'Other researchers (supported by IISD-ELA)',
                    'Students (theses)']


# Store all current IISD-ELA authors in a list
iisd_ela_authors = authors_data['authors']


# Store all distinct lakes in the data in a list
unique_lakes = sorted(list({int(num_str) for num_str in \
                            set(data['lake_tags'].str.split('; ').sum()) 
                            if num_str.isdigit()}))
unique_lakes.append('Other or Unspecified')


# Define a combined search function
def combined_search(data, 
                    data_type_query, 
                    env_issue_query, 
                    lake_query, 
                    author_query,
                    iisd_ela_rel_query, 
                    year_start_query, 
                    year_end_query, 
                    general_search_query):
    
    # Define a list of query and condition pairs for search by functions
    queries = [ (data_type_query,
                    data.apply(lambda row: 
                                    any(data_type_tag in row['data_type_tags'].split('; ') 
                                        for data_type_tag in data_type_query), 
                                axis=1)),
                (env_issue_query,
                    data.apply(lambda row:
                                    any(env_issue_tag in row['environmental_issue_tags'].split('; ') 
                                        for env_issue_tag in env_issue_query),
                                axis=1)), 
                (lake_query,
                    data.apply(lambda row:
                                    any(str(lake_tag) in row['lake_tags'].split('; ')
                                        for lake_tag in lake_query),
                                axis=1)),
                (author_query, 
                    data.apply(lambda row:
                                    any(author_tag in [s.replace('& ', '') 
                                                        for s in row['authors'].split('; ')]
                                        for author_tag in author_query),
                                axis=1)),
                (general_search_query,
                    data.apply(lambda row: 
                                    row.astype(str).str.contains(general_search_query,
                                                                 case=False).any(), 
                                                                 axis=1))
              ]

    
    # Gather all dataframes that satisfy at least one of the query-condition pairs
    list_result_datasets = []
    for query, condition in queries:
        if query:
            list_result_datasets.append(data[condition])

    # Concatenate all dataframes that satify at least one of the query-condition pairs
    # Also drop duplicates
    if len(list_result_datasets) > 0:
        data = \
          pd.concat(list_result_datasets, ignore_index=True, axis=0).drop_duplicates()

    # Filter by year queries
    if year_start_query:
        data = data[lambda data: data['year'] >= year_start_query]
    if year_end_query:
        data = data[lambda data: data['year'] <= year_end_query]
    
    # Filter by author types current researchers or other researchers (no students)
    if rel_to_iisd_ela_query in [rel_to_iisd_ela[1], rel_to_iisd_ela[2]]:

        # Create mapping instructions
        rel_to_iisd_ela_mapping = {'authored': rel_to_iisd_ela[1],
                                   'supported': rel_to_iisd_ela[2]}
        
        # Apply mapping instructions to data
        data['relationship_to_iisd_ela'] = \
            data['relationship_to_iisd_ela'].map(rel_to_iisd_ela_mapping)

        # Filter data for non-student pubs that satisfy the author type query
        data = data[(data['relationship_to_iisd_ela']==iisd_ela_rel_query) &
                    ~(data['type'].isin(['msc', 'phd']))]
        
    # Filter by author type students
    elif rel_to_iisd_ela_query == rel_to_iisd_ela[3]:
        data = data[data['type'].isin(['msc', 'phd'])]

    return data


# Create separate columns for search functions and search results
col1, col2 = st.columns(spec=[0.3, 0.7])

# Fill the search functions column with search widgets
with col1: 
    # Add a multi-select widget for data type tags
    data_type_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{data} \: \bold{type}$",
                                     options=data_types)


    # Add a multi-select widget for environmental issue tags
    env_issue_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{environmental} \: \bold{issue}$", 
                                    options=env_issues)
    

    # Add a multi-select widget for lake tags
    lake_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{lake}$ ", 
                               options=unique_lakes)


    # Add a multi-select widget for author tags
    author_search_query = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{authors}$",
                                         options=sorted(iisd_ela_authors))
    
    
    # Add a selectbox widget for author types (default is set to <select a filter>)
    rel_to_iisd_ela_query = st.selectbox(r"$\bold{Filter} \: \bold{by} \: \bold{author} \: \bold{type}$",
                                           options=rel_to_iisd_ela, 
                                           index=rel_to_iisd_ela.index('<select a filter>'))
    

    # Create columns for side-by-side year filters
    col3, col4 = st.columns(2)


    # Fill columns with year filters
    with col3:
        year_range_start_query = st.text_input(r"$\bold{Publication} \: \bold{year} \: \bold{start}$", "")
    with col4:
        year_range_end_query = st.text_input(r"$\bold{Publication} \: \bold{year} \: \bold{end}$", "")


    # Add a general search box
    general_search_query = st.text_input(r"$\bold{General} \: \bold{search}$", "")


# Write notes on the bottom of the page
st.markdown(f"<h4 style='color: #083266;'>Notes</h4>", unsafe_allow_html=True)
st.markdown('''<div style="font-size: 12px;">
                    <u1> 
                        <li> The "Search by author(s)" function will only work for current IISD-ELA researchers.\nTo search by other researchers, please use the "General search" function. </li>
                        <li> The "Search by" functions will generate results that match any of the tags you have selected. The "Filter by" function will narrow down results to only those that meet the selected filter criteria. </li>
                        <li> You can hover above the question mark icons to see the tags associated with each publication. </li>
                        <li> You can search by any keyword that may not appear in the publication texts themselves (e.g., "cyanobacteria") using the "General search" function as most records are tagged with additional invisible keywords. </li>
                    </u1>
            </div>
            ''',
                unsafe_allow_html=True)
st.markdown('**<div style="font-size: 12px;">If you notice any missing publications or encounter issues with this search engine, please reach out to us at eladata@iisd-ela.org.**</div>',
                unsafe_allow_html=True)


# Call combined_search function to filter the data based on user queries
result_for_user = combined_search(
                                data, 
                                data_type_tags,
                                env_issue_tags,
                                lake_tags,
                                author_search_query,
                                rel_to_iisd_ela_query,
                                year_range_start_query,
                                year_range_end_query,
                                general_search_query
                                ).sort_values(by=['authors', 'year'])


# Prepare authors values for APA format
result_for_user['authors'] = result_for_user['authors'].str.replace(';', ',')


with col2:
    # Display the filtered data
    if len(result_for_user) == 0:
        st.markdown(f"No publications were found for your search.")
    else:
        st.markdown(
        f"<h2 style='color: #083266;'>Search Results ({len(result_for_user)})</h2>",
        unsafe_allow_html=True
                    )
        with st.container(height=500, border=False):

            # Display each row as a string
            for index, row in result_for_user.iterrows():


                # Format journal articles in APA 7th ed format
                if row['type'] == 'journal':
                    row_string =(f"- {row['authors']} ({row['year']}). " 
                                 f"{row['title']}. *{row['journal_name']}*, " 
                                 f"*{str(int(row['journal_vol_no']))}*" 
                                 f"({str(int(row['journal_issue_no']))})" 
                                 f"{', '+str(row['journal_page_range']) if not pd.isna(row['journal_page_range']) else ''}. " 
                                 f"{row['doi_or_url']}"
                                )
                    

                # Format theses in APA 7th ed format
                #elif row['type']=='msc' or row['type']=='phd':
                elif row['type'] in ['msc', 'phd']:
                    row_string = (f"- {row['authors']} ({row['year']}). "
                                  f"*{row['title']}* "
                                  f"[{'Doctoral dissertation' if row['type']=='phd' else 'Master of Science dissertation'}, "
                                  f"{row['thesis_uni']}]. "
                                  f"{row['thesis_db']+'.' if not pd.isna(row['thesis_db']) else ''} "
                                  f"{row['doi_or_url'] if not pd.isna(row['doi_or_url']) else ''}"
                                )   
                
                # Write tag information into question mark icon for each publication
                tag_info = f"""**Lakes:** {row['lake_tags']}  
                               **Data Type:** {row['data_type_tags']}  
                               **Environmental Issue:** {row['environmental_issue_tags']}  
                            """
                
                # Display each formatted publication with question mark icon
                st.markdown(row_string, 
                            unsafe_allow_html=True,
                            help=tag_info) 
        
    