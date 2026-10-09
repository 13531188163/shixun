# Map Upgrade 1：多级行政区地图钻取

## 范围

本次升级只处理行政区边界钻取和选中高亮，不新增天气业务字段，也不把地图边界当作天气数据来源。

地图层级为：全国（省级边界）→省（地市/自治州/地区边界）→地级行政区（区县边界）→区县末级选择。
点击末级区县后，Dashboard 才会使用该区县名称请求现有天气接口；数据库没有对应记录时显示明确提示。

## 边界数据与编码

- 全国资源：`public/maps/china.json`。
- 省、市级资源：DataV GeoAtlas `areas_v3` GeoJSON 接口：
  `https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json`。
- `adcode`、`level`、`parent.adcode`、`childrenNum` 均来自 GeoJSON，不在前端生成。
- 直辖市的省级资源直接返回区县；海南、新疆等省直辖县级单位按资源的 `level/childrenNum` 识别为末级，不假设存在虚构的中间层。

## 前端实现

- `src/utils/administrativeMap.js` 负责资源格式校验、按需加载和 Promise 缓存。
- `ChinaMapChart.vue` 复用一个 ECharts 实例，动态注册不同 `adcode` 的地图，面包屑可返回任意已访问上级。
- 切换资源时保留当前图表和业务面板，只显示局部加载提示，避免整页闪烁。
- 悬浮区域使用青蓝高亮，当前选中区域使用金色发光边框。

## 已知边界

GeoAtlas 边界资源最低到区县级；乡镇/街道不在本阶段范围内。空气质量仍按现有数据库快照契约处理，不会因为选择天气日期而伪造随日期变化的 AQI。
