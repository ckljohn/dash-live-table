"""
This script is to stream tcpdump to local Elasticsearch.

Require root permission.
"""
from datetime import datetime
import subprocess as sub
import re
from elasticsearch import Elasticsearch, RequestsHttpConnection, helpers

tcpdump_reg = re.compile(r"IP (?P<IP1>[\w.-]+)\.(?P<Port1>\w+) > (?P<IP2>[\w.-]+)\.(?P<Port2>\w+): (?P<protocol>(?:tc|ud)p) (?P<size>\d+)")
ES_ENDPOINT = 'localhost'
ES_PORT = 9200
ES_AUTH_USER = 'admin'
ES_AUTH_PW = 'admin'
batch_size = 10


def parse_log(log):
    parsed_log = tcpdump_reg.match(log.rstrip().decode())
    try:
        return {
            '_index': 'tcpdump-' + datetime.utcnow().strftime('%Y%m%d'),
            'source_ip': parsed_log.group('IP1'),
            'source_port': parsed_log.group('Port1'),
            'destination_ip': parsed_log.group('IP2'),
            'destination_port': parsed_log.group('Port2'),
            'protocol': parsed_log.group('protocol'),
            'size': int(parsed_log.group('size')),
            'ts': datetime.utcnow()
        }
    except AttributeError:
        return {}


def connect_es():
    print(f'Connecting to the ES Endpoint {ES_ENDPOINT}')
    try:
        auth = (ES_AUTH_USER, ES_AUTH_PW)
        es = Elasticsearch(
            hosts=[{'host': ES_ENDPOINT, 'port': ES_PORT}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=False,
            connection_class=RequestsHttpConnection,
            maxsize=50
        )
        return es
    except Exception as E:
        print(f"Unable to connect to {ES_ENDPOINT}")
        print(E)
        exit(3)


if __name__ == '__main__':
    # Create an ES connection
    es = connect_es()

    # Start tcpdump
    p = sub.Popen(('sudo', 'tcpdump', '-lNqt'), stdout=sub.PIPE)

    actions = []
    for row in iter(p.stdout.readline, b''):
        parsed_log = parse_log(row)
        if parsed_log:
            actions.append(parsed_log)

        # send logs in batch
        if len(actions) >= batch_size:
            for success, info in helpers.parallel_bulk(es, actions, raise_on_error=True):
                if not success:
                    print(info)
            actions = []
