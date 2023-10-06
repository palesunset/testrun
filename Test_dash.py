import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import altair as alt
import requests
from io import BytesIO

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .st-bf {  # This targets the title
            font-size: 32px;
        }
        .st-bh {  # This targets the header
            font-size: 20px;
        }
        .st-cm {  # This targets the subheader
            font-size: 24px;
        }
    </style>
    """, unsafe_allow_html=True)


def fetch_github_file(file_name):
    base_url = "https://raw.githubusercontent.com/palesunset/testrun/main/"
    try:
        response = requests.get(base_url + file_name)
        response.raise_for_status()  # This will raise an error if the fetch fails
        return BytesIO(response.content)
    except requests.RequestException:  # If there's a problem with the request (e.g., the file isn't there), return None
        return None

# Try fetching from GitHub first
df1 = pd.read_excel(fetch_github_file("HC_SEMIAUTO_RESULT.xlsx") or st.session_state.uploaded_files.get("HC_SEMIAUTO_RESULT"))


# --------------- 1. Title, Uploaders, and Predefined Values ---------------

st.title('IPCORE TRANSPORT SEGMENT Dashboard')

# Predefined Values
colors = ["green", "yellow", "orange", "red"]
labels = ['Below 50% Links', '51-70% Links', '71-90% Links', 'Above 90% Links']


# Initialize the dictionary for uploaded files in session state (if not already initialized)
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {
        "HC_SEMIAUTO_RESULT": fetch_github_file("HC_SEMIAUTO_RESULT.xlsx"),
        "ONE_LEG_SCENARIO_RESULTS": fetch_github_file("ONE_LEG_SCENARIO_RESULTS.xlsx"),
        "CAPACITY_SUMMARY": fetch_github_file("CAPACITY_SUMMARY.xlsx"),
        "Segregated_HC_SEMI_AUTO": fetch_github_file("Segregated_HC_SEMI_AUTO.xlsx"),
        "Segregated_ONE_LEG_SCENARIO_RESULTS": fetch_github_file("Segregated_ONE_LEG_SCENARIO_RESULTS.xlsx")
    }

# Display uploaders if the files are not yet uploaded
if not st.session_state.uploaded_files["HC_SEMIAUTO_RESULT"]:
    st.session_state.uploaded_files["HC_SEMIAUTO_RESULT"] = st.file_uploader("Upload HC_SEMIAUTO_RESULT.xlsx", type=['xlsx'], key="uploader_1")

if not st.session_state.uploaded_files["ONE_LEG_SCENARIO_RESULTS"]:
    st.session_state.uploaded_files["ONE_LEG_SCENARIO_RESULTS"] = st.file_uploader("Upload ONE_LEG_SCENARIO_RESULTS.xlsx", type=['xlsx'], key="uploader_2")

if not st.session_state.uploaded_files["CAPACITY_SUMMARY"]:
    st.session_state.uploaded_files["CAPACITY_SUMMARY"] = st.file_uploader("Upload CAPACITY_SUMMARY.xlsx", type=['xlsx'], key="uploader_3")

if not st.session_state.uploaded_files["Segregated_HC_SEMI_AUTO"]:
    st.session_state.uploaded_files["Segregated_HC_SEMI_AUTO"] = st.file_uploader("Upload Segregated_HC_SEMI_AUTO.xlsx", type=['xlsx'], key="uploader_4")

if not st.session_state.uploaded_files["Segregated_ONE_LEG_SCENARIO_RESULTS"]:
    st.session_state.uploaded_files["Segregated_ONE_LEG_SCENARIO_RESULTS"] = st.file_uploader("Upload Segregated_ONE_LEG_SCENARIO_RESULTS.xlsx", type=['xlsx'], key="uploader_5")

# If all files are uploaded, display a success message.
if all(st.session_state.uploaded_files.values()):
    st.success("All files uploaded successfully!")
else:
    st.warning("Please upload all 5 files before proceeding.")
    st.stop()


# Embed custom CSS to adjust the font size of the sidebar selectbox and change its color
st.markdown("""
    <style>
        .st-bm .st-bd select {
            background-color: #000FF;  /* This changes the dropdown color */
            color: black;              /* This changes the text color */
            font-size: 18px;
        }
    </style>
    """, unsafe_allow_html=True)

# Adding Radio Button for Segregation
# Create space above the dropdown to push it to the middle.
for _ in range(10):
    st.empty()

# Adding Radio Button for Segregation in the center of the main page
selected_option = st.selectbox("NAVIGATION BAR", [
    "IPCORE TRANSPORT SEGMENT SUMMARY",
    "IPCORE TRANSPORT SEGMENTS CHARTS",
    "IPCORE TRANSPORT SEGMENT CAPACITY",
    "IPCORE TRANSPORT SEGMENT (UTILIZATION) - NORMAL SCENARIO",
    "IPCORE TRANSPORT SEGMENT (UTILIZATION) - ONE-LEG SCENARIO"
])

# Create space below the dropdown to push following content downwards.
for _ in range(10):
    st.empty()

# --------------- 2. Function Definitions ---------------

def generate_table_data(df):
    df_cleaned = df.dropna(subset=['Peak Utilization %', 'Segment', 'Region', 'Link Type']).copy()
    df_cleaned['Peak Utilization %'].fillna(0, inplace=True)
    bins = [-0.01, 0.4999, 0.6999, 0.8999, float('inf')]
    df_cleaned['Utilization Range'] = pd.cut(df_cleaned['Peak Utilization %'], bins=bins, labels=labels, right=True)

    link_types = [lt for lt in df_cleaned['Link Type'].unique() if lt != "Backend"]
    table_data = []

    for link_type in link_types:
        temp_df = df_cleaned[df_cleaned['Link Type'] == link_type]
        if 'Number of Links' in df_cleaned.columns:
            counts = temp_df.groupby('Utilization Range')['Number of Links'].sum().reindex(labels).fillna(0)
        else:
            counts = temp_df.groupby('Utilization Range').size().reindex(labels).fillna(0)
        total = counts.sum()
        table_data.append([link_type] + [int(x) for x in counts.tolist()] + [int(total)])

    return table_data

def display_pie_charts(df, sheet_name):
    df_cleaned = df.dropna(subset=['Peak Utilization %', 'Segment', 'Region', 'Link Type']).copy()
    df_cleaned['Peak Utilization %'].fillna(0, inplace=True)
    bins = [-0.01, 0.4999, 0.6999, 0.8999, float('inf')]
    df_cleaned['Utilization Range'] = pd.cut(df_cleaned['Peak Utilization %'], bins=bins, labels=labels, right=True)
    link_types = df_cleaned['Link Type'].unique()

    chart_counter = 0
    cols = st.columns(5)  # Create 3 columns for horizontal layout

    for link_type in link_types:
        if link_type == "Backend":
            continue
        temp_df = df_cleaned[df_cleaned['Link Type'] == link_type]
        if 'Number of Links' in df_cleaned.columns:
            temp_dist = temp_df.groupby('Utilization Range').agg({'Number of Links': 'sum'}).reindex(labels).fillna(0)['Number of Links']
        else:
            temp_dist = temp_df.groupby('Utilization Range').size().reindex(labels).fillna(0)

        non_zero_labels = [f"{int(val)}" if val > 0 else None for _, val in temp_dist.items()]
        
        # Construct legend labels with counts
        legend_labels = [f"{label} = ({int(count)})" for label, count in temp_dist.items()]

        fig, ax = plt.subplots(figsize=(4, 3), dpi=1000)  # Adjusted the size for better visibility

        wedges, texts = ax.pie(temp_dist, labels=non_zero_labels, colors=colors, startangle=120, wedgeprops=dict(width=0.3), textprops=dict(size=7))
        
        # Get the total counts for each segment
        segment_counts = [f"{label} = ({int(temp_dist[label])})" for label in labels]

        # Position the legend below the donut but centered vertically
        ax.legend(wedges, segment_counts, loc="center", fontsize=5, bbox_to_anchor=(0.5, -0.2), frameon=False)

        ax.set_title(link_type, fontsize=9)
        
        fig.tight_layout()
        cols[chart_counter % 5].pyplot(fig, use_container_width=True)
        chart_counter += 1

def plot_altair_bar_chart_with_labels(df, x_col, y_col, title, sequence=None, width=600, height=400):
    if sequence:
        df = df.set_index(x_col).loc[sequence].reset_index()

    base = alt.Chart(df).encode(
        x=alt.X(f'{x_col}:N', title=x_col, sort=sequence),
        y=alt.Y(f'sum({y_col}):Q', title=y_col)
    ).properties(
        width=width,   # Setting the width here
        height=height  # Setting the height here
    )

    bars = base.mark_bar().encode(
        color=alt.condition(
            alt.datum[y_col] > 0,
            alt.value('skyblue'),
            alt.value('salmon')
        )
    )

    text = base.mark_text(
        align='center',
        baseline='bottom',
        dy=3  # Nudge text upwards
    ).encode(
        text=f'sum({y_col}):Q'
    )

    chart = (bars + text).interactive()

    st.altair_chart(chart)

def display_table(uploaded_file):
    # Sheet name to title mapping
    sheet_to_title = {
        "49.99% and Below": "Normal Links",
        "50% to 69.99%": "Warning Links",
        "70% to 89.99%": "Highly Utilized Links",
        "90% and Above": "Critical Links"
    }
    
    # Title to color mapping
    title_colors = {
        "Normal Links": "green",
        "Warning Links": "yellow",
        "Highly Utilized Links": "orange",
        "Critical Links": "red"
    }

    xls = pd.ExcelFile(uploaded_file)
    table_dataframes = {}  # To store the dataframes for each table

    for index, sheet_name in enumerate(xls.sheet_names):
        df_temp = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        if 'Peak Utilization %' in df_temp.columns:
            df_temp['Peak Utilization %'] = df_temp['Peak Utilization %'].apply(lambda x: f"{x*100:.2f}%")  # Convert to percentage format

        table_dataframes[sheet_name] = df_temp

    # Use Streamlit columns to structure your display
    col1, col2 = st.columns(2)

    # Display tables for col1
    for sheet_name, title in [("49.99% and Below", "Normal Links"), ("70% to 89.99%", "Highly Utilized Links")]:
        df = table_dataframes.get(sheet_name)
        if df is not None:
            color = title_colors.get(title, "black")
            with col1:
                st.markdown(f"<h3 style='color: {color};'>{title}</h3>", unsafe_allow_html=True)
                st.write(df)

    # Display tables for col2
    for sheet_name, title in [("50% to 69.99%", "Warning Links"), ("90% and Above", "Critical Links")]:
        df = table_dataframes.get(sheet_name)
        if df is not None:
            color = title_colors.get(title, "black")
            with col2:
                st.markdown(f"<h3 style='color: {color};'>{title}</h3>", unsafe_allow_html=True)
                st.write(df)

# Displaying Content Based on Selected Radio Button Option

if selected_option == "IPCORE TRANSPORT SEGMENT SUMMARY":
    if st.session_state.uploaded_files["HC_SEMIAUTO_RESULT"]:
        df1 = pd.read_excel(st.session_state.uploaded_files["HC_SEMIAUTO_RESULT"])
        st.subheader("IPCORE TRANSPORT SEGMENTS")
        table_data1 = generate_table_data(df1)
        st.table(pd.DataFrame(table_data1, columns=["TRANSPORT CORE SEGMENTS", "Below 50%", "51-70%", "71-90%", "Above 90%", "Total"]).set_index("TRANSPORT CORE SEGMENTS"))

    if st.session_state.uploaded_files["ONE_LEG_SCENARIO_RESULTS"]:
        df2 = pd.read_excel(st.session_state.uploaded_files["ONE_LEG_SCENARIO_RESULTS"])
        st.subheader("IPCORE TRANSPORT SEGMENTS (ONE-LEG SCENARIO)")
        table_data2 = generate_table_data(df2)
        st.table(pd.DataFrame(table_data2, columns=["TRANSPORT CORE SEGMENTS", "Below 50%", "51-70%", "71-90%", "Above 90%", "Total"]).set_index("TRANSPORT CORE SEGMENTS"))

elif selected_option == "IPCORE TRANSPORT SEGMENTS CHARTS":
    if st.session_state.uploaded_files["HC_SEMIAUTO_RESULT"]:
        df1 = pd.read_excel(st.session_state.uploaded_files["HC_SEMIAUTO_RESULT"])
        st.subheader("IPCORE TRANSPORT SEGMENTS CHARTS")
        display_pie_charts(df1, "IPCORE TRANSPORT SEGMENTS")
    
    if st.session_state.uploaded_files["ONE_LEG_SCENARIO_RESULTS"]:
        df2 = pd.read_excel(st.session_state.uploaded_files["ONE_LEG_SCENARIO_RESULTS"])
        st.subheader("IPCORE TRANSPORT SEGMENTS (ONE-LEG SCENARIO) CHARTS")
        display_pie_charts(df2, "ONE-LEG SCENARIO")


elif selected_option == "IPCORE TRANSPORT SEGMENT CAPACITY":
    if st.session_state.uploaded_files["CAPACITY_SUMMARY"]:
        uploaded_capacity_file = st.session_state.uploaded_files["CAPACITY_SUMMARY"]
        
        # Define df_capacity_1 dataframe here
        df_capacity_1 = pd.read_excel(uploaded_capacity_file, sheet_name=0)
        
        df_capacity_1_grouped = df_capacity_1.groupby('Region')['Total Capacity (Gbps)'].sum().reset_index()
        sequence_1 = ["NLZ", "NLZ-NCR", "NCR", "NCR-NLZ", "NCR-SLZ", "NCR-VIS", "NCR-MIN", "SLZ", "SLZ-NCR", "SLZ-VIS", "VIS", "VIS-SLZ", "VIS-MIN", "MIN", "MIN-VIS"]
        
        df_capacity_2 = pd.read_excel(uploaded_capacity_file, sheet_name=1)
        df_capacity_2_grouped = df_capacity_2.groupby('Link Type')['Total Capacity (Gbps)'].sum().reset_index()
        
        df_capacity_3 = pd.read_excel(uploaded_capacity_file, sheet_name=2)
        df_capacity_3_grouped = df_capacity_3.groupby('Region')['Total Capacity (Gbps)'].sum().reset_index()
        sequence_3 = ["NLZ", "NCR", "SLZ", "VIS", "MIN"]
        
        # Set up columns for horizontal layout
        cols = st.columns(3)
        
        with cols[0]:
            st.subheader("Provisioned Capacity (GBPS) - Regionalized")
            plot_altair_bar_chart_with_labels(df_capacity_1_grouped, 'Region', 'Total Capacity (Gbps)', 'Region vs Total Capacity (Gbps) from Sheet 1', sequence_1, width=400, height=325)
        
        with cols[1]:
            st.subheader("Provisoned Capacity (GPBS) - Per Segment")
            plot_altair_bar_chart_with_labels(df_capacity_2_grouped, 'Link Type', 'Total Capacity (Gbps)', 'Link Type vs Total Capacity (Gbps) from Sheet 2', width=400, height=375)
        
        with cols[2]:
            st.subheader("Provisoned Capacity (GBPS) - ONE-LEG")
            plot_altair_bar_chart_with_labels(df_capacity_3_grouped, 'Region', 'Total Capacity (Gbps)', 'Region vs Total Capacity (Gbps) from Sheet 3', sequence_3, width=350, height=300)

elif selected_option == "IPCORE TRANSPORT SEGMENT (UTILIZATION) - NORMAL SCENARIO":
    if st.session_state.uploaded_files["Segregated_HC_SEMI_AUTO"]:
        display_table(st.session_state.uploaded_files["Segregated_HC_SEMI_AUTO"])

elif selected_option == "IPCORE TRANSPORT SEGMENT (UTILIZATION) - ONE-LEG SCENARIO":
    if st.session_state.uploaded_files["Segregated_ONE_LEG_SCENARIO_RESULTS"]:
        display_table(st.session_state.uploaded_files["Segregated_ONE_LEG_SCENARIO_RESULTS"])
