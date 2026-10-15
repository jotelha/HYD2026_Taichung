# Boba Index

A prototype app for a night-market authenticity index in Taichung, built for #HackYourDistrict 2026 on top of the former Taichung City research map. For now it maps the markets and night markets in OpenStreetMap; the index itself is not computed yet.

Live site (GitHub Pages): https://jotelha.github.io/HYD2026_Taichung/

*中文說明在英文之後（[跳到中文](#中文說明)）。*

## The map (`index.html`)

The interface is English-first, with Chinese as the secondary language: labels and side panels are in English, and market and district names carry their Chinese names.

- The markets and night markets mapped in OpenStreetMap inside the 8 districts of the former Taichung City, on an English-labelled basemap
- Night markets as filled dots with their mapped area in colour; other markets as hollow dots. Hover or tap for the name, district, mapped area, coordinates and OSM feature
- A side list of the night markets, largest first: a checkbox switches each one's dot, label and area on or off (**All** / **None** for the lot), and **Show on map** zooms to it. The **Other markets** layer toggle covers the remaining markets
- **Mock booths** at Feng Chia: zoom in to see 622 booth rectangles coloured by their Boba Index (0–5 on the viridis scale, purple through green to yellow); hover one for its id, street and score. Positions and scores are invented (see below)
- The districts with their night-market and market counts; click one to zoom to it
- Two styles and three tones from the switches in the header, remembered in the browser:
  - **Deck**: the monochrome look of the HYD Healthy City Workshop deck (Instrument Serif, warm greys, 2px ink rules)
  - **Program**: after the HYD Taichung program page (Bricolage Grotesque and IBM Plex, navy ink on cool grey, sun-yellow highlights, rounded cards)
  - **Light**, **White** or **Dark** for either style; until one is chosen, light or dark follows the system setting
- Pan by dragging, zoom with the wheel or a pinch; arrow keys pan, `+` / `-` zoom, `0` shows the full extent
- Coordinate ticks on the neatline, scale bar and north arrow

`map/index.html`, the map's old address, redirects to the home page.

## Markets (OpenStreetMap)

`scripts/fetch_landmarks.py` fetches every `amenity=marketplace` feature and every feature named …夜市 across the former city. `build_map.py` keeps marketplaces and untagged features whose name ends in 夜市 (so the parking lots, access ways and restaurants that only share the name drop out), drops stall sub-areas and duplicate points, and clips to the district boundaries. That leaves 62 markets, 7 of them night markets. Markets that nobody has mapped in OSM are missing (for example Yizhong Street).

Night markets show their mapped OSM outline as a coloured area. For Feng Chia that outline covers only Wenhua Road and Fengjia Road Lane 20, so the map adds a dashed **approximate full extent** (6.28 ha): the OSM centrelines of Wenhua Road, Fengjia Road, Fuxing Road and Fengjia Road Lane 20 (the streets [Business Today, 2015](https://www.businesstoday.com.tw/article/category/80392/post/201507160040/) names as the market area), clipped to the stretches set in `scripts/fengjia_extent.py`, buffered by 15 m and merged. No official boundary is published; treat it as an approximation. Regenerate with `python3 scripts/fengjia_extent.py` (needs `pip install shapely` and Overpass access).

### Mock booths (Feng Chia)

There is no booth data yet, so `scripts/mock_booths.py` (standard library) invents some to design the map with. It lays out 3.5 × 3 m booths every 6.5 m along both sides of the Feng Chia market streets, set back behind the carriageway (by OSM road class), skipping spots in a crossing street, too close to another booth or outside the approximate extent. Each booth gets a Boba Index drawn uniformly from 0.0 to 5.0 in steps of 0.1, from a fixed seed, so reruns give the same 622 booths. It reads the street centrelines that `fengjia_extent.py` stores next to the extent and writes `data/derived/fengjia_booths_mock.geojson`. The map labels everything from this file as mock data.

```sh
python3 scripts/mock_booths.py   # then python3 scripts/build_map.py
```

The booths are drawn at true size and appear once they are about 4 px long; the map zooms in far enough for them to reach about 20 px. Scores are coloured on viridis, a multi-hue scale whose lightness rises evenly with the score and which stays readable with colour-vision deficiencies; it starts one step above its darkest purple so low scores stay visible on the dark theme, and the same colour means the same score in every theme.

The usual build environment cannot reach the Overpass API, so a GitHub Actions workflow fetches the data: **Actions → Fetch OSM road network → Run workflow** runs `scripts/fetch_roads.py`, `scripts/fetch_landmarks.py` and `scripts/locate_projects.py`, rebuilds the site and commits the results. Run it again to refresh. The data is licensed under the ODbL 1.0 and must be credited "© OpenStreetMap contributors".

## Basemap (English labels)

Standard OSM raster tiles have their labels baked in, in the local language, so the map draws vector tiles instead and chooses the label language itself:

- Tiles and style: [OpenFreeMap](https://openfreemap.org) (`https://tiles.openfreemap.org/styles/positron`), OpenMapTiles schema built from OpenStreetMap data; free, no API key
- Renderer: [MapLibre GL JS](https://maplibre.org) 4.7.1 from cdnjs, kept in step with the svg overlay (same Web Mercator, within a fraction of a pixel)
- Labels: every name label is switched to `name:en`, falling back to the local name where OSM has no English name
- Fallback: if MapLibre or the style cannot load (no WebGL, blocked network), the map uses the standard OSM tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`, labels in Chinese) and says so under the layer toggles; if those fail too, it shows no basemap
- Credits on the map: "OpenFreeMap © OpenMapTiles · data © OpenStreetMap contributors" (or the OSM credit when the fallback is in use). Do not remove them.
- The fallback tiles follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/): ordinary browsing only, no bulk downloading or prefetching.
- **Actions → Check basemap → Run workflow** opens the map in headless Chromium, checks that the vector basemap starts, lines up with the overlay (at the Feng Chia marker) and labels in English, and attaches screenshots of the three themes (`scripts/check_basemap.mjs`).
- Opened from `file://`, browsers may refuse to load tiles. Preview locally with:

  ```sh
  python3 -m http.server 8000
  # then open http://localhost:8000/
  ```

- To use another source, change `VECTOR_STYLE` (vector) or `TILE_URL` (fallback) in `templates/basemap.html` and update the on-map credit.

## Publishing to GitHub Pages

The site is static and served from the branch root (`.nojekyll` tells GitHub to serve files as they are). Under **Settings → Pages**, the source is **Deploy from a branch**, branch `2026-10-15-HYD2026`, folder `/ (root)`. Every push to that branch republishes the site at https://jotelha.github.io/HYD2026_Taichung/.

## Rebuilding

After changing data in `data/` or the template in `templates/`, run:

```sh
python3 scripts/build_map.py
```

The script uses only the Python standard library. It inlines the district boundaries and markets into `index.html` and writes the `map/index.html` redirect; commit the generated files so GitHub Pages updates.

## Data

Used by the map:

| File | Contents | Source |
|---|---|---|
| `data/raw/former_city_8_districts.geojson` | 8 district boundaries of the former Taichung City | MOI district boundaries (2025-03-18) and NLSC village boundaries (2026-08-17), processed with plotdb/pdmaptw v2.4.0; Open Government Data License v1.0 |
| `data/derived/landmarks_osm.geojson` | Markets and night markets across the former city, plus named landmarks near Shuinan | OpenStreetMap, ODbL 1.0 |
| `data/derived/fengjia_night_market_extent.geojson` | Feng Chia Night Market, approximate full extent (our approximation), plus the clipped street centrelines it was built from | `scripts/fengjia_extent.py`; OpenStreetMap, ODbL 1.0 |
| `data/derived/fengjia_booths_mock.geojson` | **Mock** Feng Chia booths with random Boba Index scores | `scripts/mock_booths.py` |

Kept from the former-city and Shuinan research map, not shown on the page: village boundaries and attributes (`former_city_villages.*`, the old-downtown and Xitun–Beitun subsets), the Shuinan detailed plan (`Figure_7-1_Detailed_Plan_A3_English_CAD.dxf`, `shuinan_detailed_plan_traced.geojson`), zoning areas, major projects and their locations, reference points and the OSM road network, with the scripts that produce them (`georef_plan.py`, `register_plan.py`, `fetch_roads.py`, `locate_projects.py`). The git history has the earlier pages that used them.

Boundaries are simplified: use them for orientation, not measurement. Coordinates are WGS84 longitude and latitude (CRS84).

## Layout

```
index.html                 the Boba Index map (generated)
map/index.html             redirect to the home page (generated)
templates/basemap.html     page template
scripts/build_map.py       site build
scripts/fetch_landmarks.py fetches OSM markets and landmarks (run by GitHub Actions)
scripts/fengjia_extent.py  approximates the Feng Chia Night Market extent
scripts/mock_booths.py     generates mock Feng Chia booths with random scores
scripts/check_basemap.mjs  checks the basemap in a browser (run by GitHub Actions)
data/raw/                  source data
data/derived/              OSM extracts and derived layers
```

---

## 中文說明

**珍奶指數（Boba Index）**：臺中夜市「道地程度」指數的原型App，為#HackYourDistrict 2026開發，以原臺中市研究地圖為基礎。目前先呈現OpenStreetMap上的市場與夜市，指數本身尚未計算。

線上瀏覽（GitHub Pages）：https://jotelha.github.io/HYD2026_Taichung/

### 地圖（`index.html`）

介面以英文為主、中文為輔，市場與行政區名稱都附上中文。

- 原臺中市8區範圍內、OSM上的市場與夜市，疊在英文標註底圖上
- 夜市以實心點加彩色範圍表示，其他市場以空心點表示；滑過或點選可看名稱、行政區、範圍面積、座標與OSM地物
- 側欄列出各夜市（依面積排序）：勾選框可個別開關每個夜市的標記、名稱與範圍（**All**／**None**一次全開或全關），**Show on map**移到該夜市；其他市場由圖層開關的**Other markets**控制
- 逢甲夜市的**模擬攤位**：放大後可看到622個依珍奶指數（0–5，viridis色階：紫→綠→黃）著色的攤位方塊，滑過可看編號、所在街道與分數；位置與分數皆為虛構（見下方說明）
- 各行政區的夜市／市場數，點選可縮放到該區
- 頁首可切換兩種風格（**Deck**簡報風、**Program**議程風）與三種色調（**Light**、**White**、**Dark**），選擇會記在瀏覽器中；尚未選擇時依裝置設定顯示淺色或深色
- 拖曳平移、滾輪或雙指縮放；方向鍵平移、`+`／`-`縮放、`0`回到全圖
- 圖框經緯度刻度、比例尺與指北針

舊網址`map/index.html`會自動轉到首頁。

### 市場資料（OSM）

`fetch_landmarks.py`抓取原臺中市範圍內所有`amenity=marketplace`及名稱含「夜市」的地物；`build_map.py`保留市場及名稱以「夜市」結尾、未另標類型的地物（排除同名的停車場、通道與餐廳），去除攤區分區與重複點位，並以區界裁切，共62處，其中7處夜市。OSM未繪製的市場不會出現（例如一中街）。

夜市以色塊顯示OSM上的範圍；逢甲夜市在OSM上只畫了文華路與逢甲路20巷，因此另以虛線標示**約略全範圍**（6.28公頃）：取文華路、逢甲路、福星路、逢甲路20巷（[商業周刊2015年報導](https://www.businesstoday.com.tw/article/category/80392/post/201507160040/)所列範圍）的OSM道路中心線，依`scripts/fengjia_extent.py`設定的路段裁切，兩側各外擴15 m後合併。官方未公布範圍，僅供參考。重建：`python3 scripts/fengjia_extent.py`（需`pip install shapely`及Overpass連線）。

**模擬攤位（逢甲夜市）**：目前沒有攤位資料，因此由`scripts/mock_booths.py`（標準函式庫）產生虛構攤位供設計地圖：沿逢甲夜市各街道兩側、退到車道之外（依OSM道路等級），每6.5公尺放一個3.5 × 3公尺的攤位，略過位於交叉道路上、與其他攤位太近或超出約略範圍的位置；每個攤位的珍奶指數從0.0到5.0（間隔0.1）均勻隨機抽取，使用固定亂數種子，重跑結果相同（共622個）。腳本讀取`fengjia_extent.py`一併儲存的街道中心線，輸出`data/derived/fengjia_booths_mock.geojson`；地圖上一律標示為模擬資料。攤位依實際尺寸繪製，約4像素長時才顯示，最大縮放時約20像素。分數以viridis色階著色：多色相、亮度隨分數均勻遞增，色覺辨識障礙者也能分辨；色階從最深紫色的下一階開始，深色主題下低分仍看得見，各主題同色同分。

一般建置環境連不到Overpass API，因此由GitHub Actions抓取：**Actions → Fetch OSM road network → Run workflow**，會依序執行`fetch_roads.py`、`fetch_landmarks.py`、`locate_projects.py`，重建網站並commit結果。資料授權為ODbL 1.0，須標示「© OpenStreetMap contributors」。

### 底圖（英文標註）

OSM標準圖磚的文字是伺服器預先畫好的，只會顯示當地語言（中文），因此地圖改用[OpenFreeMap](https://openfreemap.org)的向量圖磚（OpenMapTiles格式，資料來自OSM，免費、免API key），由[MapLibre GL JS](https://maplibre.org)在瀏覽器繪製，並與上層的SVG圖層對齊（誤差不到1像素）。

- 所有名稱標註改用OSM的`name:en`；沒有英文名稱的地物維持原本的中文。
- 若MapLibre或樣式無法載入（例如瀏覽器不支援WebGL、網路被擋），會自動退回OSM標準圖磚（中文標註），並在圖層開關下方說明；兩者都失敗時不顯示底圖。
- 圖上的「OpenFreeMap © OpenMapTiles · data © OpenStreetMap contributors」出處請勿移除。退回OSM圖磚時，依[OSM圖磚使用政策](https://operations.osmfoundation.org/policies/tiles/)不可大量下載。
- **Actions → Check basemap → Run workflow**會用無頭瀏覽器開啟地圖，檢查向量底圖是否載入、是否對齊（以逢甲夜市標記為準）、標註是否為英文，並附上三種主題的截圖。
- 以`file://`直接開啟時可能載不到圖磚，本機預覽請用`python3 -m http.server 8000`。要更換來源，修改`templates/basemap.html`的`VECTOR_STYLE`或`TILE_URL`並更新出處標示。

### 發布到GitHub Pages

**Settings → Pages**的來源為**Deploy from a branch**，分支`2026-10-15-HYD2026`、資料夾`/ (root)`；每次push到該分支都會更新https://jotelha.github.io/HYD2026_Taichung/。

### 重新建置

修改`data/`或`templates/`後執行`python3 scripts/build_map.py`（只用Python標準函式庫），並一併commit產生的`index.html`與`map/index.html`。

### 資料

地圖使用的檔案與來源見上方英文的Data表格。原臺中市與水湳研究地圖的其他資料（里界與屬性、水湳細部計畫、分區面積、重大建設、參考點、OSM路網）及產生它們的腳本仍保留在repo中，但不再顯示於網頁；舊版頁面可在git歷史中找到。邊界為簡化版本，適合示意，不宜用於量測；座標系統為WGS84經緯度（CRS84）。
