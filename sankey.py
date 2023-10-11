import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

# Load the data
df = pd.read_excel('HC_SEMIAUTO_RESULT_updated.xlsx')

# Initialize Dash
app = dash.Dash(__name__)

# Define color scheme for the links based on 'Peak Utilization %'
def get_color(value):
    # If the value is a string and has a '%' character, strip it and convert to float
    if isinstance(value, str) and '%' in value:
        value = float(value.strip('%'))
    # If the value is already a float and represents a fraction (e.g., 0.42 for 42%)
    elif isinstance(value, float) and 0 <= value <= 1:
        value = value * 100
    # If the value is already a float representing percentage
    elif isinstance(value, float):
        pass

    if value < 50:
        return 'green'
    elif 50 <= value < 70:
        return 'yellow'
    elif 70 <= value < 90:
        return 'orange'
    else:
        return 'red'



# App layout
app.layout = html.Div([
    dcc.Dropdown(
        id='link-type-filter',
        options=[{'label': link_type, 'value': link_type} for link_type in df['Link Type'].dropna().unique()],
        multi=True,
        value=list(df['Link Type'].unique()),
        placeholder="Select a Link Type"
    ),
    dcc.Graph(id='sankey-graph', style={'height': '1000px'})
])

@app.callback(
    Output('sankey-graph', 'figure'),
    [Input('link-type-filter', 'value')]
)
def update_sankey_chart(link_type_values):
    try:
        # Handle multiple selected values for Link Type
        filtered_df = df[df['Link Type'].isin(link_type_values)]
        
        # Combine and deduplicate the 'From' and 'To' columns to form a list of nodes
        all_nodes = pd.concat([filtered_df['From'], filtered_df['To']]).unique().tolist()
        
        # Create a list of nodes for the sankey diagram
        nodes = [{"name": node} for node in all_nodes]

        # Define Sankey links
        links = []
        for idx, row in filtered_df.iterrows():
            source = all_nodes.index(row['From'])
            target = all_nodes.index(row['To'])

            color = get_color(row['Peak Utilization %'])

            links.append({
                "source": source,
                "target": target,
                "value": row['Total Capacity (Gbps)'],
                "color": color
            })

        # Create Sankey diagram data
        data = dict(
            type='sankey',
            node=dict(
                pad=20,  # Increase padding
                thickness=20,  # Increase thickness
                line=dict(color="black", width=0.2),
                label=[node['name'] for node in nodes]
            ),
            link=dict(
                source=[link['source'] for link in links],
                target=[link['target'] for link in links],
                value=[link['value'] for link in links],
                color=[link['color'] for link in links]
            )
        )
        
        # Layout settings
        layout = go.Layout(height=2000)  # Adjust the figure height here

        # Return the updated figure
        return dict(data=[data], layout=layout)

    except Exception as e:
        print(f"Error processing row {idx}: {row}")
        print(str(e))
        return dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True)
