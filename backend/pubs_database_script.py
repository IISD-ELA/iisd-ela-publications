# Draft IISD-ELA Publications Search Engine
# Author: Idil Yaktubay
# Last Updated: 2024-09-19

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd


# Set page layout to wide (occupy more of the display)
st.set_page_config(layout="wide")


# Set page title
#st.markdown("<h1 style='text-align: center; color: #083266;'>IISD-ELA Publications Search Engine</h1>", unsafe_allow_html=True)
#st.title("IISD-ELA Publications Search Engine", )


# Connect to Google Sheet containing publications data
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="Publications") 
authors_data = conn.read(worksheet="Current_IISD-ELA_Authors")


# Filter out unapproved rows that were added by staff outside data team
data = data[data['approved'].isin(['Yes', 'Not applicable'])]


# Filter out publication types other than journal articles for now
# Theses will be added to the db later and code will be added to deal with them
#data = data[data['type']=='journal']


# Convert data types to string
    # This is so that years aren't displayed with decimals and
    # to avoid some data type errors
data['year'] = data['year'].astype(int).astype(str)
data['lake_tags'] = data['lake_tags'].astype(str)


# Store all data type tags in a list
data_types = sorted(['Physical Limnology',
                      'Zooplankton',
                      'Hydrology',
                      'Meteorology',
                      'Fish',
                      'Chemistry',
                      'Algae'])
                      # Add phytoplankton? 
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
                    


# Store all relationship to IISD-ELA tags in a list
# DO NOT!! Change the order of the values in this list
rel_to_iisd_ela = ['<select a filter>',
                    'Current IISD-ELA researchers',
                    'Other researchers (supported by IISD-ELA)',
                    'Students (theses)']


# Store all *current* IISD-ELA authors in a set object
# Need to get this list from Sumeep or someone else ...
iisd_ela_authors_set = set(authors_data['authors'])


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

    
    list_result_datasets = []
    for query, condition in queries:
        if query:
            list_result_datasets.append(data[condition])

    if len(list_result_datasets) > 0:
        data = pd.concat(list_result_datasets, ignore_index=True, axis=0).drop_duplicates()
    if year_start_query:
        data = data[lambda data: data['year'] >= year_start_query]
    if year_end_query:
        data = data[lambda data: data['year'] <= year_end_query]
    
    if rel_to_iisd_ela_query in [rel_to_iisd_ela[1], rel_to_iisd_ela[2]]:
        rel_to_iisd_ela_mapping = {'authored': rel_to_iisd_ela[1],
                                   'supported': rel_to_iisd_ela[2]}
        data['relationship_to_iisd_ela'] = data['relationship_to_iisd_ela'].map(rel_to_iisd_ela_mapping)
        data = data[data['relationship_to_iisd_ela']==iisd_ela_rel_query]
    elif rel_to_iisd_ela_query == rel_to_iisd_ela[3]:
        data = data[data['type'].isin(['msc', 'phd'])]

    return data


col1, col2 = st.columns(spec=[0.3, 0.7])
with col1: 
    # Add a multi-select widget for data type tags
    data_type_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{data} \: \bold{type}$",
                                     options=data_types)

    # Add a multi-select widget for environmental issue tags
    env_issue_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{environmental} \: \bold{issue}$", 
                                    options=env_issues)
    

    # Store all distinct lakes in the data in a list
    unique_lakes = sorted(list({int(num_str) for num_str in set(data['lake_tags'].str.split('; ').sum()) 
                                    if num_str.isdigit()}))
    unique_lakes.append('Other or Unspecified')
    # b. Add a multi-select widget for lake tags
    lake_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{lake}$ ", 
                               options=unique_lakes)

    # Add a multi-select widget for author tags
    author_search_query = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{author(s)}$",
                                         options=sorted(iisd_ela_authors_set))
    
    # Add a multi-select widget for relationship to IISD-ELA
    rel_to_iisd_ela_query = st.selectbox(r"$\bold{Filter} \: \bold{by} \: \bold{author} \: \bold{type}$",
                                           options=rel_to_iisd_ela, index=rel_to_iisd_ela.index('<select a filter>'))
    
    # Add year range start and end boxes
    # Create columns for side-by-side inputs
    col3, col4 = st.columns(2)
    # Add a search box for the general search query in the first column
    with col3:
        year_range_start_query = st.text_input(r"$\bold{Publication} \: \bold{year} \: \bold{start}$", "")
    # Add a search box for the "lake_tags" in the second column
    with col4:
        year_range_end_query = st.text_input(r"$\bold{Publication} \: \bold{year} \: \bold{end}$", "")

    # Add a general search box
    general_search_query = st.text_input(r"$\bold{General} \: \bold{search}$", "")

st.markdown(f"<h4 style='color: #083266;'>Notes</h4>", unsafe_allow_html=True)
st.markdown('''<div style="font-size: 12px;">
                    <u1> 
                        <li> The "Search by author(s)" function will only work for current IISD-ELA researchers.\nTo search by other researchers, please use the "General search" function. </li>
                        <li> The "Search by" functions will generate results that match any of the tags you have selected. The "Filter by" function will narrow down results to only those that meet the selected filter criteria. </li>
                    </u1>
            </div>
            ''',
                unsafe_allow_html=True)
st.markdown('**<div style="font-size: 12px;">If you notice any missing publications or encounter issues with this search engine, please reach out to us at eladata@iisd-ela.org.**</div>',
                unsafe_allow_html=True)


# Filter the data based on the search query and selected tags
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
        #st.markdown("## Search Results")
        with st.container(height=500, border=False):
            # Display each row as a string
            for index, row in result_for_user.iterrows():
                if row['type'] == 'journal':
                    row_string = f"- {row['authors']} ({row['year']}). {row['title']}. *{row['journal_name']}*, *{str(int(row['journal_vol_no']))}*({str(int(row['journal_issue_no']))}){', '+str(row['journal_page_range']) if not pd.isna(row['journal_page_range']) else ''}. {row['doi_or_url']}"
                elif row['type']=='msc' or row['type']=='phd':
                    row_string = f"- {row['authors']} ({row['year']}). *{row['title']}* [{'Doctoral dissertation' if row['type']=='phd' else 'Master of Science dissertation'}, {row['thesis_uni']}]. {row['thesis_db']+'.' if not pd.isna(row['thesis_db']) else ''} {row['doi_or_url'] if not pd.isna(row['doi_or_url']) else ''}"
                st.markdown(row_string, 
                            unsafe_allow_html=True,
                            help=f"Lakes: {row['lake_tags']}, "+
                                 f"Data Types: {row['data_type_tags']}, " +
                                 f"Environmental Issues: {row['environmental_issue_tags']}")

        
        


# URL of the background image
#image_url = 'https://www.iisd.org/ela/wp-content/uploads/2020/12/Evening-on-Lake-240-HH-2019-scaled-1.jpeg'
# Define CSS for background image 
#background_image = f"""
#<style>
#[data-testid="stAppViewContainer"] > .main {{
   # background-image: url('{image_url}');
    #background-attachment: fixed;
    #background-size: cover;
#}}
#</style>
#"""
# Inject CSS with st.markdown
#st.markdown(background_image, unsafe_allow_html=True)
