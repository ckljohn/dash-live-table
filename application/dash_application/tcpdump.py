"""Create a Dash app within a Flask app."""
import os
import json
import dash
import dash_table
# from dash_table.Format import Format, Scheme
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_core_components as dcc
# from .layout import html_layout
from application.utils.es import connect_es
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

ES_ENDPOINT = os.environ.get('ES_ENDPOINT', 'localhost')
ES_PORT = int(os.environ.get('ES_PORT', '9200'))
ES_VERIFY_CERTS = eval(os.environ.get('ES_VERIFY_CERTS', 'False'))
APP_NAME = 'tcpdump'
APP_CONFIG = json.loads(os.environ['APP_CONFIG'])[APP_NAME]


def add_dash(server):
    """Create a Dash app."""
    external_stylesheets = [
        '/dash-apps/static/dist/css/style.css',
        'https://fonts.googleapis.com/css?family=Lato',
    ]
    dash_app = dash.Dash(server=server,
                         external_stylesheets=external_stylesheets,
                         routes_pathname_prefix=f'/dash-apps/{APP_NAME}/')

    # Override the underlying HTML template
    # dash_app.index_string = html_layout

    # Create Dash Layout comprised of Data Tables
    dash_app.layout = html.Div([
        dcc.Interval(
            id='graph-update',
            interval=APP_CONFIG.get('refresh_interval', 6000)
        ),
        html.Div(
            children=dash_table.DataTable(
                id='stats_table',
                columns=[
                    {"name": 'source_ip', "id": 'source_ip'},
                    {"name": 'source_port', "id": 'source_port'},
                    {"name": 'destination_ip', "id": 'destination_ip'},
                    {"name": 'destination_port', "id": 'destination_port'},
                    {"name": 'protocol', "id": 'protocol'},
                    {"name": 'count', "id": 'count'},
                    {"name": 'total_size', "id": 'total_size'},
                ],
            )
        )
    ])
    # Initialize callbacks after our app is loaded
    # Pass dash_app as a parameter
    init_callbacks(dash_app)

    return dash_app.server


def get_network_traffic(es, start_dt, end_dt):
    """
    Query ES to get network traffic. You may use native DSL.

    :param es: Elasticsearch client
    :type es: elasticsearch.client.Elasticsearch
    :param start_dt:
    :type start_dt: datetime.datetime
    :param end_dt:
    :type end_dt: datetime.datetime
    :return: query response
    """
    base_query = """
        SELECT 
            source_ip.keyword
            ,source_port.keyword
            ,destination_ip.keyword
            ,destination_port.keyword
            ,protocol.keyword
            ,count(*) count
            ,sum(size) total_size
        FROM tcpdump-*
        WHERE ts between '{start_dt}' and '{end_dt}' 
        GROUP BY 1, 2, 3, 4, 5
        LIMIT 20
        """
    query = base_query.format(start_dt=start_dt.strftime('%Y-%m-%dT%H:%M:%S'),
                              end_dt=end_dt.strftime('%Y-%m-%dT%H:%M:%S'), )

    # Get data from ES
    return es.transport.perform_request(
        method='POST',
        url='/_opendistro/_sql',
        body={'query': query}
    )


def init_callbacks(dash_app):
    # Create an ES connection
    es = connect_es(ES_ENDPOINT, port=ES_PORT, verify_certs=ES_VERIFY_CERTS)

    @dash_app.callback(
        Output('stats_table', 'data'),
        [Input('graph-update', 'n_intervals')]
    )
    def update_stats_table(n):
        """
        Define the callback function here
        """
        nonlocal es

        interval = timedelta(hours=APP_CONFIG.get('window', 1))
        end_dt = datetime.utcnow()
        start_dt = end_dt - interval

        response = get_network_traffic(es, start_dt, end_dt)

        # Parse the response
        data = []
        if response.get('datarows'):
            for row in response['datarows']:
                data.append({
                    'source_ip': row[0],
                    'source_port': row[1],
                    'destination_ip': row[2],
                    'destination_port': row[3],
                    'protocol': row[4],
                    'count': row[5],
                    'total_size': row[6],
                    'last_update': str(end_dt)
                })
            data = sorted(data, key=lambda i: i['count'], reverse=True)[:20]

        return data
