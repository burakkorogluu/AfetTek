
Bu proje Python (Flask) tabanlı bir web uygulamasıdır. Aşağıdaki adımları takip ederek kendi bilgisayarınızda çalıştırabilirsiniz.

1️⃣ Projeyi İndirin
git clone https://github.com/burakkorogluu/AfetTek.git
cd AfetTek

2️⃣ Gerekli Kütüphaneleri Kurun
pip install flask osmnx networkx

3️⃣ Gerekli Dosyaları Kontrol Edin ⚠️
Projenin çalışması için aşağıdaki dosyaların mevcut olması gerekir:
kahramanmaras.graphml
data/copernicus_kapali_yollar.json
data/copernicus_hasarli_binalar.json

Bu dosyalar eksikse uygulama çalışmaz.

4️⃣ Uygulamayı Başlatın
python app.py

5️⃣ Tarayıcıda Açın
Uygulama çalıştıktan sonra aşağıdaki adrese gidin:
http://127.0.0.1:5000

🗺️ Kullanım
Haritaya tıklayarak başlangıç noktası seçin
Bitiş noktası seçin
“Rota Hesapla” butonuna basın
Alternatif rotaları görüntüleyin

⚠️ Notlar
İlk açılışta yol ağı yüklenirken kısa bir bekleme olabilir
İnternet bağlantısı gereklidir (harita ve API kullanımı için)
Performans kullanılan bilgisayara göre değişebilir

🛠️ Kullanılan Teknolojiler
Flask
OSMnx
NetworkX
Leaflet.js
