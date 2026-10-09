# Map Upgrade 2：行政区横向滑动选择器

本阶段在 Map Upgrade 1 的多级地图状态之上增加底部行政区导航，不改变 Flask API、MySQL 数据和现有天气业务接口。

## 组件与数据来源

- `RegionCarousel.vue` 读取 `ChinaMapChart` 当前层级的真实 GeoJSON `features`，因此全国、省级、地级和区县层级会自动显示对应子区域。
- `RegionThumbnail.vue` 使用 `Polygon` / `MultiPolygon` 几何转换为轻量 SVG path；缺少或不支持几何时明确显示“轮廓不可用”，不会补造轮廓。
- `src/utils/regionThumbnail.js` 对同一行政区和尺寸的路径计算做内存缓存，并支持清空缓存和测试缓存数量。
- 地图和卡片共用 `ChinaMapChart` 的 `navigation`、`selectedAdcode` 和请求版本保护，不在两个组件之间复制行政区状态。

## 交互约定

- 单击卡片只选中并触发现有 `area-select`，左右业务卡片会按当前固定日期重新读取真实记录。
- 双击卡片、键盘 Enter 或“进入区域 / 查看数据”按钮进入下一级；区县或 `childrenNum=0` 的末级区域不会请求不存在的下级地图。
- 中央地图点击保留 Map Upgrade 1 的直接钻取行为；面包屑仍可返回任意上级。
- 卡片支持箭头、横向滚轮、指针拖动，选中项会自动滚动到可视区域中间。
- GeoJSON 请求按 adcode 缓存，快速切换时使用请求版本号避免旧响应覆盖新地图。

## 验证

在 `weather_sys/font/weather_font` 目录执行：

```bash
npm run test:map
npm run build
```

测试覆盖行政区 GeoJSON 规范化、末级判定、Polygon/MultiPolygon SVG 路径、空几何提示和缓存复用。
