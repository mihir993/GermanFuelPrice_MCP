import pytest
import json

from core.tools.fuel_station_dataclass import FuelStationWithLiveData, FuelStation, FuelPrice,LiveInformation, PriceStationId


@pytest.fixture
def single_fuel_station_dict():
    return """{
    "id": "474e5046-deaf-4f9b-9a32-9797b778f047",
    "name": "TOTAL BERLIN",
    "brand": "TOTAL",
    "street": "MARGARETE-SOMMER-STR.",
    "place": "BERLIN",
    "lat": 52.53083,
    "lng": 13.440946,
    "dist": 1.1,
    "diesel": 1.109,
    "e5": 1.339,
    "e10": 1.319,
    "isOpen": true,
    "houseNumber": "2",
    "postCode": 10407
    }"""

@pytest.fixture
def tankerkoenig_api_response():
    return """
    {
    "ok": true,
    "license": "CC BY 4.0 -  https:\/\/creativecommons.tankerkoenig.de",
    "data": "MTS-K",
    "status": "ok",
    "stations": [
        {
            "id": "474e5046-deaf-4f9b-9a32-9797b778f047",
            "name": "TOTAL BERLIN",
            "brand": "TOTAL",
            "street": "MARGARETE-SOMMER-STR.",
            "place": "BERLIN",
            "lat": 52.53083,
            "lng": 13.440946,
            "dist": 1.1,
            "diesel": 1.109,
            "e5": 1.339,
            "e10": 1.319,
            "isOpen": true,
            "houseNumber": "2",
            "postCode": 10407
        },
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "ARAL MÜNCHEN",
            "brand": "ARAL",
            "street": "LEOPOLDSTR.",
            "place": "MÜNCHEN",
            "lat": 48.159721,
            "lng": 11.586089,
            "dist": 2.4,
            "diesel": 1.679,
            "e5": 1.839,
            "e10": 1.819,
            "isOpen": true,
            "houseNumber": "45",
            "postCode": 80802
        },
        {
            "id": "987fcdeb-51a2-43d1-9f12-abcdef123456",
            "name": "SHELL HAMBURG",
            "brand": "SHELL",
            "street": "REEPERBAHN",
            "place": "HAMBURG",
            "lat": 53.549999,
            "lng": 9.966667,
            "dist": 0.8,
            "diesel": 1.659,
            "e5": 1.829,
            "e10": 1.809,
            "isOpen": false,
            "houseNumber": "120",
            "postCode": 20359
        }
    ]
}
    """

@pytest.fixture
def prices_response():
    return """
    {
    "ok": true,
    "license": "CC BY 4.0 -  https:\/\/creativecommons.tankerkoenig.de",
    "data": "MTS-K",
    "prices": {
        "60c0eefa-d2a8-4f5c-82cc-b5244ecae955": {
            "status": "open",
            "e5": false,
            "e10": false,
            "diesel": 1.189
        },
        "446bdcf5-9f75-47fc-9cfa-2c3d6fda1c3b": {
            "status": "closed"
        },
        "4429a7d9-fb2d-4c29-8cfe-2ca90323f9f8": {
            "status": "open",
            "e5": 1.409,
            "e10": 1.389,
            "diesel": 1.129
        },
        "44444444-4444-4444-4444-444444444444": {
            "status": "no prices"
            }
        }
    }
    """

class TestFuelStation:

    def test_fuel_station(self, single_fuel_station_dict):
        json_dict = json.loads(single_fuel_station_dict)
        fuelstation = FuelStation.from_api_dict(json_dict)
        assert fuelstation.name == "TOTAL BERLIN"
        assert fuelstation.brand == "TOTAL"
        assert fuelstation.postcode == 10407
        assert fuelstation.housenumber == "2"

class TestFuelPrice:
    def test_fuel_price(self, single_fuel_station_dict):
        json_dict = json.loads(single_fuel_station_dict)
        fuel_price = FuelPrice.from_api_dict(json_dict)
        assert fuel_price.diesel == 1.109
        assert fuel_price.e5 == 1.339
        assert fuel_price.e10 == 1.319

class TestLiveInformation:
    def test_live_information(self, single_fuel_station_dict):
        json_dict = json.loads(single_fuel_station_dict)
        live_information = LiveInformation.from_api_dict(json_dict)
        assert live_information.isopen == True
        assert live_information.dist == 1.1
        assert live_information.fuel_price.diesel == 1.109
        assert live_information.fuel_price.e5 == 1.339
        assert live_information.fuel_price.e10 == 1.319

class TestFuelStationWithLiveData:
    def test_fuel_station_live_data(self, single_fuel_station_dict):
        json_dict = json.loads(single_fuel_station_dict)
        station_live_data = FuelStationWithLiveData.from_api_dict(json_dict)

        assert station_live_data.fuelstation.name == "TOTAL BERLIN"
        assert station_live_data.fuelstation.postcode == 10407
        assert station_live_data.livedata.isopen == True
        assert station_live_data.livedata.fuel_price.diesel == 1.109

    def test_tankerkoening_api_response_to_list_stations(self,tankerkoenig_api_response):
        json_dict = json.loads(tankerkoenig_api_response)
        stations_list_dict = json_dict["stations"]
        stations_list = FuelStationWithLiveData.list_from_dict(stations_list_dict)

        assert len(stations_list) == 3
        assert stations_list[0].fuelstation.id == "474e5046-deaf-4f9b-9a32-9797b778f047"
        assert stations_list[1].fuelstation.id == "123e4567-e89b-12d3-a456-426614174000"
        assert stations_list[2].fuelstation.id == "987fcdeb-51a2-43d1-9f12-abcdef123456"

    def test_timestampt_is_added_to_livedata(self, tankerkoenig_api_response):
        json_dict = json.loads(tankerkoenig_api_response)
        stations_list_dict = json_dict["stations"]
        expected_timestamp = 12345678.65
        stations_list = FuelStationWithLiveData.list_from_dict(stations_list_dict, expected_timestamp)

        assert stations_list[0].livedata.timestamp == expected_timestamp
        assert stations_list[1].livedata.timestamp == expected_timestamp
        assert stations_list[2].livedata.timestamp == expected_timestamp


class TestPricesAPIData:

    def test_prices_api_response(self, prices_response):
        json_dict = json.loads(prices_response)
        prices_list_dict = json_dict["prices"]
        prices_obj_list = PriceStationId.from_api_dict(prices_list_dict)

        assert prices_obj_list[0].fuel_station_id == "60c0eefa-d2a8-4f5c-82cc-b5244ecae955"
        assert prices_obj_list[1].fuel_station_id == "446bdcf5-9f75-47fc-9cfa-2c3d6fda1c3b"
        assert prices_obj_list[2].fuel_station_id == "4429a7d9-fb2d-4c29-8cfe-2ca90323f9f8"

        assert prices_obj_list[0].fuel_price.diesel == 1.189
        assert prices_obj_list[0].fuel_price.e5 == None
        assert prices_obj_list[0].fuel_price.e10 == None