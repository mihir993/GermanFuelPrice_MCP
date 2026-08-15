import os
import httpx
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class TankerkoenigConnector:
    def __init__(self):
        self.load_env()
        self.api_secret = self._get_api_secret()
        self.base_url = "https://creativecommons.tankerkoenig.de/json"

    @staticmethod
    def load_env():
        load_dotenv()

    @staticmethod
    def _get_api_secret() -> str:
        return os.getenv("TANKERKOENIG_API_KEY")

    @staticmethod
    def _get_http_response(url):
        with httpx.Client() as client:
            response= client.get(url)
            return response

    def get_nearby_stations(self, lat, lng, rad=25, type = "all", sort="dist"):
        php_str = "list.php"
        request_url = (self.base_url + "/" + php_str +
                       "?" + "lat=" + str(lat) +
                       "&" + "lng=" + str(lng) +
                       "&" + "rad=" + str(rad) +
                       "&" + "type=" + type +
                       "&" + "sort=" + sort +
                       "&" + "apikey=" + self.api_secret
                       )
        logger.info(request_url)
        return self._get_http_response(request_url)

    def get_price(self, ids):
        php_str = "prices.php"
        request_url = (self.base_url + "/" + php_str +
                       "?" + "ids=" + str(ids) +
                       "&" + "apikey=" + self.api_secret
                       )

        return self._get_http_response(request_url)

    def get_detail(self, ids):
        php_str = "detail.php"
        request_url = (self.base_url + "/" + php_str +
                       "?" + "ids=" + str(ids) +
                       "&" + "apikey=" + self.api_secret
                       )
        return self._get_http_response(request_url)