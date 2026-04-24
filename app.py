from flask import Flask, request, jsonify, render_template
import osmnx as ox
import networkx as nx
import math
import os
import json
import urllib.request
import urllib.parse

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Dosya yolları
# ---------------------------------------------------------------------------
COPERNICUS_YOLLAR_DOSYA  = "data/copernicus_kapali_yollar.json"
COPERNICUS_BINALAR_DOSYA = "data/copernicus_hasarli_binalar.json"
TAMPON_METRE = 80

print("Yol ağı yükleniyor...")
G = ox.load_graphml("kahramanmaras.graphml")
print("Yol ağı hazır!")

# ---------------------------------------------------------------------------
# Veri listeleri
# ---------------------------------------------------------------------------
KAPALI_YOL_GEOJSON  = None
KAPALI_YOL_KENARLAR = []

BINA_GEOJSON        = None
BINA_KENARLAR       = []

# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def haversine_metre(lat1, lng1, lat2, lng2):
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a  = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Startup'ta node koordinatlarini cache'le
_NODE_COORDS = None

def _node_coords_cache():
    global _NODE_COORDS
    if _NODE_COORDS is None:
        _NODE_COORDS = [(n, d["y"], d["x"]) for n, d in G.nodes(data=True)]
    return _NODE_COORDS


def en_yakin_node(lat, lng):
    """Cosine-düzeltmeli kare fark ile en yakın node'u bulur (scikit-learn gerekmez)."""
    min_d, yakin = float("inf"), None
    cos_lat = math.cos(math.radians(lat))
    for node, nlat, nlng in _node_coords_cache():
        dlat = nlat - lat
        dlng = (nlng - lng) * cos_lat
        dist = dlat * dlat + dlng * dlng
        if dist < min_d:
            min_d, yakin = dist, node
    return yakin


def en_yakin_kenar(lat, lng):
    """Haversine mesafesiyle en yakın kenar orta noktasını bulur."""
    min_d, yakin = float("inf"), None
    for u, v, _ in G.edges(data=True):
        un, vn = G.nodes[u], G.nodes[v]
        olat = (un["y"] + vn["y"]) / 2
        olng = (un["x"] + vn["x"]) / 2
        dist = haversine_metre(lat, lng, olat, olng)
        if dist < min_d:
            min_d = dist
            yakin = (u, v, un["y"], un["x"], vn["y"], vn["x"])
    return yakin


def rota_mesafe_hesapla(rota):
    """Toplam mesafeyi orijinal MultiDiGraph üzerinden hesaplar."""
    toplam = 0
    for i in range(len(rota) - 1):
        u, v = rota[i], rota[i + 1]
        if G.has_edge(u, v):
            toplam += min(d.get("length", 0) for d in G[u][v].values())
        else:
            n1, n2 = G.nodes[u], G.nodes[v]
            toplam += haversine_metre(n1["y"], n1["x"], n2["y"], n2["x"])
    return toplam


def rota_hasar_skoru(rota, hasar_set):
    """Rotanın hasarlı kenarlardan kaç tanesinden geçtiğini sayar."""
    skor = 0
    for i in range(len(rota) - 1):
        if (rota[i], rota[i+1]) in hasar_set or \
           (rota[i+1], rota[i]) in hasar_set:
            skor += 1
    return skor


def rota_to_geojson(rota, renk="blue"):
    coords = [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in rota]
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {"renk": renk}
        }]
    }


def multidigraph_to_digraph():
    """MultiDiGraph'ı DiGraph'a çevirir; paralel kenarlar arasından en kısayı seçer."""
    G_di = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        w = data.get("length", 1)
        if not G_di.has_edge(u, v) or G_di[u][v].get("length", float("inf")) > w:
            G_di.add_edge(u, v, **data)
    return G_di


# ---------------------------------------------------------------------------
# Copernicus yol verisi yükleme
# ---------------------------------------------------------------------------

def kapali_yollari_yukle():
    global KAPALI_YOL_GEOJSON, KAPALI_YOL_KENARLAR

    if not os.path.exists(COPERNICUS_YOLLAR_DOSYA):
        print(f"UYARI: {COPERNICUS_YOLLAR_DOSYA} bulunamadı!")
        return

    with open(COPERNICUS_YOLLAR_DOSYA, encoding="utf-8") as f:
        geojson = json.load(f)

    KAPALI_YOL_GEOJSON = geojson

    kapali = set()
    for feat in geojson.get("features", []):
        coords = feat["geometry"]["coordinates"]
        for i in range(len(coords) - 1):
            lng1, lat1 = coords[i]
            lng2, lat2 = coords[i + 1]
            mid_lat = (lat1 + lat2) / 2
            mid_lng = (lng1 + lng2) / 2
            k = en_yakin_kenar(mid_lat, mid_lng)
            if k:
                kapali.add((k[0], k[1]))

    KAPALI_YOL_KENARLAR = list(kapali)
    print(f"Copernicus yol verisi: {len(geojson['features'])} hasarlı yol → "
          f"{len(kapali)} graf kenarı kapatıldı.")


# ---------------------------------------------------------------------------
# Copernicus bina verisi yükleme
# ---------------------------------------------------------------------------

def binalari_yukle():
    global BINA_GEOJSON, BINA_KENARLAR

    if not os.path.exists(COPERNICUS_BINALAR_DOSYA):
        print(f"UYARI: {COPERNICUS_BINALAR_DOSYA} bulunamadı!")
        return

    with open(COPERNICUS_BINALAR_DOSYA, encoding="utf-8") as f:
        geojson = json.load(f)

    BINA_GEOJSON = geojson

    kenar_ortalari = {
        (u, v): ((G.nodes[u]["y"] + G.nodes[v]["y"]) / 2,
                 (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2)
        for u, v, _ in G.edges(data=True)
    }

    agirlik = {"Destroyed": 3, "Damaged": 2, "Possibly damaged": 1}
    kapali = set()
    for feat in geojson.get("features", []):
        coords = feat["geometry"]["coordinates"]
        blat, blng = coords[1], coords[0]
        tampon = TAMPON_METRE * agirlik.get(
            feat["properties"].get("damage_gra", ""), 1)
        for (u, v), (olat, olng) in kenar_ortalari.items():
            if (u, v) not in kapali:
                if haversine_metre(blat, blng, olat, olng) <= tampon:
                    kapali.add((u, v))

    BINA_KENARLAR = list(kapali)
    print(f"Copernicus bina verisi: {len(geojson['features'])} bina → "
          f"{len(kapali)} graf kenarı kapatıldı.")


# ---------------------------------------------------------------------------
# Uygulama başlangıcı
# ---------------------------------------------------------------------------

print("Node koordinatları cache'leniyor...")
_node_coords_cache()
print(f"Cache hazır: {len(_NODE_COORDS)} node")

print("Copernicus kapalı yol verisi yükleniyor...")
kapali_yollari_yukle()

print("Copernicus bina hasar verisi yükleniyor...")
binalari_yukle()


# ---------------------------------------------------------------------------
# Flask rotaları
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/kapali_yollar")
def kapali_yollar():
    if not KAPALI_YOL_GEOJSON:
        return jsonify({"durum": "hata", "mesaj": "Kapalı yol verisi yüklenemedi."})
    return jsonify({
        "durum": "ok",
        "yol_sayisi": len(KAPALI_YOL_GEOJSON["features"]),
        "kapali_kenar_sayisi": len(KAPALI_YOL_KENARLAR),
        "geojson": KAPALI_YOL_GEOJSON
    })


@app.route("/copernicus_binalar")
def copernicus_binalar():
    if not BINA_GEOJSON:
        return jsonify({"durum": "hata", "mesaj": "Bina verisi yüklenemedi."})
    from collections import Counter
    c = Counter(
        f["properties"].get("damage_gra", "")
        for f in BINA_GEOJSON["features"]
    )
    return jsonify({
        "durum": "ok",
        "bina_sayisi": len(BINA_GEOJSON["features"]),
        "kapali_kenar_sayisi": len(BINA_KENARLAR),
        "istatistik": dict(c),
        "geojson": BINA_GEOJSON
    })


@app.route("/yakin_yol", methods=["POST"])
def yakin_yol():
    try:
        v = request.json
        k = en_yakin_kenar(v["lat"], v["lng"])
        return jsonify({
            "durum": "ok",
            "kenar": [k[0], k[1]],
            "koordinatlar": [[k[2], k[3]], [k[4], k[5]]]
        })
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)})


@app.route("/rota", methods=["POST"])
def rota_hesapla():
    try:
        veri       = request.json
        bas_node   = en_yakin_node(veri["baslangic"]["lat"], veri["baslangic"]["lng"])
        bit_node   = en_yakin_node(veri["bitis"]["lat"],     veri["bitis"]["lng"])
        yol_aktif  = veri.get("yol_aktif",  False)
        bina_aktif = veri.get("bina_aktif", False)
        kapali_manuel = veri.get("kapali", [])

        # ── Kapalı kenar seti (her iki yön) - orijinal liste kaybolmasın ──
        kapali_set = set()
        for k in kapali_manuel:
            u, v = int(k[0]), int(k[1])
            kapali_set.add((u, v))
            kapali_set.add((v, u))
        if yol_aktif:
            for u, v in KAPALI_YOL_KENARLAR:
                kapali_set.add((int(u), int(v)))
                kapali_set.add((int(v), int(u)))
        if bina_aktif:
            for u, v in BINA_KENARLAR:
                kapali_set.add((int(u), int(v)))
                kapali_set.add((int(v), int(u)))

        # ── Hasar seti: kapalı yollar + hasarlı binalar (skorlama için) ──
        hasar_set = set()
        for u, v in KAPALI_YOL_KENARLAR:
            hasar_set.add((int(u), int(v)))
            hasar_set.add((int(v), int(u)))
        for u, v in BINA_KENARLAR:
            hasar_set.add((int(u), int(v)))
            hasar_set.add((int(v), int(u)))

        # ── Graf builder ──
        def kur_graf(sil=True):
            Gd = multidigraph_to_digraph()
            if sil:
                # Kapalı kenarları tamamen sil
                for u, v in list(Gd.edges()):
                    if (u, v) in kapali_set:
                        Gd.remove_edge(u, v)
            else:
                # Kapalı kenarlara çok yüksek ağırlık ver (silme)
                for u, v in Gd.edges():
                    if (u, v) in kapali_set:
                        Gd[u][v]["length"] = Gd[u][v].get("length", 100) * 9999
            return Gd

        G_temel = kur_graf(sil=True)

        # Bağlantı yoksa fallback
        uyari_genel = None
        try:
            bagli = bas_node in G_temel and bit_node in G_temel and \
                    nx.has_path(G_temel, bas_node, bit_node)
        except Exception:
            bagli = False

        if not bagli:
            G_temel = kur_graf(sil=False)
            uyari_genel = "Kapalı yollar nedeniyle tamamen kaçınılabilen alternatif rota gösteriliyor."

        # ── 3 Profil ──

        # En Kısa: kapalı kenarlar zaten çıkarıldı
        G_kisa = G_temel

        # En Güvenli: hasarlı kenarları da çıkar
        G_guvenli = G_temel.copy()
        for u, v in list(G_guvenli.edges()):
            if (u, v) in hasar_set:
                G_guvenli.remove_edge(u, v)
        try:
            if not (bas_node in G_guvenli and bit_node in G_guvenli and
                    nx.has_path(G_guvenli, bas_node, bit_node)):
                G_guvenli = G_kisa
        except Exception:
            G_guvenli = G_kisa

        # Dengeli: hasarlı kenarlara 5x ceza
        HASAR_CEZA = 5.0
        G_dengeli = G_temel.copy()
        for u, v in G_dengeli.edges():
            base = G_dengeli[u][v].get("length", 1)
            G_dengeli[u][v]["length_w"] = base * HASAR_CEZA if (u, v) in hasar_set else base

        # ── Rota bul ──
        def bul_rota(graf, agirlik="length"):
            try:
                return nx.shortest_path(graf, bas_node, bit_node, weight=agirlik)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                return None

        rota_kisa    = bul_rota(G_kisa,    "length")
        rota_guvenli = bul_rota(G_guvenli, "length") or rota_kisa
        rota_dengeli = bul_rota(G_dengeli, "length_w") or rota_kisa

        if not rota_kisa:
            return jsonify({"durum": "hata",
                            "mesaj": "Seçilen iki nokta arasında rota bulunamadı. Farklı noktalar deneyin."})

        # ── Metrik hesapla ──
        def aday_yap(rota):
            m = rota_mesafe_hesapla(rota) or float(len(rota))
            h = rota_hasar_skoru(rota, hasar_set)
            return {"rota": rota, "mesafe_m": m, "hasar": h}

        en_kisa_aday    = aday_yap(rota_kisa)
        en_guvenli_aday = aday_yap(rota_guvenli)
        dengeli_aday    = aday_yap(rota_dengeli)

        def metrik(aday):
            mesafe_km = round(aday["mesafe_m"] / 1000, 2)
            sure      = round((mesafe_km / 40) * 60)
            return mesafe_km, sure, aday["hasar"]

        m_k, s_k, h_k = metrik(en_kisa_aday)
        m_g, s_g, h_g = metrik(en_guvenli_aday)
        m_d, s_d, h_d = metrik(dengeli_aday)

        degerler = [(m_k, h_k), (m_g, h_g), (m_d, h_d)]
        mx_m = max(v[0] for v in degerler) or 1
        mx_h = max(v[1] for v in degerler) or 1
        skorlar = [0.4*(m/mx_m) + 0.6*(h/mx_h) for m, h in degerler]
        opt_id  = ["en_kisa", "en_guvenli", "dengeli"][skorlar.index(min(skorlar))]

        rotalar = [
            {
                "id": "en_kisa", "isim": "En Kısa Rota", "renk": "#2980b9",
                "mesafe": m_k, "sure": s_k, "hasar": h_k,
                "uyari": uyari_genel,
                "geojson": rota_to_geojson(en_kisa_aday["rota"], "#2980b9"),
                "optimal": opt_id == "en_kisa"
            },
            {
                "id": "en_guvenli", "isim": "En Güvenli Rota", "renk": "#27ae60",
                "mesafe": m_g, "sure": s_g, "hasar": h_g,
                "uyari": uyari_genel,
                "geojson": rota_to_geojson(en_guvenli_aday["rota"], "#27ae60"),
                "optimal": opt_id == "en_guvenli"
            },
            {
                "id": "dengeli", "isim": "Dengeli Rota", "renk": "#8e44ad",
                "mesafe": m_d, "sure": s_d, "hasar": h_d,
                "uyari": uyari_genel,
                "geojson": rota_to_geojson(dengeli_aday["rota"], "#8e44ad"),
                "optimal": opt_id == "dengeli"
            }
        ]

        return jsonify({
            "durum": "ok",
            "rotalar": rotalar,
            "optimal": opt_id,
            "kapali_kenar_sayisi": len(kapali_set)
        })

    except nx.NetworkXNoPath:
        return jsonify({"durum": "hata", "mesaj": "Bu iki nokta arasında yol bulunamadı."})
    except Exception as e:
        import traceback
        print("HATA:", traceback.format_exc())
        return jsonify({"durum": "hata", "mesaj": str(e)})


@app.route("/yakin_yerler", methods=["POST"])
def yakin_yerler():
    try:
        veri    = request.json
        lat     = veri["lat"]
        lng     = veri["lng"]
        yaricap = veri.get("yaricap", 2000)

        overpass_sorgu = f"""
[out:json][timeout:25];
(
  node["amenity"="hospital"](around:{yaricap},{lat},{lng});
  way["amenity"="hospital"](around:{yaricap},{lat},{lng});
  node["amenity"="pharmacy"](around:{yaricap},{lat},{lng});
  node["amenity"="fire_station"](around:{yaricap},{lat},{lng});
  way["amenity"="fire_station"](around:{yaricap},{lat},{lng});
  node["amenity"="police"](around:{yaricap},{lat},{lng});
  way["amenity"="police"](around:{yaricap},{lat},{lng});
  node["amenity"="clinic"](around:{yaricap},{lat},{lng});
  node["amenity"="doctors"](around:{yaricap},{lat},{lng});
);
out center;
"""
        form_verisi = urllib.parse.urlencode({"data": overpass_sorgu}).encode("utf-8")
        req = urllib.request.Request(
            "https://overpass-api.de/api/interpreter",
            data=form_verisi,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "AfetRotaSistemi/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            sonuc = json.loads(resp.read().decode("utf-8"))

        yerler = []
        for eleman in sonuc.get("elements", []):
            if eleman["type"] == "node":
                e_lat = eleman.get("lat")
                e_lng = eleman.get("lon")
            else:
                center = eleman.get("center", {})
                e_lat  = center.get("lat")
                e_lng  = center.get("lon")

            if e_lat is None or e_lng is None:
                continue

            etiketler = eleman.get("tags", {})
            tur  = etiketler.get("amenity", "bilinmiyor")
            isim = (etiketler.get("name") or etiketler.get("name:tr")
                    or etiketler.get("name:en") or tur.capitalize())
            mesafe = round(haversine_metre(lat, lng, e_lat, e_lng) / 1000, 2)

            yerler.append({
                "isim":      isim,
                "tur":       tur,
                "lat":       e_lat,
                "lng":       e_lng,
                "mesafe_km": mesafe,
                "adres":     (etiketler.get("addr:street", "") + " " +
                              etiketler.get("addr:housenumber", "")).strip(),
                "telefon":   etiketler.get("phone", etiketler.get("contact:phone", "")),
            })

        yerler.sort(key=lambda x: x["mesafe_km"])
        return jsonify({"durum": "ok", "yerler": yerler})

    except Exception as e:
        print("YAKIN_YERLER HATA:", e)
        return jsonify({"durum": "hata", "mesaj": str(e)})


if __name__ == "__main__":
    app.run(debug=False)