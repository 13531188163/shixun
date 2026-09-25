import unittest
from datetime import date, datetime

from weather_sys.backend.utils.data_converter import (
    format_date,
    parse_aqi,
    parse_numeric_value,
    parse_precipitation,
    parse_temperature,
    parse_wind_speed,
)


class DataConverterTests(unittest.TestCase):
    def test_measurements_and_units(self):
        self.assertEqual(parse_temperature("18.6℃"), 18.6)
        self.assertEqual(parse_temperature("-2 °C"), -2)
        self.assertEqual(parse_wind_speed("3.5 m/s"), 3.5)
        self.assertEqual(parse_precipitation("12毫米"), 12)
        self.assertEqual(parse_aqi("62"), 62)
        self.assertEqual(parse_numeric_value("3.2m/s"), 3.2)

    def test_invalid_values_are_none(self):
        for parser in (parse_numeric_value, parse_temperature, parse_wind_speed, parse_precipitation, parse_aqi):
            self.assertIsNone(parser(None))
            self.assertIsNone(parser("--"))
            self.assertIsNone(parser("N/A"))
            self.assertIsNone(parser("unknown"))
        self.assertIsNone(parse_aqi("62.5"))

    def test_dates(self):
        self.assertEqual(format_date("2026/03/01"), "2026-03-01")
        self.assertEqual(format_date(datetime(2026, 3, 1, 8, 30)), "2026-03-01")
        self.assertEqual(format_date(date(2026, 3, 1)), "2026-03-01")
        self.assertIsNone(format_date("not-a-date"))


if __name__ == "__main__":
    unittest.main()
