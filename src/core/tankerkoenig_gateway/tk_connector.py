import os
import json
import httpx
import logging
import time

from dotenv import load_dotenv

from core.tools.fuel_station_dataclass import PriceStationId
from src.core.tools.fuel_station_dataclass import FuelStationWithLiveData

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

    def _parse_stations_dataclass(self, data_dict):
        return FuelStationWithLiveData.list_from_dict(data_dict["stations"], timestamp=time.time())

    def _parse_station_price_dataclass(self, data_dict):
        return PriceStationId.from_api_dict(data_dict["prices"])

    def _parse_station_detail(self, data_dict):
        return data_dict # forwarded in same format.

    def post_process_response(self, data):
        data_dict = json.loads(data)

        if data_dict["ok"] != True:
            exception_msg = "API responded with an error.\n" + str(data)
            logger.exception(exception_msg)
            return None

        if "stations" in data_dict:
            return self._parse_stations_dataclass(data_dict)

        elif "prices" in data_dict:
            return self._parse_station_price_dataclass(data_dict)

        elif "station" in data_dict:
            return self._parse_staion_detail(data_dict)

        else:
            msg_str = "API response status is ok, but response format is unknown.\n" + str(data)
            logger.info(msg_str)
            return data


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
        response= self._get_http_response(request_url)
        processed_response = self.post_process_response(response)
        return processed_response

    def get_price(self, ids):
        php_str = "prices.php"
        request_url = (self.base_url + "/" + php_str +
                       "?" + "ids=" + str(ids) +
                       "&" + "apikey=" + self.api_secret
                       )

        response = self._get_http_response(request_url)
        processed_response = self.post_process_response(response)
        return processed_response


def get_detail(self, ids):
        php_str = "detail.php"
        request_url = (self.base_url + "/" + php_str +
                       "?" + "ids=" + str(ids) +
                       "&" + "apikey=" + self.api_secret
                       )
        response = self._get_http_response(request_url)
        processed_response = self.post_process_response(response)
        return processed_response
