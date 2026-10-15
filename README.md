# Boba Index: Built On Belonging and Authenticity

The **Boba Index** (**B**uilt **O**n **B**elonging and **A**uthenticity) is a prototype app for rating Taichung's night markets on how authentic they are and how much they belong to their place, built for #HackYourDistrict 2026 on top of the former Taichung City research map. For now it maps the markets and night markets in OpenStreetMap; the index itself is not computed yet.

Live site (GitHub Pages): https://jotelha.github.io/HYD2026_Taichung/

*中文說明在英文之後（[跳到中文](#中文說明)）。*

## The map (`index.html`)

The interface is English-first, with Chinese as the secondary language: labels and side panels are in English, and market and district names carry their Chinese names.

- The markets and night markets mapped in OpenStreetMap inside the 8 districts of the former Taichung City, on an English-labelled basemap
- The map opens on the Feng Chia Night Market, zoomed in far enough for its booths to show; the full-extent button (or `0`) shows the whole former city
- Night markets as filled dots with their mapped area in colour; other markets as hollow dots. Hover or tap for the name, district, mapped area, coordinates and OSM feature
- A side list of the night markets, largest first: a checkbox switches each one's dot, label and area on or off (**All** / **None** for the lot), and **Show on map** zooms to it. In the **Layers** panel, **Night-market areas** switches the coloured outlines (and Feng Chia's dashed extent) on and off, **Booths** the Feng Chia booths, and **Other markets** the remaining markets
- **Mock booths** at Feng Chia: zoom in to see 399 booth rectangles coloured by their Boba Index (0–5 on the viridis scale, purple through green to yellow); hover one for its name, id, street and score. Names, positions and scores are invented (see below)
- A **Boba Index heat map** over Feng Chia: the booth scores smoothed into a continuous surface on its own plasma scale (purple → orange → yellow), stretched from its lowest to its highest value, readable from the overview zooms on; a slider sets the smoothing width (10–60 m, default 25 m), and hovering shows the smoothed value and how many booths it averages (see below)
- A collapsible **legend** in the map's top-left corner: the market symbols and areas, the district boundary, and the colour keys of the booths and the heat map (each shown while its layer is on; the heat-map key shows the current range). It starts collapsed on small screens; the north arrow sits under the zoom buttons
- **Find a Booth**: search the mock booths by English or Chinese name, dish, street or number (e.g. `oden`, `阿明 臭豆腐`, `FJ-0316`; every word must match). Results show the score; picking one (or pressing Enter for the first) zooms to the booth, rings it and shows a card, switching Feng Chia and the booth layer on if needed. Clicking a booth on the map selects it too; `Esc` clears the selection
- **Garbage bins**: public bins, waste containers and recycling points mapped in OpenStreetMap (70 in the eight districts), as small bin icons from street-level zooms; hover one for its type and OSM feature (see below)
- **Stores with toilets**: convenience stores tagged in OpenStreetMap as having a toilet (123 in the eight districts), as blue WC badges from street-level zooms; hover one for the store, branch and opening hours (see below)
- **Find a Place** and **Walking Route**: search any address or place around Taichung (Chinese or English), see it on the map, and use it as start (A) or destination (B); start from your own location, or send a booth there with **Walk here** on its card. The walking route is drawn on the map with its distance, time and turn-by-turn steps (click a step to zoom to it); see below
- The districts with their night-market and market counts; click one to zoom to it
- Three styles and three tones from the switches in the header, remembered in the browser:
  - **Boba** (the default): the Boba Index brand, with the logo's brown ink on cream, boba-orange highlights, Bricolage Grotesque and rounded cards
  - **Deck**: the monochrome look of the HYD Healthy City Workshop deck (Instrument Serif, warm greys, 2px ink rules)
  - **Program**: after the HYD Taichung program page (Bricolage Grotesque and IBM Plex, navy ink on cool grey, sun-yellow highlights, rounded cards)
  - **Light**, **White** or **Dark** for any style; until one is chosen, light or dark follows the system setting
- Pan by dragging, zoom with the wheel or a pinch; arrow keys pan, `+` / `-` zoom, `0` shows the full extent
- Coordinate ticks on the neatline, scale bar and north arrow

`map/index.html`, the map's old address, redirects to the home page.

## Markets (OpenStreetMap)

`scripts/fetch_landmarks.py` fetches every `amenity=marketplace` feature and every feature named …夜市 across the former city. `build_map.py` keeps marketplaces and untagged features whose name ends in 夜市 (so the parking lots, access ways and restaurants that only share the name drop out), drops stall sub-areas and duplicate points, and clips to the district boundaries. That leaves 62 markets, 7 of them night markets. Markets that nobody has mapped in OSM are missing (for example Yizhong Street).

Night markets show their mapped OSM outline as a coloured area. For Feng Chia that outline covers only Wenhua Road and Fengjia Road Lane 20, so the map adds a dashed **approximate full extent** (6.28 ha): the OSM centrelines of Wenhua Road, Fengjia Road, Fuxing Road and Fengjia Road Lane 20 (the streets [Business Today, 2015](https://www.businesstoday.com.tw/article/category/80392/post/201507160040/) names as the market area), clipped to the stretches set in `scripts/fengjia_extent.py`, buffered by 15 m and merged. No official boundary is published; treat it as an approximation. Regenerate with `python3 scripts/fengjia_extent.py` (needs `pip install shapely` and Overpass access).

### Stores with toilets (OpenStreetMap)

`scripts/fetch_stores.py` (standard library) fetches every `shop=convenience` across the former city, leaves out the Shopee parcel pick-up points tagged as convenience stores (蝦皮店到店, 97 of them), and writes `data/derived/convenience_stores_osm.geojson` with each store's `toilets` tag: of 1,026 stores, 164 are tagged `yes`, 66 `no` and 796 not at all. `build_map.py` puts the `toilets=yes` stores inside the eight districts (123) on the **Stores with toilets** layer. Most 7-Eleven and FamilyMart branches have customer toilets, but few stores carry the tag yet, so many stores with toilets are missing; the file keeps the untagged stores in case the layer should show them too. The "Fetch OSM road network" workflow refreshes the file with the other OSM data.

### Place search and walking routes

Both run in the browser against free public services built on OpenStreetMap data, with no API key:

- **Place search**: [Nominatim](https://nominatim.org/), on submit only (its usage policy allows at most one request a second and no search-as-you-type), limited to Taiwan and a box around the former city, with English names where OSM has them. Street names and landmarks are well covered; house numbers in Taichung only partly, so an exact address sometimes lands on the street.
- **Walking routes**: [Valhalla](https://valhalla.github.io/valhalla/) on the FOSSGIS public server (`valhalla1.openstreetmap.de`), pedestrian costing, directions in English with street names as mapped in OSM (often Chinese). The route line, A/B pins and steps come from its response; views fitted to a route (and the opening view) leave room for the map legend.

Both services are for light, fair use, fine for a demonstrator; a real launch should host its own Nominatim/Valhalla or use a paid provider. Search text and route points are sent to them, as the Data Notes say. Google's search and directions are not used: they need a paid key and their terms do not allow showing results on a non-Google map. Public transport routing would need Taiwan's TDX platform.

### Garbage bins (OpenStreetMap)

`scripts/fetch_bins.py` (standard library) fetches `amenity=waste_basket` (public bins), `amenity=waste_disposal` (larger containers) and `amenity=recycling` across the former city, leaving out recycling centres (facilities, not bins), and writes `data/derived/waste_bins_osm.geojson`; `build_map.py` keeps those inside the eight districts. The **Garbage bins** layer draws them as solid bin icons (bins and containers) or outlined ones (recycling) from street-level zooms. Public bins are rare in Taiwan, where household rubbish goes to the garbage trucks, and OSM coverage is patchy, so the layer shows what is mapped, not every bin. The "Fetch OSM road network" workflow refreshes the file with the other OSM data.

Four **market bins** at Feng Chia come from `data/raw/custom_bins.csv` (id, English and Chinese place name, lon, lat, note), placed by the Boba Index team at the Fengjia Road corners with Wenhua and Fuxing Roads, in Lane 20 and on Wenhua Road. They draw a size larger in the brand orange, and their tooltip names the place and says the team placed them. Add a row to the CSV and rebuild to place another.

### Mock booths (Feng Chia)

There is no booth data yet, so `scripts/mock_booths.py` (standard library) invents some to design the map with. It lays out 3.5 × 3 m booths every 10.2 m along both sides of the Feng Chia market streets, set back behind the carriageway (by OSM road class), skipping spots in a crossing street, too close to another booth or outside the approximate extent. Scores cluster in space rather than being uniform: a smooth field over the market starts at 2.5 and adds three Gaussian maxima and three minima (±1.6–2.3 points, 40–80 m wide) centred on randomly chosen booths at least 120 m apart; each booth's Boba Index is the field at its position plus strong noise (standard deviation 2.5); a draw outside 0.0–5.0 is redrawn rather than clipped (a truncated normal), so no scores pile up at the ends, and the result is rounded to 0.1. Single booths look almost random (a booth's score correlates only about 0.2 with the field), but the heat map partly recovers the hot and cold spots: its smoothed values correlate about 0.56 with the field at the default 25 m and 0.70 at 40 m, so wider smoothing shows them more clearly. The field's centres are stored in the output (`score_field`), and the `FIELD_*` constants tune it. A fixed seed means reruns give the same 399 booths. The count follows the roughly 400 stall spaces that travel guides give for Feng Chia (no official figure is published; a 2023 Feng Chia University survey counted 955 open businesses in the wider shopping district, shops included). Each booth also gets an invented name in Chinese and English, put together from the patterns real stalls use (阿 + a given name, a surname + 記, a surname + a title, or a place of origin, sometimes a descriptor such as 古早味 or 手工, then the dish) and 30 typical night-market dishes, e.g. 許記正宗蔥油餅 "Hsu's Original Scallion Pancake". The patterns and dishes come from Feng Chia food guides ([TVBS 食尚玩家](https://supertaste.tvbs.com.tw/food/351458), [funtime](https://www.funtime.com.tw/blog/funtime/taichung-fengjia-food-map)) and [Smile Taiwan](https://smiletaiwan.cw.com.tw/article/3000). No name may contain a real Feng Chia stall's name (`REAL_STALLS` in the script): a real stall shown with a random score would read as a rating of that business. Names use their own seed, so changing them does not move the scores. It reads the street centrelines that `fengjia_extent.py` stores next to the extent and writes `data/derived/fengjia_booths_mock.geojson`. As a demonstrator, the page shows these booths like real data, without mock labels; a single sentence in the page's Data Notes says that the Feng Chia booth layout, names and scores are illustrative and do not describe actual stalls. Keep that sentence while the data is invented, and keep real stall names out (`REAL_STALLS`): random scores shown under a real stall's name would read as a rating of that business.

```sh
python3 scripts/mock_booths.py   # then python3 scripts/build_map.py
```

The **heat map** is the Gaussian-weighted mean of the booth scores around each 2 m cell (a Nadaraya–Watson kernel smoother, computed in the browser), not booth density and not the field the mock scores were generated from, so it will work unchanged on real booth data. The slider sets the kernel width; cells fade where few booths are near and the surface is clipped to the approximate market extent. Its colours use plasma, a different scale from the booths' viridis so the two layers never read as one, stretched from the lowest to the highest smoothed value among well-covered cells (for example 1.7–3.5 at 25 m, 1.9–3.1 at 60 m); the heat-map key in the map legend shows the current range, so compare its numbers rather than the colours across widths. It smooths away single-booth outliers, and its picture depends on the width chosen. **Boba Index heat map** and **Booths** switch independently.

The booths are drawn at true size and appear once they are about 4 px long; the map zooms in far enough for them to reach about 20 px. Scores are coloured on viridis, a multi-hue scale whose lightness rises evenly with the score and which stays readable with colour-vision deficiencies; it starts one step above its darkest purple so low scores stay visible on the dark theme, and the same colour means the same score in every theme.

The usual build environment cannot reach the Overpass API, so a GitHub Actions workflow fetches the data: **Actions → Fetch OSM road network → Run workflow** runs `scripts/fetch_roads.py`, `scripts/fetch_landmarks.py` and `scripts/locate_projects.py`, rebuilds the site and commits the results. Run it again to refresh. The data is licensed under the ODbL 1.0 and must be credited "© OpenStreetMap contributors".

## Brand

The logo, banner and pearl scale in `img/` were made by the Boba Index team and are published with the site:

| File | Use |
|---|---|
| `img/boba-index-logo.jpg` | Square logo (752 × 752): a map pin shaped like a bubble tea cup. Scaled copies are the header logo (`logo-112.png`), the favicon (`favicon-32.png`) and the home-screen icon (`apple-touch-icon.png`) |
| `img/boba-index-banner.jpg` | Wide banner (1395 × 752), used as the link-preview image (`og:image`, absolute URL from `SITE_URL` in `build_map.py`) |
| `img/boba-index-pearl-scale.jpg` | The pearl scale: cups filling with pearls. The page redraws it as the **pearl meter**, one cup whose nine pearls fill from the bottom with the Boba Index (5 = full), shown in booth tooltips, the booth card, search results and the legend |

Brand colours, sampled from the logo: orange `#fd9f02`, cream `#f7f0d6`, brown `#42200f`. The team's "Boba Fengjia" concept poster adds two supporting colours, deep green `#183c30` and terracotta (`#cc6048` on the poster, `#b8523b` on the page for contrast; lighter versions in dark mode), which the Boba style uses for headings, the eyebrow line, section rules, the selected-booth ring and small notes. From the poster also come the line "Taste a deeper Taichung" (header and link preview), "Not just a score — a story." (booth card) and the note on the Feng Chia entry that the market is named after Feng Chia University, itself named for the poet and educator Qiu Fengjia 丘逢甲 (1864–1912). The poster's figures (founding year, student numbers, stall count, visit time) are not used until they are checked. The **Boba** style uses them for the page; the map's data colours (viridis booths, plasma heat map) stay the same in every style so the data reads the same.

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
| `data/raw/custom_bins.csv` | Market bins placed by the Boba Index team at Feng Chia | Boba Index team |
| `data/derived/convenience_stores_osm.geojson` | Convenience stores with their toilets tag | `scripts/fetch_stores.py`; OpenStreetMap, ODbL 1.0 |
| `data/derived/waste_bins_osm.geojson` | Garbage bins, waste containers and recycling points | `scripts/fetch_bins.py`; OpenStreetMap, ODbL 1.0 |
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
scripts/fetch_bins.py      fetches OSM garbage bins (run by GitHub Actions)
scripts/fetch_stores.py    fetches OSM convenience stores and their toilets tag (run by GitHub Actions)
scripts/fengjia_extent.py  approximates the Feng Chia Night Market extent
scripts/mock_booths.py     generates mock Feng Chia booths with random scores
scripts/check_basemap.mjs  checks the basemap in a browser (run by GitHub Actions)
data/raw/                  source data
data/derived/              OSM extracts and derived layers
img/                       brand assets (logo, banner, pearl scale, icons)
```

---

## 中文說明

**珍奶指數（Boba Index，Built On Belonging and Authenticity，以歸屬感與道地為本）**：評估臺中夜市道地程度與在地歸屬感的指數原型App，為#HackYourDistrict 2026開發，以原臺中市研究地圖為基礎。目前先呈現OpenStreetMap上的市場與夜市，指數本身尚未計算。

線上瀏覽（GitHub Pages）：https://jotelha.github.io/HYD2026_Taichung/

### 地圖（`index.html`）

介面以英文為主、中文為輔，市場與行政區名稱都附上中文。

- 原臺中市8區範圍內、OSM上的市場與夜市，疊在英文標註底圖上
- 地圖開啟時直接放大到逢甲夜市並顯示攤位；按全圖按鈕（或`0`）可看整個原臺中市
- 夜市以實心點加彩色範圍表示，其他市場以空心點表示；滑過或點選可看名稱、行政區、範圍面積、座標與OSM地物
- 側欄列出各夜市（依面積排序）：勾選框可個別開關每個夜市的標記、名稱與範圍（**All**／**None**一次全開或全關），**Show on map**移到該夜市；**Layers**圖層區的開關可分別切換**Night-market areas**（夜市範圍色塊與逢甲夜市虛線範圍）、**Booths**（逢甲攤位）與**Other markets**（其他市場）
- 逢甲夜市的**模擬攤位**：放大後可看到399個依珍奶指數（0–5，viridis色階：紫→綠→黃）著色的攤位方塊，滑過可看店名、編號、所在街道與分數；店名、位置與分數皆為虛構（見下方說明）
- 逢甲夜市的**珍奶指數熱度圖**：把攤位分數平滑成連續的面，使用獨立的plasma色階（紫→橘→黃），並依最低到最高值拉伸，縮小時也看得清楚；滑桿可調整平滑半徑（10–60公尺，預設25公尺），滑過可看平滑後的數值與參與平均的攤位數（見下方說明）
- 地圖左上角可收合的**圖例**：市場符號與範圍、區界，以及攤位與熱度圖的色階（各在其圖層開啟時顯示，熱度圖色階顯示目前的數值範圍）；小螢幕預設收合，指北針移到縮放按鈕下方
- **Find a Booth**查詢攤位：可用中英文店名、品項、街道或編號搜尋模擬攤位（例如`oden`、`阿明 臭豆腐`、`FJ-0316`，每個詞都須符合）；結果列出分數，點選（或按Enter選第一筆）會移到該攤位、加上圓圈標示並顯示資訊卡，必要時自動開啟逢甲夜市與攤位圖層。在地圖上點攤位也會選取；按`Esc`取消
- **垃圾桶**：OpenStreetMap上的公共垃圾桶、大型垃圾箱與資源回收點（八區內共70處），放大到街道層級後以垃圾桶圖示顯示，滑過可看類型與OSM地物（見下方說明）
- **有廁所的超商**：OpenStreetMap上標示有廁所的便利商店（八區內123家），放大到街道層級後以藍色WC標記顯示，滑過可看店名、分店與營業時間（見下方說明）
- **Find a Place**查詢地點與**Walking Route**步行路線：可用中英文搜尋臺中一帶的任何地址或地點，在地圖上查看，並設為起點（A）或終點（B）；也可從目前位置出發，或在攤位資訊卡按**Walk here**設為終點。步行路線會畫在地圖上，並列出距離、時間與逐步指引（點選步驟可放大到該處）；見下方說明
- 各行政區的夜市／市場數，點選可縮放到該區
- 頁首可切換三種風格（預設的**Boba**品牌風：標誌的棕色與米色配珍奶橘重點色；**Deck**簡報風；**Program**議程風）與三種色調（**Light**、**White**、**Dark**），選擇會記在瀏覽器中；尚未選擇時依裝置設定顯示淺色或深色
- 拖曳平移、滾輪或雙指縮放；方向鍵平移、`+`／`-`縮放、`0`回到全圖
- 圖框經緯度刻度、比例尺與指北針

舊網址`map/index.html`會自動轉到首頁。

### 市場資料（OSM）

`fetch_landmarks.py`抓取原臺中市範圍內所有`amenity=marketplace`及名稱含「夜市」的地物；`build_map.py`保留市場及名稱以「夜市」結尾、未另標類型的地物（排除同名的停車場、通道與餐廳），去除攤區分區與重複點位，並以區界裁切，共62處，其中7處夜市。OSM未繪製的市場不會出現（例如一中街）。

夜市以色塊顯示OSM上的範圍；逢甲夜市在OSM上只畫了文華路與逢甲路20巷，因此另以虛線標示**約略全範圍**（6.28公頃）：取文華路、逢甲路、福星路、逢甲路20巷（[商業周刊2015年報導](https://www.businesstoday.com.tw/article/category/80392/post/201507160040/)所列範圍）的OSM道路中心線，依`scripts/fengjia_extent.py`設定的路段裁切，兩側各外擴15 m後合併。官方未公布範圍，僅供參考。重建：`python3 scripts/fengjia_extent.py`（需`pip install shapely`及Overpass連線）。

**有廁所的超商（OSM）**：`scripts/fetch_stores.py`（標準函式庫）抓取原臺中市範圍內所有`shop=convenience`，排除被標成便利商店的蝦皮店到店取貨點（97處），輸出`data/derived/convenience_stores_osm.geojson`並保留各店的`toilets`標籤：1,026家中164家標示`yes`、66家`no`、796家未標示。`build_map.py`將八區內標示`toilets=yes`的123家放在**Stores with toilets**圖層。多數7-Eleven與全家都有提供顧客使用的廁所，但目前標示的店家不多，因此許多有廁所的超商不會出現；檔案保留未標示的店家，日後可視需要一併顯示。「Fetch OSM road network」工作流程會一併更新。

**地點搜尋與步行路線**：兩者都在瀏覽器中呼叫以OpenStreetMap資料為基礎的免費公共服務，不需API key。地點搜尋使用[Nominatim](https://nominatim.org/)，依其使用政策只在送出時查詢（每秒最多一次、不做即時建議），範圍限於臺灣及原臺中市周邊；路名與地標相當完整，門牌號碼僅部分收錄，精確地址有時只會定位到路段。步行路線使用FOSSGIS公共伺服器上的[Valhalla](https://valhalla.github.io/valhalla/)（行人模式），指引為英文、路名依OSM標示（多為中文）。這兩項服務僅供輕度合理使用，適合展示；正式上線應自行架設或改用付費服務。搜尋文字與路線點位會傳送給這些服務（資料說明中已註明）。未使用Google的搜尋與路線服務：需付費金鑰，且條款不允許在非Google地圖上顯示結果；大眾運輸路線則需要臺灣的TDX平台。

**垃圾桶（OSM）**：`scripts/fetch_bins.py`（標準函式庫）抓取原臺中市範圍內的`amenity=waste_basket`（公共垃圾桶）、`amenity=waste_disposal`（大型垃圾箱）與`amenity=recycling`（不含資源回收場等設施），輸出`data/derived/waste_bins_osm.geojson`，`build_map.py`保留八區範圍內的點位。**Garbage bins**圖層以實心圖示表示垃圾桶與垃圾箱、空心圖示表示資源回收，放大到街道層級才顯示。臺灣公共垃圾桶不多（家戶垃圾交由垃圾車收運），OSM的繪製也不完整，因此只呈現已繪製的點位。「Fetch OSM road network」工作流程會一併更新。逢甲夜市另有四個由珍奶指數團隊放置的**夜市垃圾桶**，來自`data/raw/custom_bins.csv`（編號、中英文地點、經緯度、備註），位於逢甲路與文華路、福星路口、逢甲路20巷及文華路，以較大的品牌橘色圖示表示，提示中註明地點與由團隊放置；在CSV新增一列並重建即可增加。

**模擬攤位（逢甲夜市）**：目前沒有攤位資料，因此由`scripts/mock_booths.py`（標準函式庫）產生虛構攤位供設計地圖：沿逢甲夜市各街道兩側、退到車道之外（依OSM道路等級），每10.2公尺放一個3.5 × 3公尺的攤位，略過位於交叉道路上、與其他攤位太近或超出約略範圍的位置；分數在空間上群聚而非均勻分布：以2.5為基準，在市集內隨機選三個高點與三個低點（彼此相距至少120公尺，幅度±1.6–2.3分、範圍40–80公尺的高斯分布），每個攤位的珍奶指數為所在位置的場值加上強雜訊（標準差2.5）；超出0.0–5.0的抽樣會重抽而非截斷（截斷常態分布），因此兩端不會堆積，結果取到小數一位。個別攤位看起來幾乎是隨機的（與場值的相關約0.2），熱度圖則能部分呈現高分區與低分區：預設25公尺平滑後與場值的相關約0.56，40公尺約0.70，平滑半徑越大越明顯。高低點位置記錄在輸出檔的`score_field`，可用`FIELD_*`常數調整。使用固定亂數種子，重跑結果相同（共399個）。攤位數依旅遊資料常見的「約400個攤位」設定（官方未公布；逢甲大學2023年調查商圈內實際營業店家955家，含店面）。每個攤位另有虛構的中英文店名，依真實攤名常見的組合（阿＋名字、姓＋記、姓＋稱謂或地名，有時加上「古早味」「手工」等形容，再接品項）與30種夜市常見小吃產生，例如「許記正宗蔥油餅」；組合方式參考逢甲夜市美食報導（[TVBS 食尚玩家](https://supertaste.tvbs.com.tw/food/351458)、[funtime](https://www.funtime.com.tw/blog/funtime/taichung-fengjia-food-map)）與[Smile Taiwan](https://smiletaiwan.cw.com.tw/article/3000)。店名不得包含逢甲夜市真實攤位的名稱（腳本中的`REAL_STALLS`），以免隨機分數被誤認為對真實店家的評分；店名使用獨立的亂數種子，修改店名不影響分數。腳本讀取`fengjia_extent.py`一併儲存的街道中心線，輸出`data/derived/fengjia_booths_mock.geojson`；作為展示版本，頁面上的攤位不再標示「模擬」，看起來如同真實資料；頁面資料說明中保留一句說明，指出逢甲夜市的攤位配置、店名與分數僅為示意，並非實際攤位。資料仍為虛構時請保留這句說明，並避免使用真實攤名（`REAL_STALLS`），以免隨機分數被誤認為對真實店家的評分。**熱度圖**為每個2公尺網格周圍攤位分數的高斯加權平均（Nadaraya–Watson核平滑，在瀏覽器中計算），不是攤位密度，也不是產生模擬分數用的場，因此換成真實攤位資料後可直接沿用。滑桿設定核的寬度；攤位稀疏處逐漸透明，並以約略範圍裁切。色彩採用plasma色階，與攤位的viridis不同，避免兩層混淆；色階依涵蓋充足網格的最低到最高平滑值拉伸（例如25公尺時為1.7–3.5，60公尺時為1.9–3.1），熱度圖圖例會顯示目前的範圍，不同寬度之間請比較數字而非顏色。平滑會抹掉個別攤位的極端值，呈現結果也取決於所選寬度。**Boba Index heat map**與**Booths**可各自開關。

攤位依實際尺寸繪製，約4像素長時才顯示，最大縮放時約20像素。分數以viridis色階著色：多色相、亮度隨分數均勻遞增，色覺辨識障礙者也能分辨；色階從最深紫色的下一階開始，深色主題下低分仍看得見，各主題同色同分。

一般建置環境連不到Overpass API，因此由GitHub Actions抓取：**Actions → Fetch OSM road network → Run workflow**，會依序執行`fetch_roads.py`、`fetch_landmarks.py`、`locate_projects.py`，重建網站並commit結果。資料授權為ODbL 1.0，須標示「© OpenStreetMap contributors」。

### 品牌

`img/`中的標誌、橫幅與珍珠刻度由珍奶指數團隊製作，隨網站公開：方形標誌（地圖標記造型的珍奶杯）縮成頁首標誌、網站圖示與主畫面圖示；橫幅作為連結預覽圖（`og:image`）；珍珠刻度在頁面上重繪為**珍珠計量杯**：一個杯子，九顆珍珠依珍奶指數由下往上填滿（5分為全滿），用於攤位提示、資訊卡、搜尋結果與圖例。品牌色取自標誌：橘`#fd9f02`、米`#f7f0d6`、棕`#42200f`；團隊的「Boba Fengjia」概念海報另提供兩個輔助色：深綠`#183c30`與赭紅（海報為`#cc6048`，頁面為對比改用`#b8523b`，深色模式使用較亮的版本），Boba風格用於標題、眉標、分隔線、選取攤位的圓圈與小註記。頁首與連結預覽的「Taste a deeper Taichung／品味更深的臺中」、攤位資訊卡的「Not just a score — a story.／不只是分數，更是故事。」，以及逢甲夜市名稱來源的註記（得名自逢甲大學，校名紀念詩人與教育家丘逢甲，1864–1912）也取自海報。海報上的數字（創立年份、學生數、攤位數、建議停留時間）尚未查證，因此未使用；**Boba**風格以這些顏色裝飾頁面，地圖上的資料色彩（攤位viridis、熱度圖plasma）在各風格中保持不變。

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
