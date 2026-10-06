# Platform Oyunu — Proje Hafızası

## Proje
- Python + pygame-ce ile 2D platform (zıplama) oyunu.
- Kullanıcı hiç kod yazmamış: kodu Claude yazar, kullanıcı test eder ve geri bildirim verir.
- Kullanıcıyla Türkçe konuş, teknik terimleri basitçe açıkla.
- Çalıştırma: `python main.py` (ESC veya pencereyi kapatmak oyundan çıkar).

## Çalışma kuralları
- Her aşama sonunda oyun çalışır durumda olmalı; kullanıcı denedikten sonra git commit at.
- Ayarlanabilir sayılar (hız, zıplama gücü, renkler) `settings.py` içinde dursun.
- Önce oyun çalışsın, sonra güzelleşsin: resim/ses 8. aşamaya kadar yok, renkli kareler kullan.

## Dosyalar
- `main.py` — oyun döngüsü (olaylar → güncelleme → çizim)
- `settings.py` — tüm ayarlar
- `player.py` — karakter (`Player` sprite'ı; ok tuşları / A-D ile hareket, Boşluk/Yukarı/W ile
  zıplama; yerçekimi `velocity_y` + ondalıklı `pos_y` ile; zemin şimdilik sabit `GROUND_HEIGHT`)
- `level.py` — bölüm/platformlar (Aşama 3'te eklenecek)
- `assets/` — resim ve sesler (Aşama 8'de eklenecek)

## Yol haritası
- [x] 0. Kurulum — boş pencere açılıyor
- [x] 1. Karakter — kare, ok tuşlarıyla sağ-sol hareket
- [x] 2. Fizik — yerçekimi, boşlukla zıplama, zemin
- [ ] 3. Platformlar — havada platformlar, üzerine çıkma
- [ ] 4. Kamera & bölüm — ekrandan geniş harita, kamera takibi
- [ ] 5. Toplanabilir — altın, puan göstergesi
- [ ] 6. Düşman & can — yürüyen düşman, can, ölme/yeniden başlama
- [ ] 7. Bitiş — bayrak, kazandın ekranı, başlangıç menüsü
- [ ] 8. Güzelleştirme — sprite, animasyon, ses/müzik
- [ ] 9. Ekstra — yeni bölümler, .exe çıktısı

## Sıradaki adım
Aşama 3: `level.py` oluştur, havada platformlar ekle. `player.py`'deki sabit zemin kontrolünü
platform çarpışmasıyla değiştir (zemin de bir platform olsun; yatay ve dikey çarpışmayı ayrı çöz).
