# Draft IISD-ELA Publications Search Engine
# Author: Idil Yaktubay
# Last Updated: 2024-08-15

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


#######################debugging stuff start#######################
#url = "https://docs.google.com/spreadsheets/d/1FMSNSxu7-NA2ZSGOEyd01X7xnyRA4R8TRvONNTPuBMo/edit?gid=1098272421#gid=1098272421"

#conn = st.connection("gsheets", type=GSheetsConnection)

#data = conn.read(spreadsheet=url, worksheet='1098272421')
#authors_data = conn.read(spreadsheet=url, worksheet='2088685364')
#######################debugging stuff end#########################


# Convert data types to string
    # This is so that years aren't displayed with decimals and
    # to avoid some data type errors
data['publication_year'] = data['publication_year'].astype(int).astype(str)
data['issue_no'] =  data['issue_no'].astype(int).astype(str)
data['volume_no'] = data['volume_no'].astype(int).astype(str)
data['lake_tags'] = data['lake_tags'].astype(str)

print(data['approved'])
data = data[data['approved']=='Not applicable']
print(data)

# Store all data type tags in a set object
data_types_set = set(['Physical Limnology',
                      'Zooplankton',
                      'Hydrology',
                      'Meteorology',
                      'Fish',
                      'Chemistry',
                      'Algae']) # Add phytoplankton? 

# Store all environmental issue tags in a set object
env_issues_set = set(['Acid Rain',
                      'Algal Blooms',
                      'Climate Change',
                      'Drugs',
                      'Mercury',
                      'Oil Spills',
                      'Plastics',
                      'Other'
                    ])

# Store all *current* IISD-ELA authors in a set object
# Need to get this list from Sumeep or someone else ...
iisd_ela_authors_set = set(authors_data['publication_authors'])


# Define a combined search function
def combined_search(data, 
                    data_type_query, 
                    env_issue_query, 
                    lake_query, 
                    author_query, 
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
                                    any(lake_tag in row['lake_tags'].split('; ')
                                        for lake_tag in lake_query),
                                axis=1)),
                (author_query, 
                    data.apply(lambda row:
                                    any(author_tag in [s.replace('& ', '') 
                                                        for s in row['publication_authors'].split('; ')]
                                        for author_tag in author_query),
                                axis=1)),
                (general_search_query,
                    data.apply(lambda row: 
                                    row.astype(str).str.contains(general_search_query,
                                                                 case=False).any(), 
                                                                 axis=1)),
              ]
    
    list_result_datasets = []
    for query, condition in queries:
        if query: 
            list_result_datasets.append(data[condition])

    if len(list_result_datasets) > 0:
        data = pd.concat(list_result_datasets, ignore_index=True, axis=0).drop_duplicates()
    if year_start_query:
        data = data[lambda data: data['publication_year'] >= year_start_query]
    if year_end_query:
        data = data[lambda data: data['publication_year'] <= year_end_query]
    return data


col1, col2 = st.columns(spec=[0.3, 0.7])
with col1: 
    # Add a multi-select widget for data type tags
    data_type_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{data} \: \bold{type}$",
                                     options=data_types_set)

    # Add a multi-select widget for environmental issue tags
    env_issue_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{environmental} \: \bold{issue}$", 
                                    options=env_issues_set)
    
    # Add a multi-select widget for lake tags
    # a. Get a list of all distinct (unique) lakes in the database
    set_unique_lakes = set(data['lake_tags'].str.split('; ').sum())
    # b. Add the lake tag widget
    lake_tags = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{lake}$ ", 
                               options=sorted(set_unique_lakes))

    # Add aa multi-select widget for author tags
    author_search_query = st.multiselect(r"$\bold{Search} \: \bold{by} \: \bold{author(s)}$",
                                         options=sorted(iisd_ela_authors_set))
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

    st.markdown('**<div style="font-size: 12px;">Please note that the "Search by author(s)" function will only work for current IISD-ELA researchers.\nTo search by other researchers, please use the "General search" function.**</div>',
                unsafe_allow_html=True)

# Filter the data based on the search query and selected tags
result_for_user = combined_search(
                                data, 
                                data_type_tags,
                                env_issue_tags,
                                lake_tags,
                                author_search_query,
                                year_range_start_query,
                                year_range_end_query,
                                general_search_query
                                ).sort_values(by=['publication_authors', 'publication_year'])

# Prepare authors values for MLA format
result_for_user['publication_authors'] = result_for_user['publication_authors'].str.replace(';', ',')


with col2:
    # Display the filtered data
    if len(result_for_user) == 0:
        st.markdown(f"No publications were found for your search.")
    else:
        st.markdown(
        "<h2 style='color: #083266;'>Search Results</h2>",
        unsafe_allow_html=True
                    )
        #st.markdown("## Search Results")
        with st.container(height=500, border=False):
            # Display each row as a string
            for index, row in result_for_user.iterrows():
                row_string = f"- {row['publication_authors']} ({row['publication_year']}). {row['publication_title']}. *{row['journal_name']}*, *{row['volume_no']}*({row['issue_no']}), {row['page_range']}. https://doi.org/{row['doi']}"
                st.markdown(row_string, unsafe_allow_html=True)

        
        


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
