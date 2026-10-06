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
- OYUN SONSUZ (kullanıcı kararı, Doodle Jump tarzı): harita elle yazılmış küçük PARÇALARIN rastgele
  üst üste dizilmesiyle oluşur; ekranın üstüne yeni parça eklenir, çok altta kalan parça silinir.
- `chunks.py` — `START_CHUNK` (zemin + `P`) ve `CHUNKS` listesi; her parça
  `{"entry": "L"/"R", "exit": "L"/"R", "difficulty": 1-3, "rows": [...]}`, 10 karakter genişlik
  (`#` katı blok, `-` ince platform — o da katı; kullanıcı alttan içinden geçilmesini İSTEMEDİ, kafa
  çarpmalı; `.` boş). Birleşme kuralı: en alt satır boş, sondan ikinci satır giriş (sadece `-`, giriş
  tarafında; sol = sütun 0-4 ve 4 dolu, sağ = 5-9 ve 5 dolu), en üst satır çıkış (aynı kural). Çıkışı
  sol olanın üstüne girişi sağ olan gelir → birleşmede 2 satır fark, üst üste binme yok.
  `check_chunk` yanlış parçada oyun açılırken hata verir. Yeni parça eklerken her iki giriş
  tarafı için her zorlukta parça olsun.
- `level.py` — `Tile`, `Platform` sprite'ları ve `Level(seed)`: y=0 zeminin altı, yukarı çıktıkça
  y EKSİ. `add_chunk`, `pick_chunk` (giriş = önceki çıkışın tersi, zorluk ≤ 1 + yükseklik //
  `DIFFICULTY_STEP`), `update(view_top, view_bottom)` (`GENERATE_AHEAD` kadar yukarıyı doldurur,
  `REMOVE_BELOW`'dan aşağıdaki parçaları siler). `tiles` = çarpılan her şey, `bottom` = en alttaki
  parçanın altı, `width` piksel.
- `camera.py` — `Camera()`: DİKEYDE yumuşak takip (`CAMERA_SMOOTHNESS`), karakter ekranın
  `CAMERA_PLAYER_Y` oranında durur; yukarısı sınırsız, aşağıda `level.bottom`'da durur;
  `follow(rect, level_bottom)`, `top`/`bottom`, `apply(rect)`. Tüm çizim `main.py`'de kamera üzerinden.
- `main.py` → `new_game()` yeni rastgele bölüm + karakter + kamera kurar. `level.bottom`'ın altına
  düşerse şimdilik `new_game()` (yeni harita); can sistemi Aşama 6'da.
- Parçaların çıkılabilirliği gerçek fizikle test edildi (her parça içi + tüm birleşmeler): yeni
  parça eklenince aynı tür bir test (Player'ı sahte tuşlarla çalıştıran BFS) tekrar yapılmalı.
- Zıplama ~133 px (3 blok = 120 px'e çıkılabilir), yatayda ~4 blok gidilebilir; parça
  tasarlarken basılan yüzeyler arası dikey fark en fazla 3 satır olsun. Platformlar katı olduğu
  için bir üst platform tam tepede olmasın; yana kaydırılmış olsun ki zıplayıp üstüne çıkılabilsin.
- `assets/` — resim ve sesler (Aşama 8'de eklenecek)

## Yol haritası
- [x] 0. Kurulum — boş pencere açılıyor
- [x] 1. Karakter — kare, ok tuşlarıyla sağ-sol hareket
- [x] 2. Fizik — yerçekimi, boşlukla zıplama, zemin
- [x] 3. Platformlar — havada platformlar, üzerine çıkma
- [x] 4. Kamera & bölüm — dikey (yukarı doğru) uzun harita, dikey kamera takibi, ince platformlar
- [x] 4b. Sonsuz parça sistemi — rastgele parçalar, geride kalanlar silinir, yükseldikçe zorlaşır
- [ ] 5. Toplanabilir — altın, puan göstergesi (puan = tırmanılan yükseklik + altınlar)
- [ ] 6. Düşman & can — yürüyen düşman, can, ölme/yeniden başlama
- [ ] 7. Oyun sonu — bayrak YOK (sonsuz): kaybettin ekranı + en yüksek skor, başlangıç menüsü
- [ ] 8. Güzelleştirme — sprite, animasyon, ses/müzik, dokunmatik kontroller (ekran butonları)
- [ ] 9. Ekstra — yeni parçalar, telefonda çalışır çıktı (ör. pygbag ile tarayıcıda)

## Sıradaki adım
Aşama 5: parçalara (`chunks.py`) `C` (altın) karakteri ekle (platformların üstüne; `check_chunk`
ve `Level.add_chunk` `C`'yi tanısın, giriş/çıkış satırı kuralını bozmasın). Altınlar toplanınca
kaybolsun, puan artsın; tırmanılan yükseklik de puana eklensin. Ekranın üst köşesinde puan yazısı
(kameradan bağımsız çizilir). Puan değerleri `settings.py`'de. Silinen parçanın altınları da silinmeli.
