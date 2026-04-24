Bu proje, Python (Flask) tabanlı bir web uygulamasıdır. Afet durumlarında en uygun rotayı hesaplamak için geliştirilmiştir.

📦 1. Projeyi İndirin
git clone https://github.com/burakkorogluu/AfetTek.git
cd AfetTek
🧰 2. Gerekli Kütüphaneleri Kurun
pip install flask osmnx networkx
⚠️ 3. Gerekli Dosyalar

Uygulamanın düzgün çalışması için aşağıdaki dosyaların proje içinde mevcut olması gerekir:

📁 kahramanmaras.graphml
📁 data/
   ├── copernicus_kapali_yollar.json
   └── copernicus_hasarli_binalar.json

❗ Bu dosyalar eksikse uygulama çalışmaz.

🚀 4. Uygulamayı Başlatın
python app.py
🌐 5. Tarayıcıda Açın

Uygulama çalıştıktan sonra şu adresi açın:

http://127.0.0.1:5000
🗺️ Kullanım
🖱️ Haritaya tıkla → Başlangıç noktası seç
🖱️ Tekrar tıkla → Bitiş noktası seç
🧭 "Rota Hesapla" butonuna bas
📍 Alternatif rotaları görüntüle
⚠️ Önemli Notlar
⏳ İlk açılışta yol ağı yüklenirken kısa bir bekleme olabilir
🌐 İnternet bağlantısı gereklidir (harita ve API servisleri için)
💻 Performans, kullanılan bilgisayara göre değişebilir
🛠️ Kullanılan Teknolojiler
🐍 Flask – Web framework
🗺️ OSMnx – Yol ağı analizi
📊 NetworkX – Grafik algoritmaları
🗺️ Leaflet.js – Harita arayüzü
🎯 Proje Amacı

Afet durumlarında:

En hızlı rotayı hesaplamak
Kapalı yolları hesaba katmak
Hasarlı binalardan kaçınmak
Alternatif güzergahlar sunmak
