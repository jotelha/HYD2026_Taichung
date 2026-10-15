# HYD2026_Taichung

Research data and maps for the former Taichung City and the Shuinan Economic and Trade Park, prepared for #HackYourDistrict 2026.

Live site (GitHub Pages): https://yunching0513.github.io/HYD2026_Taichung/

*中文說明在英文之後（[跳到中文](#中文說明)）。*

## Outputs

### Former Taichung City Base Map (`map/index.html`)

The interface is English-first, with Chinese as the secondary language: map labels, legend and side panels are in English, and village, district, zone, project and road names carry their Chinese names. The village search accepts English or Chinese.

- The 8 districts and 214 villages of the former Taichung City on an English-labelled basemap (OpenStreetMap data); the 5 old-downtown districts (Central, East, South, West, North) carry a darker tint and a merged outline, Xitun, Nantun and Beitun a lighter one
- Two styles and three tones from the switches in the header, remembered in the browser and shared with the landing page:
  - **Deck**: the monochrome look of the HYD Healthy City Workshop deck (Instrument Serif, warm greys, 2px ink rules)
  - **Program**: after the HYD Taichung program page (Bricolage Grotesque and IBM Plex, navy ink on cool grey, sun-yellow highlights for the old downtown, project markers and charts, rounded cards)
  - **Light**, **White** or **Dark** for either style; until one is chosen, light or dark follows the system setting
- Pan by dragging, zoom with the wheel or a pinch; arrow keys pan, `+` / `-` zoom, `0` shows the full extent
- Hover a village for its name and area; click or search to see its area, share of the district, area rank and village code
- Road network from OpenStreetMap, with English and Chinese road names along the arterials
- The Shuinan detailed plan, traced from Figure 7-1 and fitted to the road network
- Numbered markers for the major projects, with their mapped footprints and sources
- Coordinate ticks on the neatline, scale bar and north arrow
- Side panels: land-use areas of the Shuinan Airport site detailed plan (2024) and the status of major projects (2026)

The landing page (`index.html`) introduces the map and lists every data file for download.

### Detailed plan overlay

`data/raw/Figure_7-1_Detailed_Plan_A3_English_CAD.dxf` is a trace drawn on an A3 sheet in millimetres and has no coordinate reference; its `$LATITUDE` / `$LONGITUDE` header values (37.795, -122.394) are AutoCAD's San Francisco defaults. `scripts/georef_plan.py` places it on WGS84 with a similarity transform whose parameters come from fitting the traced blocks to OpenStreetMap road centrelines (`scripts/register_plan.py`):

| Parameter | Value | Basis |
|---|---|---|
| Scale | 12.52 m per drawing mm (about 1:12,500) | Road-network fit; matches the 12.24–12.87 m/mm derived from the zone areas |
| Rotation | 0.4° (almost exactly north-up) | Road-network fit; matches runway 18/36 of the former airport (175°–355°) |
| Translation | (-1927.9, -1848.6) m | Road-network fit (local plane origin 120.654°E, 24.185°N) |

The fit asks block edges to sit half a street from a road and keeps roads out of the blocks. Afterwards the median distance from a block edge to the nearest road is 11 m and 3% of block interiors touch a road (26 m and 12% before), so expect errors of a few tens of metres. Two independent checks agree: the Green Museumbrary grounds mapped in OpenStreetMap fall within about 55 m of the north end of the traced Central Park, and the OSM footprint of the dome site lines up with the traced Innovation R&D blocks.

The first estimate, built only from a Wikipedia coordinate for the Museumbrary and a guessed no-fly-zone centre, sat about 210 m too far west; the Wikipedia infobox point turned out to lie about 210 m west of the mapped grounds.

**Adjust position** in the map's side panel still lets you move, rotate and scale the overlay; **Copy parameters** outputs `SCALE`, `ROTATION_DEG` and `TRANSLATION_M` for `georef_plan.py`. Then run:

```sh
python3 scripts/georef_plan.py   # writes data/derived/shuinan_detailed_plan_traced.geojson
python3 scripts/build_map.py
```

After a road-network refresh the fit can be rerun with `python3 scripts/register_plan.py` (needs `pip install numpy scipy shapely`).

Colour patches and zones: the ecological residential, cultural and commercial, innovation and R&D, economic and trade, and cultural and educational zones are matched by area against the plan's land-use table (each within 7%); park, drainage and blue patches follow colour conventions only. The figure is an unofficial English reference: the Chinese plan and official GIS/CAD data prevail.

### Major projects on the map

`scripts/locate_projects.py` places each project from `data/raw/shuinan_major_projects_2026.csv`, trying in order: a named OpenStreetMap feature of the right type (so that bus stops sharing the name are skipped), a road junction named in an official document, a block of the traced plan, then a published coordinate. Results go to `data/derived/project_locations.geojson`.

| # | Project | Latitude | Longitude | Located from |
|---|---|---|---|---|
| 1 | Taichung Green Museumbrary 臺中綠美圖 | 24.19295°N | 120.65446°E | OSM way 485125572 (grounds) |
| 2 | Taichung International Exhibition Center 臺中國際會展中心 | 24.19386°N | 120.65177°E | OSM way 1305878545 (building) |
| 3 | Shuinan Transfer Center 水湳轉運中心 | 24.19735°N | 120.65312°E | OSM way 1305878254 (bus station) |
| 4 | Taichung pop music and film center 臺中流行影音中心 | 24.18184°N | 120.65766°E | OSM way 485125554 (site) |
| 5 | Taichung dome stadium 臺中超巨蛋 | 24.18016°N | 120.65345°E | OSM ways 1391518117 and 1391518516 (BOT site, 10.6 ha mapped; the city gives about 16.35 ha on Innovation R&D Zone 1) |
| 6 | Taichung Central Park 中央公園 | 24.18518°N | 120.65463°E | Largest park patch of the traced plan (53.7 ha) |
| 7 | MRT Green Line, Wenhua Senior High School Station 捷運綠線文華高中站 | 24.17150°N | 120.66065°E | OSM node 4428067702 (station) |
| 8 | Parking supply in the park 園區停車供給 | – | – | Park-wide figure, not mapped |

### Shuinan coordinates

| Place | Latitude | Longitude | Source |
|---|---|---|---|
| Centre of the traced detailed plan | 24.1860°N | 120.6510°E | This repository's fit |
| Former Shuinan Airport reference point | 24.1863°N | 120.6540°E | OurAirports (RCLG) |
| Taichung Green Museumbrary (grounds) | 24.1929°N | 120.6545°E | OpenStreetMap |
| Taichung International Exhibition Center | 24.1939°N | 120.6518°E | OpenStreetMap |
| MRT Wenhua Senior High School Station | 24.1715°N | 120.6607°E | OpenStreetMap |

The runway thresholds lay at 24.1786°N and 24.1933°N (PilotNav). The traced plan spans roughly 120.6389–120.6632°E and 24.1737–24.1983°N.

## Road network and landmarks (OpenStreetMap)

The **Road network** layer covers motorways down to tertiary roads, rail and metro across the former Taichung City, plus local streets around Shuinan (shown when zoomed in).

This build environment cannot reach the Overpass API, so a GitHub Actions workflow fetches the data: **Actions → Fetch OSM road network → Run workflow** runs `scripts/fetch_roads.py`, `scripts/fetch_landmarks.py` and `scripts/locate_projects.py`, rebuilds the site and commits the results. Run it again to refresh. The data is licensed under the ODbL 1.0 and must be credited "© OpenStreetMap contributors".

## Basemap (English labels)

Standard OSM raster tiles have their labels baked in, in the local language, so the map draws vector tiles instead and chooses the label language itself:

- Tiles and style: [OpenFreeMap](https://openfreemap.org) (`https://tiles.openfreemap.org/styles/positron`), OpenMapTiles schema built from OpenStreetMap data; free, no API key
- Renderer: [MapLibre GL JS](https://maplibre.org) 4.7.1 from cdnjs, kept in step with the svg overlay (same Web Mercator, within a fraction of a pixel)
- Labels: every name label is switched to `name:en`, falling back to the local name where OSM has no English name. In the current OSM data about 94% of named primary and secondary roads in the area have an English name, about half of the local streets do
- Fallback: if MapLibre or the style cannot load (no WebGL, blocked network), the map uses the standard OSM tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`, labels in Chinese) and says so under the layer toggles; if those fail too, it shows no basemap
- Credits on the map: "OpenFreeMap © OpenMapTiles · data © OpenStreetMap contributors" (or the OSM credit when the fallback is in use). Do not remove them.
- The fallback tiles follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/): ordinary browsing only, no bulk downloading or prefetching.
- **Actions → Check basemap → Run workflow** opens the map in headless Chromium, checks that the vector basemap starts, lines up with the overlay and labels in English, and attaches screenshots of the three themes (`scripts/check_basemap.mjs`).
- Opened from `file://`, browsers may refuse to load tiles. Preview locally with:

  ```sh
  python3 -m http.server 8000
  # then open http://localhost:8000/
  ```

- To use another source, change `VECTOR_STYLE` (vector) or `TILE_URL` (fallback) in `templates/basemap.html` and update the on-map credit.

## Publishing to GitHub Pages

The site is static and served from the branch root (`.nojekyll` tells GitHub to serve files as they are):

1. Open **Settings → Pages** in the repository
2. Under **Build and deployment → Source**, choose **Deploy from a branch**
3. Choose the branch `claude/gracious-ride-hxhf3w` (the current default) and the folder `/ (root)`, then **Save**
4. After about a minute the site appears at https://yunching0513.github.io/HYD2026_Taichung/

Every push to that branch republishes the site. If `main` becomes the main branch later, switch the Pages branch to `main` on the same page.

## Rebuilding

After changing data in `data/` or templates in `templates/`, run:

```sh
python3 scripts/build_map.py
```

The script uses only the Python standard library. It inlines the GeoJSON and CSV data into `index.html` and `map/index.html`; commit the generated files so GitHub Pages updates.

## Data

| File | Contents | Source |
|---|---|---|
| `data/raw/former_city_8_districts.geojson` | 8 district boundaries of the former Taichung City | MOI district boundaries (2025-03-18) and NLSC village boundaries (2026-08-17), processed with plotdb/pdmaptw v2.4.0; Open Government Data License v1.0 |
| `data/raw/former_city_villages.geojson` | 214 village boundaries (the map's source) | As above |
| `data/raw/former_city_villages.csv` | Village attribute table, 214 rows | As above |
| `data/raw/old_downtown_5_districts.geojson` | Old downtown: 5 district boundaries | Subset of the former-city file |
| `data/raw/old_downtown_villages.geojson` | Old downtown: 108 village boundaries | Subset of the former-city file |
| `data/raw/context_xitun_beitun_districts.geojson` | Xitun and Beitun district boundaries | Subset of the former-city file |
| `data/raw/context_xitun_beitun_villages.geojson` | Xitun and Beitun: 81 village boundaries | Subset of the former-city file |
| `data/raw/shuinan_zoning_areas_2024.csv` | Zone areas of the Shuinan Airport site detailed plan | Urban Development Bureau, Taichung City Government: public briefing for the 2nd comprehensive review (2024-02-01) |
| `data/raw/shuinan_major_projects_2026.csv` | Status of major projects in the park | Taichung City Government project reports (2025-09-30, 2026-08-03) and news coverage; see each row's `source` |
| `data/raw/Figure_7-1_Detailed_Plan_A3_English_CAD.dxf` | Detailed plan, unofficial English reference trace | A3 sheet units, not georeferenced |
| `data/raw/reference_points.csv` | Reference coordinates and their sources | OpenStreetMap, Wikipedia, OurAirports |
| `data/derived/shuinan_detailed_plan_traced.geojson` | Detailed plan trace fitted to the road network | `scripts/georef_plan.py` |
| `data/derived/roads_osm.geojson` | Road and rail network | OpenStreetMap, ODbL 1.0 |
| `data/derived/landmarks_osm.geojson` | Named landmarks near the site, and markets (e.g. Feng Chia Night Market) across the former city | OpenStreetMap, ODbL 1.0 |
| `data/derived/project_locations.geojson` | Major project locations with method and source | `scripts/locate_projects.py` |

Notes:

- Boundaries are simplified (about 1,800 vertices for the 214 villages): use them for context, not for measurement or precise overlay. Areas come from the attribute table.
- The old-downtown and Xitun–Beitun files match the former-city files feature for feature (same geometry and attributes); the build reads the former-city files and warns if a subset drifts. The old downtown is the set of districts flagged `old_downtown`.
- Futai Village (富台里, East District, 0.052 km²) has no geometry in the source files. The map draws it as a dashed circle of the same area at its label point and says so in the village card.
- Coordinates are WGS84 longitude and latitude (CRS84).

## Layout

```
index.html                landing page (generated)
map/index.html            interactive map (generated)
templates/                page templates
scripts/build_map.py      site build
scripts/georef_plan.py    places the plan trace on WGS84
scripts/register_plan.py  fits the plan trace to OSM roads
scripts/fetch_roads.py    fetches OSM roads (run by GitHub Actions)
scripts/fetch_landmarks.py fetches OSM landmarks (run by GitHub Actions)
scripts/locate_projects.py places the major projects
scripts/check_basemap.mjs checks the basemap in a browser (run by GitHub Actions)
data/raw/                 source data
data/derived/             fitted plan trace, OSM roads and landmarks, project locations
```

---

## 中文說明

原臺中市與水湳經貿園區的研究資料與地圖，為#HackYourDistrict 2026準備。

線上瀏覽（GitHub Pages）：https://yunching0513.github.io/HYD2026_Taichung/

### 成果

**原臺中市基本圖（`map/index.html`）**：介面以英文為主、中文為輔，里名、區名、分區、建設與路名都附上中文，搜尋可輸入英文或中文里名。

- 原臺中市8區、214里的界線，疊在OpenStreetMap底圖上；舊市區5區（中、東、南、西、北區）用較深的底色並加上合併外框，西屯、南屯、北屯用較淺的底色
- 頁首可切換兩種風格與三種色調，選擇會記在瀏覽器中，並與成果首頁同步：
  - **Deck**簡報風：HYD健康城市工作坊簡報的黑白灰風格（Instrument Serif、暖灰、2px墨線）
  - **Program**議程風：參考HYD臺中議程頁（Bricolage Grotesque與IBM Plex字體、深藍字配冷灰底、圓角卡片），舊市區、重大建設標記與圖表改用黃色重點色
  - 兩種風格都有**Light**淺色、**White**白色、**Dark**深色；尚未選擇時依裝置設定顯示淺色或深色
- 拖曳平移、滾輪或雙指縮放；方向鍵平移、`+`／`-`縮放、`0`回到全圖
- 滑過里顯示名稱與面積；點選或搜尋里名可查看面積、占行政區比例、面積排序與村里代碼
- OSM路網，主要道路沿線標示英文與中文路名
- 由Figure 7-1描繪、並對齊路網的水湳細部計畫疊圖
- 重大建設編號標記，附OSM基地範圍與出處
- 圖框經緯度刻度、比例尺與指北針
- 側欄：水湳機場原址細部計畫土地使用面積（2024）與園區重大建設進度（2026）

成果首頁（`index.html`）介紹地圖並列出所有可下載的資料。

### 細部計畫疊圖

DXF是畫在A3圖紙上的描圖（單位mm），本身沒有地理座標；檔頭的`$LATITUDE`／`$LONGITUDE`（37.795, -122.394）是AutoCAD預設的舊金山座標。`scripts/georef_plan.py`以相似轉換把它放到WGS84上，參數由`scripts/register_plan.py`對齊OSM道路中心線求得：比例12.52 m／圖面mm（約1:12,500，與分區面積推算一致）、旋轉0.4°（與跑道18/36一致）、平移(-1927.9, -1848.6) m。

對齊後，街廓邊緣到最近道路的中位距離為11公尺，觸及道路的街廓內部比例為3%（配準前為26公尺與12%），誤差估計在數十公尺內。兩項獨立檢核都吻合：OSM標註的綠美圖基地距離描圖中央公園北端約55公尺，OSM的超巨蛋基地輪廓與描圖的創研街廓重合。最初的估計偏西約210公尺，原因是維基百科的綠美圖座標比實際基地偏西約210公尺。

地圖側欄的**Adjust position**可微調疊圖，**Copy parameters**會輸出`SCALE`、`ROTATION_DEG`、`TRANSLATION_M`，填回`georef_plan.py`後執行上方兩行指令重建。路網更新後可重跑`python3 scripts/register_plan.py`（需`pip install numpy scipy shapely`）。

生態住宅、文化商業、創新研發、經貿、文教區五類色塊以面積對照計畫面積表（誤差皆在7%以內）；公園、排水道與藍色色塊只依顏色慣例判斷。此圖為非官方英文參考版，以中文計畫書與官方圖資為準。

### 重大建設位置

`scripts/locate_projects.py`依序嘗試：名稱與類型相符的OSM設施（排除同名公車站）、官方文件寫明的路口、計畫圖街廓，最後才用已發布的座標。7項中6項取自OSM設施，中央公園取自計畫圖公園色塊（53.7公頃），園區停車供給為全區統計，不標點。超巨蛋的OSM基地為10.6公頃，市府資料為創研一約16.35公頃。各項座標見上方英文表格。

### 路網與地標（OSM）

路網涵蓋原臺中市範圍的國道到區道、鐵路與捷運，以及水湳周邊巷道（放大後顯示）。本環境連不到Overpass API，因此由GitHub Actions抓取：**Actions → Fetch OSM road network → Run workflow**，會依序執行`fetch_roads.py`、`fetch_landmarks.py`、`locate_projects.py`，重建網站並commit結果。資料授權為ODbL 1.0，須標示「© OpenStreetMap contributors」。

### 底圖（英文標註）

OSM標準圖磚的文字是伺服器預先畫好的，只會顯示當地語言（中文），因此地圖改用[OpenFreeMap](https://openfreemap.org)的向量圖磚（OpenMapTiles格式，資料來自OSM，免費、免API key），由[MapLibre GL JS](https://maplibre.org)在瀏覽器繪製，並與上層的SVG圖層對齊（誤差不到1像素）。

- 所有名稱標註改用OSM的`name:en`；沒有英文名稱的地物維持原本的中文。目前範圍內約94%的主要與次要道路有英文名，巷道約一半。
- 若MapLibre或樣式無法載入（例如瀏覽器不支援WebGL、網路被擋），會自動退回OSM標準圖磚（中文標註），並在圖層開關下方說明；兩者都失敗時不顯示底圖。
- 圖上的「OpenFreeMap © OpenMapTiles · data © OpenStreetMap contributors」出處請勿移除。退回OSM圖磚時，依[OSM圖磚使用政策](https://operations.osmfoundation.org/policies/tiles/)不可大量下載。
- **Actions → Check basemap → Run workflow**會用無頭瀏覽器開啟地圖，檢查向量底圖是否載入、是否對齊、標註是否為英文，並附上三種主題的截圖。
- 以`file://`直接開啟時可能載不到圖磚，本機預覽請用`python3 -m http.server 8000`。要更換來源，修改`templates/basemap.html`的`VECTOR_STYLE`或`TILE_URL`並更新出處標示。

### 發布到GitHub Pages

到**Settings → Pages**，**Source**選**Deploy from a branch**，**Branch**選`claude/gracious-ride-hxhf3w`、資料夾`/ (root)`，按**Save**。約一分鐘後網站上線，之後每次push都會自動更新。若日後改用`main`，記得同步更改發布分支。

### 重新建置

修改`data/`或`templates/`後執行`python3 scripts/build_map.py`（只用Python標準函式庫），並一併commit產生的`index.html`與`map/index.html`。

### 資料與注意事項

各檔案的內容與來源見上方英文的Data表格。地圖以原臺中市8區、214里的檔案為準；舊市區與西屯、北屯的檔案是它的子集，幾何與屬性完全相同，建置時若不一致會發出警告。邊界為簡化版本（214里合計約1,800個頂點），適合示意與脈絡判讀，不宜用於量測或精確套疊；座標系統為WGS84經緯度（CRS84）。

東區富台里（0.052平方公里）在原始檔中沒有邊界，地圖在其標籤點以等面積的虛線圓表示，並在里別資訊中註明。
