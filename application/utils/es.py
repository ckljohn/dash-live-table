import logging
from elasticsearch import Elasticsearch, RequestsHttpConnection

logger = logging.getLogger(__name__)
ES_AUTH_USER = 'admin'
ES_AUTH_PW = 'admin'


def connect_es(host, port=443, verify_certs=True):
    logger.info(f'Connecting to the ES Endpoint {host}')
    auth = (ES_AUTH_USER, ES_AUTH_PW)
    try:
        return Elasticsearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection,
            timeout=100
        )
    except Exception as e:
        logger.error(f"Unable to connect to {host}")
        logger.error(e)
        exit(3)
