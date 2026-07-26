import logging
from core.tankerkoenig_gateway.tk_connector import TankerkoenigConnector

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def example_call():
    connector = TankerkoenigConnector()
    response = connector.get_nearby_stations(
        lng=11.48, lat=48.778, rad=25, type="diesel", sort="price"
    )
    logger.info("\nStatus code:\t %d", response.status_code)
    logger.debug("\nResponse json:\t %s", response.json())
    logger.debug("\nResponse text:\t %s", response)

if __name__ == "__main__":
    example_call()
