from dataclasses import dataclass

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
    diesel: float # Euros per liter
    e5: float # Euros per liter
    e10: float # Euros per liter

    @classmethod
    def from_api_dict(cls, json_dict: dict) -> "FuelPrice":
        return FuelPrice(
            diesel=json_dict["diesel"],
            e5=json_dict["e5"],
            e10=json_dict["e10"],
        )

@dataclass
class LiveInformation:
    isopen: bool # if fuel station is open at the time of query
    dist: float # disdtance from original queried location
    fuel_price: FuelPrice # live fuel prices at the time of query

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
    def list_from_dict(cls, json_dict: dict) -> list["FuelStationWithLiveData"]:
        return [cls.from_api_dict(station_dict) for station_dict in json_dict]
