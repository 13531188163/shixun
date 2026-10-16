# 地图资源说明

`china.json` 是公开的中国行政区 GeoJSON 边界资源，仅用于前端地图轮廓和当前省份高亮，不包含天气、AQI 或城市坐标业务数据。

来源：<https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json>

地图钻取时，前端使用同一数据源按 `adcode` 按需请求省级和地市级边界，
例如 `370000_full.json` 返回山东省地市边界，`370500_full.json` 返回东营市区县边界。
资源只包含行政区轮廓和官方行政区元数据，不包含天气、空气质量或坐标业务数据；
请求结果在当前页面生命周期内缓存，资源不可用时页面会保留当前地图并显示明确错误。

## 台湾省边界适配

DataV 的 `710000_full.json` 不提供台湾省下级边界，且全国资源将台湾省标为
`childrenNum=0`。项目因此单独随前端发布 `taiwan-towns.topo.json`，并在运行时
转换为 ECharts GeoJSON：

- `counties` 对象提供 22 个县市边界；`COUNTYCODE`（5 位）作为县市编码。
- `towns` 对象提供 368 个乡镇市区边界；`TOWNCODE`（8 位）作为区县编码，
  通过原始 `COUNTYCODE` 建立父子关系。
- 编码和原始名称不拼接 `710000`，天气数据库没有台湾记录时，页面只展示真实
  地图并明确显示暂无天气/AQI 数据。

资源来自 [`taiwan-atlas`](https://github.com/dkaoster/taiwan-atlas) 的 MIT 分发
文件，项目说明其边界源自台湾内政部/NLSC 与 data.gov.tw 开放资料；县市边界
资料集及 Open Government Data License 说明见
<https://data.gov.tw/en/datasets/7442>。转换逻辑位于
`src/utils/taiwanAdministrative.js`，不会修改原始数据库。

当前随仓库保存的资源 SHA-256：
`250f63cdef76679b67d2a34633a69355c8f1180ae6b55407e6c87789940feab0`。
