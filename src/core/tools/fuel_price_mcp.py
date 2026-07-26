from core.tools.server import mcp
from core.tankerkoenig_gateway.tk_connector import TankerkoenigConnector

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
    connector = TankerkoenigConnector()
    response = connector.get_nearby_stations(lng, lat, rad, type, sort)
    assert response.status_code == 200, "Something is wrong with the response."
    return response.json()

@mcp.tool()
def get_fuel_price_from_station_ids(station_ids):
    """
    This function returns live fuel prices at the given station ids.
    :param station_ids: list of station ids 
    :return: live fuel prices
    """
    connector = TankerkoenigConnector()
    return connector.get_price(station_ids)

@mcp.tool()
def fuel_station_detail(station_ids):
    """
    This function returns details of fuel stations at the given station ids.
    :param station_ids: list of station ids
    :return: Fuel station details
    """
    connector = TankerkoenigConnector()
    return connector.get_detail(station_ids)