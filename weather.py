import requests
import sys
import json
from jsontraverse.parser import JsonTraverseParser
from os.path import exists


def json_parser(response, *args: str) -> list:
    """
        Takes in a json formated get response and parses through it
        looking for the elements that match the argument location
        and then collects the values and returns an array with those
        values in the order the arguments were given

        Args:
            response (json dict or dict) : GET response either in
                json format or converted to json format in processing
            *args (str) : strings of dictionary keys in dot format

        Returns:
            List of values from the dictionary in the order the args
            were given.

        Raises:
            AttributeError: if GET response is already translated
                as a json object, simply moves it forward as such
            ValueError: if the dictionary is empty, none, or provides
                an empty value, will append as an empty string.
            AnyError: If anything bad happens.
    """
    return_arr = []

    try:
        data = response.json()
    except AttributeError:
        data = response
    json_string = json.dumps(data)
    parser = JsonTraverseParser(json_string)
    try:
        for arg in args:
            return_arr.append(str(parser.traverse(arg)))
    except ValueError:
        return_arr.append("")
    return return_arr


def get_key():
    key = ""
    try:
        with open("key.txt") as file:
            df = file.read()
            key = df
    except:
        pass

    return key


def get_location_info(zip_code: str) -> list:
    """
        Takes a zip code (US ONLY) and contacts google's geocoding
        API to get the location's latitude and longitude for that
        ZIP code. Code could be expanded to get lat/long for exact
        address but such precise measurements are not required.

        NOTE: Key is required to use this API, as the api is not 100%
        FREE, key is not provided here.

        Args:
            zip_code (str): Five digit zip code. If larger zip is given
                on command line, zip will be sliced down to five digits
                before passed here.

        Returns: A list of the latitude and longitutde

        Raises:
            AnyError: If anything bad happens.
    """
    key = get_key()

    if key == "":
        local = ("40.703", "-74.013")
    else:
        url = "https://google-maps-geocoding.p.rapidapi.com/geocode/json"
        querystring = {"address": str(zip_code), "language": "en"}

        headers = {
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": "google-maps-geocoding.p.rapidapi.com"
            }

        response = requests.request("GET", url,
                                    headers=headers, params=querystring)
        arg1 = "results.geometry.location.lat"
        arg2 = "results.geometry.location.lng"

        local = json_parser(response, arg1, arg2)

    return local


def get_weather_station_info(latitude, longitude) -> list:
    """
        get_weather_station_info takes in a latitude and longitude
        and contacts the governments weather api. This information is
        then processed and the weather station id as well as the grid
        designation (x and y) is also returned. There's a lot of other
        information returned but these are the only elements needed
        in order to get the current weather information

        Args:
            latitude (str): string of latitude
            longitude (str): string of longitude

        Returns: List of station Id, gridx designation, and gridy designation

        Raises:
            AnyError: If anything bad happens.
    """
    url = "https://api.weather.gov/points/{},{}".format(latitude, longitude)
    response = requests.request("GET", url)

    arg1 = "properties.gridId"
    arg2 = "properties.gridX"
    arg3 = "properties.gridY"

    re_value = json_parser(response, arg1, arg2, arg3)
    return re_value


def create_location(zip_code) -> dict:
    """
        In order to save transactions with the google api, values are
        saved in a local location.json file. If the location dict is
        empty, then a location must be created from the zip code.

        Args:
            zip_code (str): five digit zip code

        Returns:
            a dictionary called location with zip code, lat, long,
            weather_station_id, gridx, gridy

        Raises:
            AnyError: If anything bad happens.
    """

    local = get_location_info(zip_code)
    station_info = get_weather_station_info(local[0], local[1])

    location = {
      "location": {
        "zip_code": zip_code,
        "latitude": local[0],
        "longitude": local[1],
        "weather_station_id": station_info[0],
        "gridx": station_info[1],
        "gridy": station_info[2],
      }
    }
    return location


def process_location(file_path, zip_code):
    """
        Process_location takes a file path and a zip code. the file path is
        to the saved json file that holds the location information. the zip
        code is compared to the zip in the json. if they match, it uses the
        information in the dictionary. Each step is checked, if the zip
        matches but the station information is blank, it will fill those
        out using the lat/long. If those are balnk, it will retrieve those.
        If the file doesn't exist or the zip doesn't match, a new dictionary
        is created using the new dictionary.

        Args:
            file_path (str): string of file path to location.json file
            zip_code (str): five digit zip code

        Returns: returns list of weather station id, gridx and gridy

        Raises:
            AnyError: If anything bad happens.
    """
    arg1 = "location.zip_code"
    arg2 = "location.latitude"
    arg3 = "location.longitude"
    arg4 = "location.weather_station_id"
    arg5 = "location.gridx"
    arg6 = "location.gridy"

    with open(file_path, 'r+') as file:
        try:
            df = json.load(file)
            location_info = json_parser(df, arg1, arg2, arg3, arg4, arg5, arg6)
        except json.decoder.JSONDecodeError:
            location_info = [zip_code, "", "", "", "", ""]

        location = {
          "location": {
            "zip_code": location_info[0],
            "latitude": location_info[1],
            "longitude": location_info[2],
            "weather_station_id": location_info[3],
            "gridx": location_info[4],
            "gridy": location_info[5],
          }
        }
        if location_info[0] == zip_code:
            pass
        else:
            location = create_location(zip_code)

        lt = location["location"]["latitude"]
        lg = location["location"]["longitude"]
        wid = location["location"]["weather_station_id"]
        gx = location["location"]["gridx"]
        gy = location["location"]["gridy"]

        if wid == "None" or gx == "None" or gy == "None":
            local = get_location_info(zip_code)
            location["location"]["latitude"] = local[0]
            location["location"]["longitude"] = local[1]
            station_info = get_weather_station_info(local[0], local[1])
            wid = station_info[0]
            gx = station_info[1]
            gy = station_info[2]

        file.seek(0)
        file.truncate(0)
        json.dump(location, file, indent=4)
        return wid, gx, gy


def get_weather_forecast(office_name, grid_x, grid_y):
    """
        Sends request to the government weather API to get current
        weather conditions for the zip code given on command line.
        That zip was turned into weather station information. That
        weather station info is passed to this function and sent
        to the government's weather API. It returns a forecast for
        the next few days as well as current weather conditons.
        The current weather conditions are extracted and returned
        in a list.

        Args:
            office_name (str): string of the weather_station_id
            grid_x (str): string of the grid_x number for the
                weather_station
            grid_y (str): string of the grid_y number for the
                weather_station

        Returns:
            list of weather conditions currently (Weather condition,
            temperature value, temperature measurement unit (F or C))

        Raises:
            AnyError: If anything bad happens.
    """

    url = "https://api.weather.gov/gridpoints/{}/{},{}/forecast".format(office_name, grid_x, grid_y)

    response = requests.request("GET", url)
    arg1 = "properties.periods.0.shortForecast"
    arg2 = "properties.periods.0.temperature"
    arg3 = "properties.periods.0.temperatureUnit"


    forecast = json_parser(response, arg1, arg2, arg3)
    
    if forecast == ['None', 'None', 'None']:
        forecast = ["No response from server, default values", "72", "F"]
    return forecast


def main(*args):
    """
        Takes in a zip code and processes it through different API's
        in order to get the current weather conditions for that zip
        code. If no zip is given, the zip 10004 is used. This is the
        zip code for the statue of liberty. The zip code and it's
        processed values are saved in a local json file for future use
        in order to improve processing time for values that do not change.

        if more arguments are provided than the zip code, they are
        disregarded.

        API's used:
            Google Geocoder
            US GOVT Weather API (station information and weather forecast)

        Args:
            *args: command line arguments given for processing.

            expected
                zip code: Only a zip code will be accepted. if it
                is not a valid uses zip code 10004 by default.

        Raises:
            IndexError: raises if zip code is not provided and instead
                substitutes default zip code value
            FileNotFoundError: raises if location.json doesn't exsist
                if no file found, one is created
            AnyError: If anything bad happens.
    """
    try:
        zip_code = args[0][1]
        zip_code = zip_code[:5]
        if zip_code.isnumeric():
            pass
        else:
            zip_code = '10004'
    except IndexError:
        zip_code = '10004'

    try:
        query_data = process_location('location.json', zip_code)
    except FileNotFoundError:
        fp = open('location.json', 'x')
        fp.close()
        query_data = process_location('location.json', zip_code)

    station_id = query_data[0]
    gridx = query_data[1]
    gridy = query_data[2]
    wfore = get_weather_forecast(station_id, gridx, gridy)

    print("Weather is {} based on zip code {}.".format(wfore, zip_code))



if __name__ == '__main__':
    main(sys.argv)
