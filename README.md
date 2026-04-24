 AfetTek 
 
## 📁 Proje Yapısı

```
AfetTek/
├── app.py                          # Flask backend, rota algoritması
├── kahramanmaras.graphml           # OSMnx yol ağı (önceden indirilmiş)
├── veri.py                         # Copernicus verisi işleme scripti
├── templates/
│   └── index.html                  # Leaflet.js harita arayüzü
├── data/
│   ├── copernicus_kapali_yollar.json   # 134 hasarlı yol (Copernicus EMS)
│   └── copernicus_hasarli_binalar.json # 927 hasarlı bina (Copernicus EMS)
└── cache/                          # OSMnx önbellek
```

---

## ⚙️ Kurulum ve Çalıştırma

### 1. Repoyu klonlayın
```bash
git clone https://github.com/burakkorogluu/AfetTek.git
cd AfetTek
```

### 2. Gerekli kütüphaneleri kurun
```bash
pip install flask osmnx networkx
```

### 3. Uygulamayı başlatın
```bash
python app.py
```

İlk başlatmada terminal şu çıktıları verir (normaldir, birkaç saniye sürebilir):
```
Yol ağı yükleniyor...
Yol ağı hazır!
Copernicus kapalı yol verisi yükleniyor...
Copernicus yol verisi: 134 hasarlı yol → XXX graf kenarı kapatıldı.
Copernicus bina hasar verisi yükleniyor...
Copernicus bina verisi: 927 bina → XXX graf kenarı kapatıldı.
```

### 4. Tarayıcıda açın
```
http://127.0.0.1:5000
```

---
## ✨ Özellikler

| Özellik | Açıklama |
|---|---|
| 🛰️ **Copernicus EMS entegrasyonu** | 134 kapalı yol + 927 hasarlı bina (Destroyed / Damaged / Possibly Damaged) |
| 🗺️ **3 Alternatif Rota** | En Kısa · En Güvenli · Dengeli — her biri ayrı renk ve skor kartıyla |
| ⭐ **Optimal Rota Önerisi** | Mesafe × 0.4 + Hasar Skoru × 0.6 normalize formülüyle otomatik seçim |
| 🚧 **Manuel Kapalı Yol** | Haritaya tıklayarak anlık yol kapatma |
| 📍 **Yakın Acil Noktalar** | OpenStreetMap Overpass API ile hastane, eczane, itfaiye, polis, klinik |
| 🗺️ **Yerden Rota** | Yakın yer listesinden doğrudan "Bu Yere Rota Oluştur" |

---
## 🗺️ Kullanım Kılavuzu

### Temel Rota Hesaplama
1. Haritaya **ilk tıklama** → Başlangıç noktası (mavi pin)
2. Haritaya **ikinci tıklama** → Bitiş noktası (mavi pin)
3. **"Rota Hesapla"** butonuna bas
4. Sağ panelde 3 rota kartı belirir; **⭐ Önerilen** etiketi optimal rotayı gösterir
5. Karta tıkla → Haritada o rotaya odaklan

### Copernicus Hasar Katmanları
- **🚫 Copernicus Kapalı Yollar** → 134 hasarlı yolu kırmızı kesik çizgiyle göster / rota hesaplamada bu yolları kapat
- **🏚️ Copernicus Hasarlı Binalar** → 927 binayı hasar derecesine göre renklendir (🔴 Yıkık · 🟠 Hasarlı · 🟡 Muhtemel)

### Manuel Kapalı Yol
1. **"Manuel Kapalı Yol Ekle"** butonuna bas (imleç artı işaretine döner)
2. Kapatmak istediğin yola tıkla → turuncu çizgiyle işaretlenir
3. **"Eklemeyi Bitir"** ile moda son ver

### Yakın Acil Noktalar
1. **"📍 Yakın Hastane / Eczane"** butonuna bas
2. Arama yarıçapını ayarla (varsayılan: 2 km)
3. Kategori filtrelerinden seç: Hastane · Eczane · İtfaiye · Polis · Klinik
4. **"Bu Yere Rota Oluştur"** → o konuma 3 alternatif rota otomatik hesaplanır

---

## 🧠 Algoritma

### Rota Motoru
- **Graf tipi:** OSMnx `MultiDiGraph` → hesaplama için `DiGraph`'a dönüştürülür (paralel kenarlarda en kısa seçilir)
- **Algoritma:** Yen's k-shortest paths (`nx.shortest_simple_paths`) — en kısa rotanın 2.5 katına kadar olan adaylar arasından en fazla 12 rota üretilir
- **Mesafe ölçümü:** Her aday için orijinal graf üzerinden gerçek km hesaplanır (ağırlık şişmesi olmaz)

### 3 Rota Profili

| Profil | Seçim Kriteri | Renk |
|---|---|---|
| En Kısa | `min(mesafe_m)` | 🔵 Mavi |
| En Güvenli | `min(hasar_kesimi, sonra mesafe)` | 🟢 Yeşil |
| Dengeli | `min(0.45 × mesafe_norm + 0.55 × hasar_norm)` | 🟣 Mor |




## 🛠️ Kullanılan Teknolojiler

| Katman | Teknoloji |
|---|---|
| Backend | Python 3 · Flask |
| Yol Ağı | OSMnx · NetworkX |
| Hasar Verisi | Copernicus EMS EMSR648 AOI04 |
| Yakın Yerler | OpenStreetMap Overpass API |
| Harita | Leaflet.js · OpenStreetMap |

---

## 📡 Veri Kaynakları

- **Copernicus Emergency Management Service** — EMSR648 Kahramanmaraş Depremi Aktivasyonu  
  `data/copernicus_kapali_yollar.json` · `data/copernicus_hasarli_binalar.json`
- **OpenStreetMap** — Yol ağı ve POI verileri
- **Overpass API** — Gerçek zamanlı acil nokta sorgulaması

---

## ⚠️ Gereksinimler

- Python 3.8+
- İnternet bağlantısı (harita karolarını ve Overpass API'yi çeker)
- Tüm dosyalar repoda mevcuttur, ekstra indirme gerekmez

---

