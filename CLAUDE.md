# Platform Oyunu — Proje Hafızası

## Proje
- Python + pygame-ce ile 2D platform (zıplama) oyunu.
- MOBİL oyun olacak: ekran dikey (telefon gibi, 400x720) ve bölüm YUKARI doğru ilerler
  (Doodle Jump / Icy Tower tarzı tırmanma). Kullanıcı yana kayan haritayı istemedi.
- Kullanıcı hiç kod yazmamış: kodu Claude yazar, kullanıcı test eder ve geri bildirim verir.
- Kullanıcıyla Türkçe konuş, teknik terimleri basitçe açıkla.
- Çalıştırma: `python main.py` (ESC veya pencereyi kapatmak oyundan çıkar).

## Çalışma kuralları
- Her aşama sonunda oyun çalışır durumda olmalı.
- Kullanıcının isteği: HER eklemeden/değişiklikten sonra (aşamanın bitmesini bekleme) git commit at
  ve hemen `git push` ile GitHub'a gönder. Kullanıcıya ayrıca sorma; bu kalıcı izin.
  Depo: https://github.com/erenalbayrakk04/platform, dal `main`. Commit mesajları Türkçe ve kısa.
- Ayarlanabilir sayılar (hız, zıplama gücü, renkler) `settings.py` içinde dursun.
- Önce oyun çalışsın, sonra güzelleşsin: resim/ses 8. aşamaya kadar yok, renkli kareler kullan.

## Dosyalar
- `main.py` — oyun döngüsü (olaylar → güncelleme → çizim)
- `settings.py` — tüm ayarlar
- `player.py` — karakter (`Player` sprite'ı; ok tuşları / A-D ile hareket, Boşluk/Yukarı/W ile
  zıplama; yerçekimi `velocity_y` + ondalıklı `pos_y`; `update(tiles)` yatay ve dikey
  çarpışmayı ayrı çözer; `on_ground` ayağın 1 px altını kontrol eder; `respawn()` başlangıca döndürür;
  `Player(x, y, level_width)` — bölüm kenarından dışarı çıkamaz)
- `level.py` — `LEVEL_MAP` metin haritası (`#` katı blok, `-` ince platform (o da katı;
  kullanıcı alttan içinden geçilmesini İSTEMEDİ, kafa çarpmalı),
  `.` boş, `P` başlangıç; 40 px kareler, şu an 10x46 = 400x1840 px, en alt satır tam zemin,
  karakter alttan başlayıp tepedeki `######`'e tırmanır), `Tile` ve `Platform` sprite'ları,
  haritayı okuyan `Level` sınıfı (`tiles` = çarpılan her şey, bloklar + ince platformlar;
  `width`/`height` piksel cinsinden)
- `camera.py` — `Camera(level_height)`: DİKEYDE yumuşak takip (`CAMERA_SMOOTHNESS`), karakter
  ekranın `CAMERA_PLAYER_Y` oranında (biraz altta) durur, bölüm üst/alt kenarında durur;
  `apply(rect)` bölüm konumunu ekran konumuna çevirir. Tüm çizim `main.py`'de kamera üzerinden.
- Bölümün altından düşerse (`rect.top > level.height`) şimdilik `respawn()`; can sistemi Aşama 6'da.
- Zıplama ~133 px (3 blok = 120 px'e çıkılabilir), yatayda ~4 blok gidilebilir; harita
  tasarlarken basılan yüzeyler arası dikey fark en fazla 3 satır olsun. Platformlar katı olduğu
  için bir üst platform tam tepede olmasın; yana kaydırılmış olsun ki zıplayıp üstüne çıkılabilsin.
- `assets/` — resim ve sesler (Aşama 8'de eklenecek)

## Yol haritası
- [x] 0. Kurulum — boş pencere açılıyor
- [x] 1. Karakter — kare, ok tuşlarıyla sağ-sol hareket
- [x] 2. Fizik — yerçekimi, boşlukla zıplama, zemin
- [x] 3. Platformlar — havada platformlar, üzerine çıkma
- [x] 4. Kamera & bölüm — dikey (yukarı doğru) uzun harita, dikey kamera takibi, ince platformlar
- [ ] 5. Toplanabilir — altın, puan göstergesi
- [ ] 6. Düşman & can — yürüyen düşman, can, ölme/yeniden başlama
- [ ] 7. Bitiş — bayrak, kazandın ekranı, başlangıç menüsü
- [ ] 8. Güzelleştirme — sprite, animasyon, ses/müzik, dokunmatik kontroller (ekran butonları)
- [ ] 9. Ekstra — yeni bölümler, telefonda çalışır çıktı (ör. pygbag ile tarayıcıda)

## Sıradaki adım
Aşama 5: haritaya `C` (altın) karakteri ekle (tırmanma yolu boyunca, platformların üstüne),
altınlar toplanınca kaybolsun ve puan artsın; ekranın üst köşesinde puan yazısı (kameradan
bağımsız çizilir). Puan değeri `settings.py`'de.
