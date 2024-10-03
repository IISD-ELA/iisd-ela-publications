# Code purpose: Backend code for IISD-ELA Publications Search Engine
# Link to search engine: https://iisd-ela-pubs-search-engine.streamlit.app/
# Author: Idil Yaktubay (iyaktubay@iisd-ela.org)

# Last Updated: 10-03-2024
# Last Updated by: Idil Yaktubay


# Import required modules
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys


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
                    


# Store all author type options in a list
# DO **NOT**!! Change the order of the values in this list
# You can change the values themselves if needed, but 
# do not change the order!
author_type_options = ['<select a filter>',
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


# Define function to clear all search parameters
def clear_search_params():
    for input in inputs_list:
        st.session_state[input] = [] if 'multi' in input else \
                            '<select a filter>' if 'selectbox' in input \
                            else ""
    return


# Define function to set author tags in URL
def generate_author_tag_url(input_tags):
    if input_tags:
        # Change url to include input author tag
        st.query_params['author_tags'] = input_tags

    else:
        # If there's no author input, clear parameters
        st.query_params.clear()


# Define a combined search function
def combined_search(data, 
                    data_type_query=list(), 
                    env_issue_query=list(), 
                    lake_query=list(), 
                    author_query=list(),
                    iisd_ela_rel_query=None, 
                    year_start_query=None, 
                    year_end_query=None, 
                    general_search_query=None):
    
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

    
    # Filter by general search queries
    if general_search_query:
        data = data[data.loc[:, ~data.columns.isin(['source',
                                        'approved_date',
                                        'approved_by',
                                        'approved',
                                        'account',
                                        'update_date'])
                        ].apply(lambda row: 
                            row.astype(str).str.contains(general_search_query,
                                                        case=False).any(), 
                               axis=1)
                    ]
    
    # Filter by author types current researchers or other researchers (no students)
    if iisd_ela_rel_query in [author_type_options[1], author_type_options[2]]:

        # Create mapping instructions
        author_type_options_mapping = {'authored': author_type_options[1],
                                   'supported': author_type_options[2]}
        
        # Apply mapping instructions to data
        data['relationship_to_iisd_ela'] = \
            data['relationship_to_iisd_ela'].map(author_type_options_mapping)

        # Filter data for non-student pubs that satisfy the author type query
        data = data[(data['relationship_to_iisd_ela']==iisd_ela_rel_query) &
                    ~(data['type'].isin(['msc', 'phd']))]
        
    # Filter by author type students
    elif iisd_ela_rel_query == author_type_options[3]:
        data = data[data['type'].isin(['msc', 'phd'])]

    return data


#==========================CODE FOR SCIENTIST PROFILES============================

# SECTION PURPOSE: 
    # This is the backend code for IISD-ELA search engine results for queried
    # scientists.
    # For any scientist queries in the app URL, the code in this section will return
    # a list of publications for the queried scientist.
    # The page resulting from the code in this section will not have any UI features
    # (e.g., search by lake). Rather, it will only have a list of publications
    # for the purposes of embedding this list into the corresponding scientist
    # profile on the IISD-ELA website.


# Check if URL has scientist queries
if 'author_tags' in st.query_params:
    st.write(st.query_params.author_tags)

    
    # Filter results by the queried scientist in the URL
    result_for_scientist = combined_search(data=data, 
                                           author_query= \
                            [st.query_params['author_tags']]).sort_values(
                                                           by=['authors', 'year'])
    

    # Prepare authors values for APA format
    result_for_scientist['authors'] = \
        result_for_scientist['authors'].str.replace(';', ',')
    

    # Create Title
    st.markdown(
            f"<h2 style='color: #083266;'>Publications by {st.query_params.author_tags}</h2>",
            unsafe_allow_html=True
                        )
    

    # Create container to enable scrolling
    with st.container(height=500, border=False):


        # Display each row as a string
        for index, row in result_for_scientist.iterrows():


            # Format journal articles in APA 7th ed format
            if row['type'] == 'journal':
                row_string =(f"{row['authors']} ({row['year']}). " 
                                f"{row['title']}. *{row['journal_name']}*, " 
                                f"*{str(int(row['journal_vol_no']))}*" 
                                f"({str(int(row['journal_issue_no']))})" 
                                f"{', '+str(row['journal_page_range']) if not pd.isna(row['journal_page_range']) else ''}. " 
                                f"{row['doi_or_url']}"
                            )
                

            # Format theses in APA 7th ed format
            elif row['type'] in ['msc', 'phd']:
                row_string = (f"{row['authors']} ({row['year']}). "
                                f"*{row['title']}* "
                                f"[{'Doctoral dissertation' if row['type']=='phd' else 'Master of Science dissertation'}, "
                                f"{row['thesis_uni']}]. "
                                f"{row['thesis_db']+'.' if not pd.isna(row['thesis_db']) else ''} "
                                f"{row['doi_or_url'] if not pd.isna(row['doi_or_url']) else ''}"
                            )   
            
            # Write tag information into question mark icon for each publication
            tag_info = f"""**Lakes:** {row['lake_tags']}  
                            **Data Types:** {row['data_type_tags']}  
                            **Environmental Issues:** {row['environmental_issue_tags']}  
                        """
            
            # Display each formatted publication with question mark icon
            st.markdown(row_string, 
                        unsafe_allow_html=True,
                        help=tag_info) 

    st.stop()

#============================CODE FOR SEARCH ENGINE================================

# SECTION PURPOSE:
    # This is the backend code for the actual IISD-ELA search engine.
    # Link to search engine: https://iisd-ela-pubs-search-engine.streamlit.app/
    # When the user adds query parameters for scientists to the URL above, the code
    # in this section will not run. Instead, the app will only return search
    # results based on the scientist query in the URL by running the code in the
    # previous section and terminating the rest of the code.


# Create separate columns for search functions and search results
col1, col2 = st.columns(spec=[0.3, 0.7])

# Fill the search functions column with search widgets
with col1: 
    # Add a multi-select widget for data type tags
    tags_help_general = """You may choose multiple,
                           which will return search results 
                           for *any* of the tags ("OR" logic).  
                          """
    data_type_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{data} \: \bold{types}$",
                                     options=data_types, 
                                     key='multi_data_type_tags',
                                     help=tags_help_general)


    # Add a multi-select widget for environmental issue tags
    env_issue_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{environmental} \: \bold{issues}$", 
                                    options=env_issues, 
                                    key='multi_env_issue_tags',
                                    help=tags_help_general)
    

    # Add a multi-select widget for lake tags
    lake_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{lakes}$ ", 
                               options=unique_lakes, 
                               key='multi_lake_tags',
                               help=tags_help_general)


    # Add a multi-select widget for author tags
    author_tags_help = """To search by authors who are not currently
                          IISD-ELA researchers, please use the "General Search"
                          function.
                       """
    # This will look for any author tags in embed URL (for scientist profiles only)
    if 'author_tags' in st.query_params:
        author_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{authors}$",
                                     options=sorted(iisd_ela_authors),
                                     key='multi_author_tags',
                                     default=st.query_params.author_tags,
                                     help=tags_help_general + 
                                          author_tags_help)
    # If no author tags in URL, proceed as normal
    else:
        author_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{authors}$",
                                     options=sorted(iisd_ela_authors),
                                     key='multi_author_tags',
                                     help=tags_help_general + 
                                     author_tags_help)

    
    # Add a selectbox widget for author types (default is set to <select a filter>)
    author_types_help = """The filters are mutually exclusive and you may
                           only choose one.
                        """
    author_types = st.selectbox(r"$\bold{Filter} \: \bold{by} \: \bold{author} \: \bold{type}$",
                                           options=author_type_options, 
                                           index=author_type_options.index('<select a filter>'),
                                           key='selectbox_author_type',
                                           help=author_types_help)
    

    # Create columns for side-by-side year filters
    col3, col4 = st.columns(2)


    # Fill columns with year filters
    with col3:
        year_start_help = """This will filter the search results
                             to show only publications published
                             *in* or *after* the input year.
                          """
        year_range_start = st.text_input(r"$\bold{Publication} \: \bold{year} \: \bold{start}$", "",
                                         key='text_year_start',
                                         help=year_start_help)
    with col4:
        year_end_help = """This will filter the search results
                           to show only publications published
                           *in* or *before* the input year.
                          """
        year_range_end = st.text_input(r"$\bold{Publication} \: \bold{year} \: \bold{end}$", "",
                                       key='text_year_end',
                                       help=year_end_help)


    # Add a general search box
    gen_search_help = """You can search by any keyword,
                         such as those in the article
                         title or other generally related
                         keywords that may be included with
                         the publication metadata (e.g., "cyanobacteria").
                      """
    general_search_query = st.text_input(r"$\bold{General} \: \bold{search}$", "",
                                         key='text_gen_search',
                                         help=gen_search_help)
        

# Write notes on the bottom of the page
st.markdown('**<div style="font-size: 12px;">If you notice any missing publications or encounter issues with this search engine, please reach out to us at eladata@iisd-ela.org.**</div>',
                unsafe_allow_html=True)


# Call combined_search function to filter the data based on user queries
result_for_user = combined_search(
                                data, 
                                data_type_tags,
                                env_issue_tags,
                                lake_tags,
                                author_tags,
                                author_types,
                                year_range_start,
                                year_range_end,
                                general_search_query
                                ).sort_values(by=['authors', 'year'])


# Prepare authors values for APA format
result_for_user['authors'] = result_for_user['authors'].str.replace(';', ',')


with col2:


    # Split right hand side into two columns for header and
    # clear all search parameters button
    col5, col6 = st.columns(spec=[0.8, 0.2])

    with col5:
        st.markdown(
            f"<h2 style='color: #083266;'>Search Results ({len(result_for_user)})</h2>",
            unsafe_allow_html=True
                        )
        
    with col6:
        # Store all widget keys in a list 
        # this is so that clear_search_params can access widgets to clear inputs
        inputs_list = [key for key in st.session_state.keys()]

        # Add a clear all search parameters button
        st.button('Clear all search parameters', on_click=clear_search_params)
        

    if len(result_for_user) == 0:
        st.markdown(f"No publications were found for your search.")
    else:
        with st.container(height=500, border=False):

            # Display each row as a string
            for index, row in result_for_user.iterrows():


                # Format journal articles in APA 7th ed format
                if row['type'] == 'journal':
                    row_string =(f"{row['authors']} ({row['year']}). " 
                                 f"{row['title']}. *{row['journal_name']}*, " 
                                 f"*{str(int(row['journal_vol_no']))}*" 
                                 f"({str(int(row['journal_issue_no']))})" 
                                 f"{', '+str(row['journal_page_range']) if not pd.isna(row['journal_page_range']) else ''}. " 
                                 f"{row['doi_or_url']}"
                                )
                    

                # Format theses in APA 7th ed format
                #elif row['type']=='msc' or row['type']=='phd':
                elif row['type'] in ['msc', 'phd']:
                    row_string = (f"{row['authors']} ({row['year']}). "
                                  f"*{row['title']}* "
                                  f"[{'Doctoral dissertation' if row['type']=='phd' else 'Master of Science dissertation'}, "
                                  f"{row['thesis_uni']}]. "
                                  f"{row['thesis_db']+'.' if not pd.isna(row['thesis_db']) else ''} "
                                  f"{row['doi_or_url'] if not pd.isna(row['doi_or_url']) else ''}"
                                )   
                
                # Write tag information into question mark icon for each publication
                tag_info = f"""**Lakes:** {row['lake_tags']}  
                               **Data Types:** {row['data_type_tags']}  
                               **Environmental Issues:** {row['environmental_issue_tags']}  
                            """
                
                # Display each formatted publication with question mark icon
                st.markdown(row_string, 
                            unsafe_allow_html=True,
                            help=tag_info) 
        
    