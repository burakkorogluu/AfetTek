import osmnx as ox

print("Kahramanmaras yol agi indiriliyor...")
G = ox.graph_from_place("Kahramanmaraş, Turkey", network_type="drive")
print("Indirildi! Diske kaydediliyor...")
ox.save_graphml(G, "kahramanmaras.graphml")
print("Tamamlandi! kahramanmaras.graphml dosyasi olusturuldu.")