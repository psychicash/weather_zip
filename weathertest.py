import weather
import unittest
import re

#TESTS

class TestWeatherMethods(unittest.TestCase):

    def test_location(self):
        self.assertEqual(weather.get_location_info("10004"), ["40.7038704", "-74.0138541"])
        pass

    def test_station(self):
        self.assertEqual(weather.get_weather_station_info("40.7038704", "-74.0138541"), ['OKX', '32', '34'])

    def test_results(self):
        result = weather.get_weather_forecast('OKX', '32', '34')
        self.assertEqual(len(result), 3)
        try:
            self.assertEqual(result[2], 'F')
        except:
            self.assertEqual(result[2], 'C')
        temp_result = re.search(r'/d', result[1])
        self.assertFalse(temp_result, None)


if __name__ == '__main__':
    unittest.main()
    
