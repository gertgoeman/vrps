import googlemaps
import logging
import collections
import utils
import requests
import json

logger = logging.getLogger()

LatLng = collections.namedtuple("LatLng", ["latitude", "longitude"])
DistTime = collections.namedtuple("DistTime", ["distance", "time"])

class DistanceTimeMatrix(object):
    def __init__(self, row_keys, col_keys):
        self.__row_keys = row_keys
        self.__col_keys = col_keys
        self.__matrix = [ [ None for i in range(len(row_keys)) ] for j in range(len(col_keys)) ]

    def add_matrix(self, row_keys, col_keys, matrix):
        for row_idx, row in enumerate(matrix):
            for col_idx, value in enumerate(row):
                row_key = row_keys[row_idx]
                col_key = col_keys[col_idx]

                if row_key not in self.__row_keys:
                    raise ValueError("Invalid row key '{0}'.".format(row_key))

                if col_key not in self.__col_keys:
                    raise ValueError("Invalid column key '{0}'.".format(col_key))

                actual_row_idx = self.__row_keys.index(row_key)
                actual_col_idx = self.__col_keys.index(col_key)

                self.__matrix[actual_row_idx][actual_col_idx] = value

    def get_entry(self, from_key, to_key):
        if from_key not in self.__row_keys: return None
        if to_key not in self.__col_keys: return None

        row_idx = self.__row_keys.index(from_key)
        col_idx = self.__col_keys.index(to_key)

        return self.__matrix[row_idx][col_idx]

    def __str__(self):
        return str(self.__matrix)

geocode_cache = {}
matrix_cache = {}

class GeoHelper(object):
    def __init__(self, google_api_key, bing_api_key):
        self.__gmaps = googlemaps.Client(key = google_api_key)
        self.__bing_api_key = bing_api_key

    def geocode(self, address):
        logger.info("Getting coordinates for address '{0}'".format(address))

        # If the coordinates have already been calculated, return them from cache.
        if address in geocode_cache:
            return geocode_cache[address]

        geo = self.__gmaps.geocode(address)

        if len(geo) == 0 or (not "geometry" in geo[0]) or (not "location" in geo[0]["geometry"]):
            raise ValueError("Unable to get coordinates for '{0}'. Please verify the address.".format(address))

        result = LatLng(
            geo[0]["geometry"]["location"]["lat"],
            geo[0]["geometry"]["location"]["lng"])

        # Update the cache
        geocode_cache[address] = result

        return result

    def __get_bing_distance_matrix(self, origins, destinations):
        # If the matrix has already been calculated, return it from cache.
        key_origin = ":".join([str(coord) for coord in origins])       
        key_dest = ":".join([str(coord) for coord in destinations])
        cache_key = key_origin + "-" + key_dest

        if cache_key in matrix_cache:
            return matrix_cache[cache_key]

        body = {
            "origins": [],
            "destinations": [],
            "travelMode": "driving",
            "timeUnit": "second",
            "distanceUnit": "km"
        }

        for coordinate in origins:
            obj = {
                "latitude": coordinate.latitude,
                "longitude": coordinate.longitude
            }

            body["origins"].append(obj)

        for coordinate in destinations:
            obj = {
                "latitude": coordinate.latitude,
                "longitude": coordinate.longitude
            }

            body["destinations"].append(obj)

        url = "https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix?key={0}".format(self.__bing_api_key)

        response = requests.post(url, data = json.dumps(body), headers = { "Content-Type": "application/json"})
        response.raise_for_status()
        response_json = response.json()

        results = response_json["resourceSets"][0]["resources"][0]["results"]

        matrix = [ [ 0 for i in range(len(destinations)) ] for j in range(len(origins)) ]

        for result in results:
            origin_idx = int(result["originIndex"])
            dest_idx = int(result["destinationIndex"])
            distance = float(result["travelDistance"]) if "travelDistance" in result else float(0)
            duration = int(result["travelDuration"]) if "travelDuration" in result else int(0)

            matrix[origin_idx][dest_idx] = DistTime(distance, duration)

        # Update the cache
        matrix_cache[cache_key] = matrix

        return matrix


    def calculate_distance_time_matrix(self, coordinates):
        logger.info("Calculating time and distance between locations.")

        # Split in batches of 20
        batches = list(utils.split_in_batches(coordinates, 20))

        result = DistanceTimeMatrix(coordinates, coordinates)

        for i, batch in enumerate(batches):
            for j, other_batch in enumerate(batches):
                logger.info("batch: {0}, {1}".format(i, j))

                matrix = self.__get_bing_distance_matrix(batch, other_batch)
                result.add_matrix(batch, other_batch, matrix)

        return result
