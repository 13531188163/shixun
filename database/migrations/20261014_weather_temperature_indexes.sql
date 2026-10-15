-- Temperature and rainfall analysis performance migration.
-- Apply once after importing database/weather_data.sql into weather_db.
-- The source dump remains read-only; this migration only adds lookup indexes.

ALTER TABLE weather_data
    ADD INDEX idx_weather_data_date (date),
    ADD INDEX idx_weather_data_location_date (province, city, district, date);
