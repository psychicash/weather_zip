import requests
import sys
import json
from jsontraverse.parser import JsonTraverseParser
from os.path import exists


def json_parser(response, *args):
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


def get_location_info(zip_code):
    # contacts google to convert zip_code to lat/long
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
                                    headers=headers,
                                    params=querystring)
        arg1 = "results.geometry.location.lat"
        arg2 = "results.geometry.location.lng"
        local = json_parser(response, arg1, arg2)

    return local


def get_weather_station_info(latitude, longitude):
    url = "https://api.weather.gov/points/{},{}".format(latitude, longitude)
    response = requests.request("GET", url)

    arg1 = "properties.gridId"
    arg2 = "properties.gridX"
    arg3 = "properties.gridY"

    re_value = json_parser(response, arg1, arg2, arg3)
    return re_value


def create_location(zip_code):
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

        if ((wid == "") or (gx == "") or (gy == "")):
            local = get_location_info(zip_code)
            location["location"]["latitude"] = local[0]
            location["location"]["longitude"] = local[1]
            station_info = get_weather_station_info(local[0], local[1])
            wid = station_info[0]
            gx = station_info[1]
            gy = station_info[2]

        json.dump(location, file, indent=4)
        return wid, gx, gy


def get_weather_forecast(office_name, grid_x, grid_y):
    url = "https://api.weather.gov/gridpoints/{}/{},{}/forecast".format(office_name, grid_x, grid_y)
    response = requests.request("GET", url)
    arg1 = "properties.periods.0.shortForecast"
    arg2 = "properties.periods.0.temperature"
    arg3 = "properties.periods.0.temperatureUnit"
    forecast = json_parser(response, arg1, arg2, arg3)
    return forecast


def main(arguments):
    try:
        zip_code = arguments[1]
    except IndexError:
        # if no zip_code given use statue of liberty zip code
        zip_code = "10004"

    try:
        query_data = process_location("location.json", zip_code)
    except FileNotFoundError:
        fp = open("location.json", 'x')
        fp.close()

        query_data = process_location("location.json", zip_code)

    station_id = query_data[0]
    gridx = query_data[1]
    gridy = query_data[2]

    print(get_weather_forecast(station_id, gridx, gridy))


if __name__ == "__main__":
    main(sys.argv)
