import pytest
from src.core.tankerkoenig_gateway.tk_connector import TankerkoenigConnector
from dotenv import load_dotenv


class TestTKConnector:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.mock_test_env(mocker)
        self.connector = TankerkoenigConnector()

    def mock_test_env(self, mocker):
        mocker.patch.object(TankerkoenigConnector, "load_env", side_effect=lambda:load_dotenv("test/.env.test"))

    def test_apikey_is_str(self, mocker):
        print("api key for you.\n", self.connector.api_secret)
        assert isinstance(self.connector.api_secret, str)

    def test_base_url_is_str(self):
        print("\n", self.connector.base_url)
        assert isinstance(self.connector.base_url, str)

    def test_get_nearby_station(self):
        response = self.connector.get_nearby_stations(lat=52.521, lng=13.438, rad=2)
        assert(response.status_code == 200)
        print(response.json())

     