from dataclasses import dataclass
from enum import Enum
import numbers

def is_numeric(value):
    return isinstance(value, numbers.Number) and not isinstance(value, bool)

@dataclass
class FuelStation:
    id: str # UUID if the fuel station
    name: str
    brand: str
    street: str
    housenumber: str
    place: str
    postcode: int
    lat: float # geographical latitude
    lng: float # geographical longitude

    @classmethod
    def from_api_dict(cls, json_dict: dict) -> "FuelStation":
        return FuelStation(
            json_dict["id"],
            json_dict["name"],
            json_dict["brand"],
            json_dict["street"],
            json_dict["houseNumber"],
            json_dict["place"],
            json_dict["postCode"],
            json_dict["lat"],
            json_dict["lng"],
        )

@dataclass
class FuelPrice:
    diesel: float | None # Euros per liter
    e5: float | None # Euros per liter
    e10: float | None # Euros per liter

    @classmethod
    def from_api_dict(cls, json_dict: dict) -> "FuelPrice":
        return FuelPrice(
            diesel=json_dict["diesel"] if is_numeric(json_dict["diesel"]) else None,
            e5=json_dict["e5"] if is_numeric(json_dict["e5"]) else None,
            e10=json_dict["e10"] if is_numeric(json_dict["e10"]) else None,
        )

@dataclass
class LiveInformation:
    isopen: bool # if fuel station is open at the time of query
    dist: float # disdtance from original queried location
    fuel_price: FuelPrice # live fuel prices at the time of query
    timestamp: float = 0.0

    @classmethod
    def from_api_dict(cls, json_dict: dict) -> "LiveInformation":
        fuel_price = FuelPrice.from_api_dict(json_dict)
        return LiveInformation(
            isopen=json_dict["isOpen"],
            dist=json_dict["dist"],
            fuel_price=fuel_price
        )

@dataclass
class FuelStationWithLiveData:
    fuelstation: FuelStation
    livedata: LiveInformation

    @classmethod
    def from_api_dict(cls, json_dict: str) -> "FuelStationWithLiveData":
        live_data = LiveInformation.from_api_dict(json_dict)
        station_detail = FuelStation.from_api_dict(json_dict)
        return FuelStationWithLiveData(
            fuelstation=station_detail,
            livedata=live_data
        )

    @classmethod
    def list_from_dict(cls, json_dict: dict, timestamp: float | None = None) -> list["FuelStationWithLiveData"]:

        output_list = []
        for station_dict in json_dict:
            station_object = cls.from_api_dict(station_dict)
            station_object.livedata.timestamp = timestamp
            output_list.append(station_object)
        return output_list


class StationOpenStatus(Enum):
    Closed = 0
    Open = 1
    NoPrice = 2

@dataclass
class PriceStationId:
    fuel_station_id: str # UUID of the staion id
    status: StationOpenStatus # station status (open|closed|unknown) at the time of query.
    fuel_price: FuelPrice  # live fuel prices at the time of query

    @classmethod
    def from_api_dict(cls, json_dict: str) -> list["PriceStationId"]:
        output_list = list()
        for key, value in json_dict.items():
            if value["status"] == "open":
                fuel_price = FuelPrice.from_api_dict(value)
            else:
                fuel_price = FuelPrice(None, None, None)
            obj = PriceStationId(
                fuel_station_id = key,
                status = value["status"],
                fuel_price = fuel_price
            )
            output_list.append(obj)
        return output_list
