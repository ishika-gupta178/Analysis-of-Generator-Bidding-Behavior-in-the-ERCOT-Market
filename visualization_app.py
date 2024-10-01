import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df = pd.read_csv("melted_non_renewable.csv")

# Create the first graph (Graph 1)
def create_graph1(selected_date, selected_unit, selected_generator, selected_resource_type):
    if selected_date is None or selected_unit is None or selected_generator is None or selected_resource_type is None:
        return go.Figure()

    # Filter the dataframe based on selections
    filtered_df = df[(df['Delivery Date'] == selected_date) & (df['Resource Name'] == selected_unit) & 
                     (df['QSE'] == selected_generator) & (df['Resource Type'] == selected_resource_type)]
    
    # Create a 4x6 subplot grid (24 hours)
    fig = make_subplots(rows=4, cols=6, subplot_titles=[f'Hour {i+1}' for i in range(24)],
                        horizontal_spacing=0.05, vertical_spacing=0.1)
    
    # Plot each hour's data
    for hour, hour_df in filtered_df.groupby('Hour Ending'):
        row = (hour - 1) // 6 + 1
        col = (hour - 1) % 6 + 1
        
        # Add scatter plot for the hour
        fig.add_trace(
            go.Scatter(
                x=hour_df['Supply Bid Value'], 
                y=hour_df['Price Bid Value'],
                mode='markers',
                marker=dict(size=8),
                name=f'Hour {hour}'
            ), row=row, col=col
        )
    
    # Update axis titles
    fig.update_xaxes(title_text='Supply Bid Value', row=4, col=1)
    fig.update_yaxes(title_text='Price Bid Value', row=1, col=1)

    # Update layout
    fig.update_layout(
        height=800, width=1200,
        showlegend=False,
        title_text=f'Supply vs Price for {selected_date}, {selected_unit}, {selected_generator}, {selected_resource_type}'
    )
    
    return fig

# Create the second graph (Graph 2)
def create_graph2(selected_date, selected_unit, selected_generator, selected_resource_type):
    if selected_date is None or selected_unit is None or selected_generator is None or selected_resource_type is None:
        return go.Figure()

    # Filter the dataframe based on selections
    filtered_df = df[(df['Delivery Date'] == selected_date) & (df['Resource Name'] == selected_unit) & 
                     (df['QSE'] == selected_generator) & (df['Resource Type'] == selected_resource_type)]
    
    fig = go.Figure()

    # Plotting for each hour
    for hour in filtered_df['Hour Ending'].unique():
        hour_df = filtered_df[filtered_df['Hour Ending'] == hour]
        fig.add_trace(go.Scatter(
            x=hour_df['Supply Bid Value'],
            y=hour_df['Price Bid Value'],
            mode='markers+lines',
            name=f'Hour {hour}'
        ))

    # Update layout
    fig.update_layout(
        title=f'Supply and Price Bids for {selected_resource_type}, {selected_generator}, {selected_unit}, {selected_date}',
        xaxis_title='Supply Bid',
        yaxis_title='Price Bid',
        showlegend=True
    )

    return fig

# Initialize the main Dash app
app = dash.Dash(__name__)

# Layout with dropdowns for filtering
app.layout = html.Div([
    html.H1("Supply Price Bid Analysis"),
    
    # Dropdown for Resource Type
    dcc.Dropdown(id='resource_type_dropdown', options=[
        {'label': rt, 'value': rt} for rt in df['Resource Type'].unique()
    ], placeholder="Select Resource Type"),
    
    # Dropdown for Generator
    dcc.Dropdown(id='generator_dropdown', placeholder="Select Generator"),
    
    # Dropdown for Unit
    dcc.Dropdown(id='unit_dropdown', placeholder="Select Unit"),
    
    # Dropdown for Date
    dcc.Dropdown(id='date_dropdown', placeholder="Select Date"),

     html.Div([
        html.Button('Show Graph 1 (Separate plot for each hour)', id='btn-graph1', n_clicks=0 , style={'margin-right': '20px'}),
        html.Button('Show Graph 2 (All hours on one plot)', id='btn-graph2', n_clicks=0),
    ], style={'padding': '20px'}),  # Add padding to the div
    
    # Graph for plotting
    dcc.Graph(id='graph-placeholder')
    
    # # Buttons to toggle between graphs
    # html.Button('Show Graph 1 (Separate plot for each hour)', id='btn-graph1', n_clicks=0),
    # html.Button('Show Graph 2 (One plot)', id='btn-graph2', n_clicks=0),
    
    # # Graph for plotting
    # dcc.Graph(id='graph-placeholder')
])

# Callback to update Generator dropdown based on Resource Type
@app.callback(
    Output('generator_dropdown', 'options'),
    [Input('resource_type_dropdown', 'value')]
)
def update_generator_dropdown(selected_resource_type):
    if selected_resource_type is None:
        return []
    
    filtered_df = df[df['Resource Type'] == selected_resource_type]
    generators = filtered_df['QSE'].unique()
    return [{'label': gen, 'value': gen} for gen in generators]

# Callback to update Unit dropdown based on Generator
@app.callback(
    Output('unit_dropdown', 'options'),
    [Input('generator_dropdown', 'value'), Input('resource_type_dropdown', 'value')]
)
def update_unit_dropdown(selected_generator, selected_resource_type):
    if selected_generator is None:
        return []
    
    filtered_df = df[(df['QSE'] == selected_generator) & (df['Resource Type'] == selected_resource_type)]
    units = filtered_df['Resource Name'].unique()
    return [{'label': unit, 'value': unit} for unit in units]

# Callback to update Date dropdown based on Unit
@app.callback(
    Output('date_dropdown', 'options'),
    [Input('unit_dropdown', 'value'), Input('generator_dropdown', 'value'), Input('resource_type_dropdown', 'value')]
)
def update_date_dropdown(selected_unit, selected_generator, selected_resource_type):
    if selected_unit is None:
        return []
    
    filtered_df = df[(df['Resource Name'] == selected_unit) & (df['QSE'] == selected_generator) & (df['Resource Type'] == selected_resource_type)]
    dates = filtered_df['Delivery Date'].unique()
    return [{'label': date, 'value': date} for date in dates]

# Callback to update the graph based on button clicks
@app.callback(
    Output('graph-placeholder', 'figure'),
    Input('btn-graph1', 'n_clicks'),
    Input('btn-graph2', 'n_clicks'),
    Input('date_dropdown', 'value'),
    Input('unit_dropdown', 'value'),
    Input('generator_dropdown', 'value'),
    Input('resource_type_dropdown', 'value')
)
def display_graph(btn1, btn2, selected_date, selected_unit, selected_generator, selected_resource_type):
    # Check which button was clicked and update the graph accordingly
    ctx = dash.callback_context
    if not ctx.triggered:
        return go.Figure()  # No graph displayed initially

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]  # Get the ID of the button that triggered the callback

    if button_id == 'btn-graph1' and btn1 > 0:
        return create_graph1(selected_date, selected_unit, selected_generator, selected_resource_type)  # Show Graph 1
    elif button_id == 'btn-graph2' and btn2 > 0:
        return create_graph2(selected_date, selected_unit, selected_generator, selected_resource_type)  # Show Graph 2
    return go.Figure()  # Default case if no button has been clicked

# Run the app in an external browser
if __name__ == '__main__':
    app.run_server(debug=True)
