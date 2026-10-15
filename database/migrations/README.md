# Weather data migrations

The SQL dump is a read-only source asset. Apply migrations separately after
the dump has been imported into `weather_db`.

```bash
mysql -u root -p weather_db < database/migrations/20261014_weather_temperature_indexes.sql
```

`20261014_weather_temperature_indexes.sql` adds a date index and a
province/city/district/date index. The temperature and rainfall trend,
recent-data, and date-list queries use these indexes to locate bounded
observed dates before aggregating rows.
