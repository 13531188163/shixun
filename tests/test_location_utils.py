import unittest

from weather_sys.backend.utils.location_utils import (
    city_query_values,
    normalize_city_name,
    normalize_province_name,
    province_query_values,
)


class LocationUtilsTests(unittest.TestCase):
    def test_explicit_city_mappings(self):
        self.assertEqual(normalize_city_name("北京市"), "北京")
        self.assertEqual(normalize_city_name("上海市"), "上海")
        self.assertEqual(normalize_city_name("  广州市 "), "广州")

    def test_explicit_province_mappings(self):
        self.assertEqual(normalize_province_name("广东省"), "广东")
        self.assertEqual(normalize_province_name("浙江省"), "浙江")
        self.assertEqual(normalize_province_name("重庆市"), "重庆")

    def test_unknown_values_are_preserved(self):
        self.assertEqual(normalize_city_name("锡林郭勒盟"), "锡林郭勒盟")
        self.assertEqual(normalize_province_name("自定义地区"), "自定义地区")
        self.assertIsNone(normalize_city_name(""))

    def test_query_aliases_include_raw_and_canonical_forms(self):
        self.assertEqual(city_query_values("北京市"), ("北京市", "北京"))
        self.assertEqual(province_query_values("广东"), ("广东", "广东省"))


if __name__ == "__main__":
    unittest.main()
