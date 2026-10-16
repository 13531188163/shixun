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
        self.assertEqual(normalize_province_name("内蒙古自治区"), "内蒙古")
        self.assertEqual(normalize_province_name("广西壮族自治区"), "广西")
        self.assertEqual(normalize_province_name("宁夏回族自治区"), "宁夏")
        self.assertEqual(normalize_province_name("新疆维吾尔自治区"), "新疆")
        self.assertEqual(normalize_province_name("西藏自治区"), "西藏")

    def test_unknown_values_are_preserved(self):
        self.assertEqual(normalize_city_name("锡林郭勒盟"), "锡林郭勒盟")
        self.assertEqual(normalize_province_name("自定义地区"), "自定义地区")
        self.assertIsNone(normalize_city_name(""))

    def test_query_aliases_include_raw_and_canonical_forms(self):
        self.assertEqual(city_query_values("北京市"), ("北京市", "北京"))
        self.assertEqual(province_query_values("广东"), ("广东", "广东省"))

    def test_aqi_city_aliases_match_weather_data_names(self):
        self.assertEqual(normalize_city_name("广安市"), "广安")
        self.assertIn("广安", city_query_values("广安市"))
        self.assertIn("阿坝藏族羌族自治州", city_query_values("阿坝"))
        self.assertIn("凉山彝族自治州", city_query_values("凉山"))

    def test_autonomous_region_query_aliases_include_full_name(self):
        self.assertEqual(province_query_values("内蒙古"), ("内蒙古", "内蒙古自治区"))
        self.assertEqual(province_query_values("宁夏"), ("宁夏", "宁夏回族自治区"))
        self.assertIn("广西壮族自治区", province_query_values("广西"))
        self.assertIn("新疆维吾尔自治区", province_query_values("新疆"))


if __name__ == "__main__":
    unittest.main()
