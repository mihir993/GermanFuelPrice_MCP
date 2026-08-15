from core.tools.server import mcp
from core.tankerkoenig_gateway.tk_connector import TankerkoenigConnector
from cache_fuel_price import FuelPriceCache, build_list_key, PRICE_TTL_SECONDS


class GermanFuelPriceMcp:
    def __init__(self):
        self.cache = FuelPriceCache()
        self.tk_connector = TankerkoenigConnector()

    def _fetch_fuel_prices_nearby(self, lat, lng):
        """
        This function always fetches all the fuel stations in 25km radius and prices for all the fuel types.
        :param lat: latitude
        :param lng: longitude
        :return:
        """
        return self.tk_connector.get_nearby_stations(lat= lat, lng=lng)

    def _filter_nearby_stations(self, data, rad, type, sort):
        # Post-filter: the cached bucket may cover a larger radius than asked.
        stations = [s for s in data["stations"] if s["dist"] <= rad]
        # stations = stations[type] # filter only for fuel type
        stations.sort(key=(lambda s: s["dist"]) if sort == "dist" else (lambda s: s[type]))
        return stations

    def find_fuel_station_nearby(self, lat, lng, rad, type, sort):
        """
        Function to find the fuel station near given location.
        :param lat: latitude
        :param lng: lonitude
        :param rad: radius of search area
        :param type: type of the fuel 'e5', 'e10', 'diesel' or 'all'
        :param sort: sort by distance or price. 'price' or 'dist'
        :return:
        """
        max_radius = 25
        cache_key = build_list_key(lat, lng, max_radius)
        # TODO: Convert the json string to fuel station dataclass.
        data, stale = self.cache.get_or_fetch(cache_key,
                                fetch_fn=lambda: self._fetch_fuel_prices_nearby(lat, lng),
                                ttl_seconds=PRICE_TTL_SECONDS
                                )
        stations = self._filter_nearby_stations(data, rad, type, sort)
        if stale:
            for s in stations:
                s["_note"] = "served from cache, refresh rate-limited"
        return stations

    def get_fuel_price_for_station_id(self, ids):


fuelprice_mcp = GermanFuelPriceMcp()

@mcp.tool()
def find_fuel_stations_near_location(lng, lat, rad=25, type = "all", sort="dist"):
    """
    This function finds all the fuel stations near the given location in given radius of area.
    The result includes the list of fuel stations.
    It includes the details of each fuel station like: station id, name, brand, distance, address street house number postalcode, live price of different fuels.
    It can either sort the results by distance or price.
    To sort the results by price, specific fuel type must be given.
    :param lng: longitude
    :param lat: latitude
    :param rad: radius of search area
    :param type: type of the fuel 'e5', 'e10', 'diesel' or 'all'
    :param sort: sort by distance or price. 'price' or 'dist'
    :return: list of fuel stations
    """
    return fuelprice_mcp.find_fuel_station_nearby(lng, lat, rad, type, sort)
    # TODO: Clean up unused code.
    # connector = TankerkoenigConnector()
    # response = connector.get_nearby_stations(lng, lat, rad, type, sort)
    # assert response.status_code == 200, "Something is wrong with the response."
    # return response.json()

@mcp.tool()
def get_fuel_price_from_station_ids(station_ids):
    """
    This function returns live fuel prices at the given station ids.
    :param station_ids: list of station ids 
    :return: live fuel prices
    """
    # TODO: Cache output data.
    connector = TankerkoenigConnector()
    return connector.get_price(station_ids)

@mcp.tool()
def fuel_station_detail(station_ids):
    """
    This function returns details of fuel stations at the given station ids.
    :param station_ids: list of station ids
    :return: Fuel station details
    """
    # TODO: Cache output data.
    connector = TankerkoenigConnector()
    return connector.get_detail(station_ids)