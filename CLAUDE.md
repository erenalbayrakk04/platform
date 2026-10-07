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
- Görseller ve sesler dosya DEĞİL, kodla üretiliyor (kullanıcı kararı, Aşama 8): piksel sanatı
  `art.py`'de, retro sesler/müzik `sound.py`'de. Renkler settings.py'deki ana renklerden gelir.

## Dosyalar
- `main.py` — oyun döngüsü (olaylar → güncelleme → çizim)
- `settings.py` — tüm ayarlar
- `player.py` — karakter (`Player` sprite'ı; `update(tiles, controls)` — tuşları kendisi okumaz,
  `controls.left/right/jump` alır; `jumped` = bu karede zıpladı (ses için); `animate(dx)` resim seçer
  (idle/walk1/walk2/jump × `facing`); yerçekimi `velocity_y` + ondalıklı `pos_y`; yatay ve dikey
  çarpışmayı ayrı çözer; `on_ground` ayağın 1 px altını kontrol eder; `respawn()` başlangıca döndürür;
  `Player(x, y, level_width)` — bölüm kenarından dışarı çıkamaz)
- OYUN SONSUZ (kullanıcı kararı, Doodle Jump tarzı): harita elle yazılmış küçük PARÇALARIN rastgele
  üst üste dizilmesiyle oluşur; ekranın üstüne yeni parça eklenir, çok altta kalan parça silinir.
- `chunks.py` — `START_CHUNK` (zemin + `P`) ve `CHUNKS` listesi; her parça
  `{"entry": "L"/"R", "exit": "L"/"R", "difficulty": 1-3, "rows": [...]}`, 10 karakter genişlik
  (`#` katı blok, `-` ince platform — o da katı; kullanıcı alttan içinden geçilmesini İSTEMEDİ, kafa
  çarpmalı; `K` kırılan platform — ince, katı, giriş/çıkış satırında olmaz, üstüne yay/düşman konmaz
(`SOLID = "#-K"`, `STEADY = "#-"`); `.` boş; `C` altın — bir platformun hemen üstündeki kareye konur, giriş/çıkış/en alt
  satırda olamaz; `S` yay — aynı kural, `SPRING_POWER` ile ~9 blok fırlatır (yaylı parçalarda
  3 satır kuralı yok); `M` hareketli platform — satırda tek grup, `moving_platforms(rows)` →
  (satır, sol, genişlik, yol solu, yol sağı); yolun hemen üstü/altı boş, iki üstünde `#` yok; `E` düşman — aynı kural + altındaki platform en az `ENEMY_MIN_PLATFORM` (3) kare;
  `platform_run(rows, r, c)` düşmanın yürüyeceği sütun aralığını verir; `F` uçan düşman — satırında
  `free_span(row, left, right)` ile katı kareye/kenara kadar uçar, satırda tek F, M ile aynı satırda olmaz,
  yol en az `FLYER_MIN_PATH` kare; en iyisi bir platformun hemen üstündeki satır). `mirror(chunk)` sağ-sol
  aynası; `MIRRORED_CHUNKS` içindeki parçalar oyuna hem kendisi hem aynası olarak girer (yeni parçaları
  buraya ekle → iki giriş tarafı otomatik). Toplam 44 parça; 2 yaylı, 2 hareketli platformlu, 3 kırılan platformlu, 3 yarasalı tasarım (+aynaları). Birleşme kuralı: en alt satır boş, sondan ikinci satır giriş (sadece `-`, giriş
  tarafında; sol = sütun 0-4 ve 4 dolu, sağ = 5-9 ve 5 dolu), en üst satır çıkış (aynı kural). Çıkışı
  sol olanın üstüne girişi sağ olan gelir → birleşmede 2 satır fark, üst üste binme yok.
  `check_chunk` yanlış parçada oyun açılırken hata verir. Yeni parça eklerken her iki giriş
  tarafı için her zorlukta parça olsun.
- `enemy.py` — ortak `Patrol` (`patrol()`: `left`-`right` piksel arasında gidip gelir, ondalıklı `pos_x`,
  `old_top` = önceki karedeki üst kenar); `Enemy(center_x, bottom, left, right)` yürür (`ENEMY_SPEED`),
  `FlyingEnemy(center_x, center_y, left, right)` yarasa: `FLYER_SPEED` ile uçar, `FLYER_BOB` kadar süzülür.
  İkisi de `level.enemies`'te; tile'larla çarpışma yok (sınırlar parçadan hesaplanır).
- `level.py` — `Tile`, `Platform`, `Coin`, `Pickup`, `Spring` (`level.springs`; `Spring.squash()` basık resim), `MovingPlatform` (`level.movers` VE
  `level.tiles`; `move()` kaydığı pikseli döndürür; `unsafe = True`), `CrumblingPlatform` (`level.crumblers`;
  sağlamken `level.tiles`'ta da; `step(player, tiles)` her karede: basılınca `CRUMBLE_DELAY` kare titrer
  (`draw_rect` ile çizim kayar, `rect` sabit), sonra tiles'tan çıkar → "break"; `CRUMBLE_RESPAWN` kare sonra
  geri gelir, son `GHOST_TIME` karede `ghost` = silik çizilir; `unsafe = True`) sprite'ları (her `C` için `pick_item()`: `PICKUP_CHANCES`
  ihtimalleriyle altın yerine `Pickup(x, y, kind)` olur → `level.pickups`; kind "heart": `player.heal()` +1 can,
  can doluysa `score.add_bonus(HEART_POINTS)`; kind "magnet"/... güçlendirme → `player.power_up(kind)`;
  `Coin.attract(target)` mıknatısla `MAGNET_RADIUS` içindeyse `MAGNET_PULL` hızla uçar) ve `Level(seed)`: y=0 zeminin altı, yukarı çıktıkça
  y EKSİ. `add_chunk`, `pick_chunk` (giriş = önceki çıkışın tersi, zorluk ≤ 1 + yükseklik //
  `DIFFICULTY_STEP`), `update(view_top, view_bottom)` (`GENERATE_AHEAD` kadar yukarıyı doldurur,
  `REMOVE_BELOW`'dan aşağıdaki parçaları siler). `tiles` = çarpılan her şey, `coins` = altınlar,
  `enemies` = düşmanlar (katı değiller; parça silinince onunkiler de silinir). Tile/Platform/Coin resimleri `level.image()`
  ile bir kere hazırlanıp paylaşılır; `Coin.update()` dönme animasyonu., `bottom` = en alttaki parçanın altı, `width` piksel.
- `score.py` — `Score(start_y)`: `height` = üstüne basılan en yüksek yer (blok, sadece `on_ground`
  iken sayılır, düşünce azalmaz), `coins`, `enemies`, `total` = height × `HEIGHT_POINTS` + coins × `COIN_POINTS`
  + enemies × `ENEMY_POINTS`; `draw(screen)` sol üstte gölgeli yazı (kameradan bağımsız);
  `draw_lives(screen, lives)` sağ üstte kalpler (kaybedilen can gri); `draw_powers(screen, player)` kalplerin
  altında süren güçlendirmelerin simgesi + süre çubuğu (son `POWERUP_WARN_TIME` karede yanıp söner); `draw_text(screen, font, text,
  color, center=/topleft=...)` gölgeli yazı (her yerde bu kullanılır); `load_high_score()` /
  `save_high_score(v)` → `highscore.txt` (oyun klasöründe, git dışı; bozuk/yoksa 0, yazılamazsa sessiz).
- `screens.py` — `draw_menu(screen, high_score)` ve `draw_game_over(screen, score, high_score,
  new_record, ready)`: oyunun üstüne yarı saydam perde + ortalanmış yazılar; yazı tipleri önbellekte.
- Can sistemi `Player`'da: `lives`, `invincible` (kalan kare; `visible` ile yanıp söner), `hurt()`
  (can −1, dokunulmazlık, küçük sıçrama), `bounce(power)`, `check_springs(springs)` (ayak şeridi yaya
  değiyor ve yükselmiyorsa `SPRING_POWER` ile fırlar; main ve check_chunks ikisi de player.update'ten
  sonra çağırır), `heal()`, güçlendirmeler: `powers` {tür: kalan kare} (`POWER_TIME`), `power_up(kind)`,
  `power_fraction(kind)`, `expired` (bu karede bitenler → "powerdown" sesi), `standing_on(sprite)`, `carry(dx, tiles)`
  (main.py her karede önce platformları oynatır, üstünde duranı taşır; duvara çarparsa taşımaz),
  `old_bottom` (önceki karenin ayak hizası),
  `safe_pos` (en son yerde durduğu yer, `unsafe` olanlar — hareketli/kırılan platform — hariç — `respawn()` oraya koyar).
- `camera.py` — `Camera()`: DİKEYDE yumuşak takip (`CAMERA_SMOOTHNESS`), karakter ekranın
  `CAMERA_PLAYER_Y` oranında durur; yukarısı sınırsız, aşağıda `level.bottom`'da durur;
  `follow(rect, level_bottom)`, `top`/`bottom`, `apply(rect)`. Tüm çizim `main.py`'de kamera üzerinden
  (sprite'ta `draw_rect` varsa çizim onunla yapılır).
- `main.py` → ekran durumu `state`: "menu" → (Boşluk/Enter/tıklama) → "playing" → (can biter) →
  "game_over" (`GAME_OVER_DELAY` kare tuş çalışmaz; rekor kırıldıysa hemen kaydedilir) → tuşla
  `new_game()` + "playing". `update_game(...)` oyun mantığı, `draw_world(...)` dünyayı çizer (her
  ekranda arkada görünür). ESC her yerde oyundan çıkar.
  `new_game()` yeni rastgele bölüm + karakter + kamera + puan kurar; altınlar
  `spritecollide(player, level.coins, True)` ile toplanır. Düşmana değince `player.old_bottom <= enemy.old_top`
  ise düşman ölür (`STOMP_BOUNCE`), değilse dokunulmaz değilken `hurt()`. `level.bottom`'ın altına
  düşerse `hurt()` + `respawn()`.
- `check_chunks.py` — çıkılabilirlik testi: `python check_chunks.py` (~20 sn, çok çekirdekli).
  Gerçek `Player` fiziğiyle (sahte `Controls`) BFS: her parçanın girişinden (başlangıçta P) tepesine
  ve her geçerli birleşmede (alt parçanın üst 4 satırı + üst parçanın alt 5 satırı) girişe
  ulaşılabiliyor mu. Düşmanları hesaba katmaz. Yayları gerçek fizikle dener; hareketli
  platformu iki uç durumla modeller (üstündeysen öbür uca taşınırsın, değilsen beklersin). Kırılan
  platformun üstündeyken sadece zıplama hareketleri denenir (beklemek/yürümek yok).
  Yeni yay/platform parçasında "o olmadan çıkılamıyor mu" diye de bak (yoksa süs olur):
  karakter 3 satır yukarıya ~3 kare yana zıplayabiliyor, tahmin edilenden uzak. Yeni parça eklenince veya zıplama/hız ayarı
  değişince MUTLAKA çalıştır. (Konsol cp1254: çıktıda "→" gibi karakter kullanma.)
- Zıplama ~133 px (3 blok = 120 px'e çıkılabilir), yatayda ~4 blok gidilebilir; parça
  tasarlarken basılan yüzeyler arası dikey fark en fazla 3 satır olsun. Platformlar katı olduğu
  için bir üst platform tam tepede olmasın; yana kaydırılmış olsun ki zıplayıp üstüne çıkılabilsin.
- `art.py` — piksel sanatı: harf haritası + palet → `render(rows, palette, size)` (her harf
  `PIXEL_SCALE` px, çizim alta-ortaya yaslı), `shade`/`tint` ile tonlar; `player_frames()`,
  `enemy_frames()` ({1: sağ, -1: sol} çiftleri), `coin_frames()` (dönme), `tile_image()`,
  `platform_image()`, `heart_images()`, `Background` (`SKY_THEMES` gökleri, her `SKY_CHANGE_HEIGHT` px tırmanışta sıradakine
  `SKY_BLEND_HEIGHT` boyunca saydamlıkla geçer, döngüsel; + `STAR_PARALLAX` ile kayan yıldızlar).
- `sound.py` — `pre_init()` (pygame.init'ten önce; 22050 Hz mono 16 bit), `Sounds()`: efektler
  (jump, coin, stomp, hurt, start, game_over, life, spring, crumble, powerup, powerdown) ve 8 ölçülük döngü müzik (`MELODY`/`BASS` nota
  numaraları) `array` ile üretilir (numpy YOK); `play(name)`, `start_music/stop_music`, `toggle_mute`
  (M). Mixer yoksa/biçim farklıysa `enabled=False`, her şey sessizce çalışır. Stereo da desteklenir.
- `controls.py` — `Controls(left, right, jump)`; `TouchButtons`: sol altta ←→, sağ altta zıpla,
  çoklu dokunma (`FINGER*` olayları, parmak yoksa farenin sol tuşu), `handle_event`, `update`,
  `draw` (sadece oyun sırasında); `read_controls(touch)` klavye + butonları birleştirir.
- `effects.py` — `Particle`, `burst(group, center, color)`: altın/düşman/can kaybında saçılan
  kareler; `level.effects` grubunda (new_game'de oluşur).

## Yol haritası
- [x] 0. Kurulum — boş pencere açılıyor
- [x] 1. Karakter — kare, ok tuşlarıyla sağ-sol hareket
- [x] 2. Fizik — yerçekimi, boşlukla zıplama, zemin
- [x] 3. Platformlar — havada platformlar, üzerine çıkma
- [x] 4. Kamera & bölüm — dikey (yukarı doğru) uzun harita, dikey kamera takibi, ince platformlar
- [x] 4b. Sonsuz parça sistemi — rastgele parçalar, geride kalanlar silinir, yükseldikçe zorlaşır
- [x] 5. Toplanabilir — altın, puan göstergesi (puan = tırmanılan yükseklik + altınlar)
- [x] 6. Düşman & can — yürüyen düşman, can, ölme/yeniden başlama
- [x] 7. Oyun sonu — bayrak YOK (sonsuz): kaybettin ekranı + en yüksek skor, başlangıç menüsü
- [x] 8. Güzelleştirme — sprite, animasyon, ses/müzik, dokunmatik kontroller (ekran butonları)
- [ ] 9. Ekstra — yeni parçalar, telefonda çalışır çıktı (ör. pygbag ile tarayıcıda)

## Sıradaki adım
Aşama 9 devam. Yapılanlar: yeni parçalar, yükseldikçe değişen gök, can toplama (kalp), yay,
hareketli platform, kırılan platform, uçan düşman, mıknatıs. Kalan seçenek (kullanıcıya sor):
- Telefonda/tarayıcıda çalışır çıktı: pygbag ile web sürümü (main döngüsü `async` + her karede
  `await asyncio.sleep(0)` olmalı; `highscore.txt` tarayıcıda çalışmaz → localStorage gerekebilir;
  ses biçimi tarayıcıda farklı olabilir — `Sounds` bunu zaten sessizce idare eder; check_chunks
  multiprocessing kullanıyor, web paketine girmemeli). GitHub Pages'te yayın.
- Başka fikirler: kırılan platform, uçan düşman, mıknatıs/kalkan gibi güçlendirmeler.
