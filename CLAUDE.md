# Platform Oyunu — Proje Hafızası

## Proje
- Python + pygame-ce ile 2D platform (zıplama) oyunu.
- MOBİL oyun olacak: ekran dikey (telefon gibi, 400x720) ve bölüm YUKARI doğru ilerler
  (Doodle Jump / Icy Tower tarzı tırmanma). Kullanıcı yana kayan haritayı istemedi.
- Kullanıcı hiç kod yazmamış: kodu Claude yazar, kullanıcı test eder ve geri bildirim verir.
- Kullanıcıyla Türkçe konuş, teknik terimleri basitçe açıkla.
- Çalıştırma: `python main.py` (ESC veya pencereyi kapatmak oyundan çıkar).
- Web sürümü (pygbag 0.9.3, tarayıcıda Python 3.12 çalışır): `python -m pygbag --width 400 --height 720
  --title "Platform Oyunu" --template web.tmpl .` → derler ve http://localhost:8000'de test sunucusu açar
  (`--build` = sadece derle; çıktı `build/web`, git dışı). `pygbag.ini` pakete girmeyecek dosyalar
  (check_chunks.py, CLAUDE.md, highscore.txt...). `web.tmpl` = sayfa şablonu (pygbag default.tmpl'den:
  koyu arka plan; Python'dan tarayıcıya (platform.window...) giden yazıda Türkçe harfler BOZULUYOR
  (UTF-8 → Latin-1) → şablondaki Python yazıları sadece ASCII + HTML kodu (`&#351;`) ve `innerHTML`,
  telefonda kaydırma/yakınlaştırma kapalı, `image-rendering: pixelated`). pygbag şablonda sadece
  `{{cookiecutter.x}}` doldurur (Jinja yorumu vb. çalışmaz). Tarayıcıda test: Chrome görünmez modda
  CDP ile denendi (Edge görünmez modu wasm'da çöküyor); `window.python.PyRun_SimpleString(code)` ile
  sayfadaki Python'a komut gönderilebilir (sonuç bazen bir kare sonra gelir → `platform.window.probe`'a yazdırıp
  JS'ten birkaç kez yokla; `gc.get_objects()` ile Player/Level bulunur). Hız testi: CDP
  `Emulation.setCPUThrottlingRate` ile işlemci yavaşlatılır (telefon taklidi); görünmez Chrome ekranı ~240 Hz yeniler.
  pygbag döngüyü tarayıcının ekran yenilemesine bağlar (her yenilemede bir tur) ve `clock.tick()` tarayıcıda
  ~16 ms MEŞGUL BEKLER (tarayıcıyı kilitler, kare kaçırtır) → web'de çağrılmaz.

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
  `old_top` = önceki karedeki üst kenar); `Enemy(center_x, bottom, left, right, speed)` yürür,
  `FlyingEnemy(center_x, center_y, left, right, speed)` yarasa: uçar, `FLYER_BOB` kadar süzülür (hızları level.py moda göre verir).
  İkisi de `level.enemies`'te; tile'larla çarpışma yok (sınırlar parçadan hesaplanır).
- `level.py` — `Tile`, `Platform`, `Coin`, `Pickup`, `Spring` (`level.springs`; `Spring.squash()` basık resim), `MovingPlatform` (`level.movers` VE
  `level.tiles`; `move()` kaydığı pikseli döndürür; `unsafe = True`), `CrumblingPlatform` (`level.crumblers`;
  sağlamken `level.tiles`'ta da; `step(player, tiles)` her karede: basılınca `CRUMBLE_DELAY` kare titrer
  (`draw_rect` ile çizim kayar, `rect` sabit), sonra tiles'tan çıkar → "break"; `CRUMBLE_RESPAWN` kare sonra
  geri gelir, son `GHOST_TIME` karede `ghost` = silik çizilir; `unsafe = True`) sprite'ları (her `C` için `pick_item()`: `PICKUP_CHANCES`
  ihtimalleriyle altın yerine `Pickup(x, y, kind)` olur → `level.pickups`; kind "heart": `player.heal()` +1 can,
  can doluysa `score.add_bonus(HEART_POINTS)`; kind "magnet"/"shield" güçlendirme → `player.power_up(kind)`;
  `Coin.attract(target)` mıknatısla `MAGNET_RADIUS` içindeyse `MAGNET_PULL` hızla uçar) ve `Level(mode, seed)` (mode = `DIFFICULTIES[...]` sözlüğü): y=0 zeminin altı, yukarı çıktıkça
  y EKSİ. `add_chunk`, `pick_chunk` (giriş = önceki çıkışın tersi; yükseklik = tırmanılan + `map_head_start`,
  zorluk ≤ 1 + yükseklik // `DIFFICULTY_STEP`; `random.choices` ağırlığı `1 + t·HARD_CHUNK_BIAS·(zorluk−1)` → yukarıda zor parçalar sık), `update(view_top, view_bottom)` (`GENERATE_AHEAD` kadar yukarıyı doldurur,
  `REMOVE_BELOW`'dan aşağıdaki parçaları siler). `tiles` = çarpılan her şey, `coins` = altınlar,
  `enemies` = düşmanlar (katı değiller; parça silinince onunkiler de silinir).
  ZORLUK MODLARI: settings `DIFFICULTIES` = mod → sayılar sözlüğü ("easy" Kolay, "normal" Orta = eski oyunun
  sayıları, "hard" Zor, "ultra" Ultra Zor; `DIFFICULTY_NAMES` ekrandaki adlar). Anahtarlar: `lives`/`max_lives`,
  `hard_height`, `map_head_start` (harita parçaları baştan o kadar yukarıdaymış gibi), `lava_delay`, `lava_speed(_max)`,
  `enemy_speed(_max)`, `flyer_speed(_max)`, `heart_chance(_min)`. Ultra Zor (kullanıcı kararı): baştan en zor
  (sayıları Orta'nın en zor hâlinden başlar, zor parçalar hemen), lav beklemez ve hızlı, 1 canla başlar (kalp nadir,
  en fazla 3), kalkan/mıknatıs normal çıkar. Güçlendirme ihtimalleri modlara göre değişmez.
  YÜKSELDİKÇE ZORLAŞMA: `hardness(height, mode)` = 0 (başlangıç) → 1 (modun `hard_height` px tırmanınca), `blend(easy, hard, t)`.
  `add_chunk` parçanın yüksekliğinden `t` hesaplar: düşman hızı `enemy_speed`→`enemy_speed_max`,
  `pick_item(t)` kalp ihtimali `heart_chance`→`heart_chance_min`. Tile/Platform/Coin resimleri `level.image()`
  ile bir kere hazırlanıp paylaşılır; `Coin.update()` dönme animasyonu., `bottom` = en alttaki parçanın altı, `width` piksel.
- `score.py` — `Score(start_y, record)`: `height` = üstüne basılan en yüksek yer (blok = ekranda "m", sadece `on_ground`
  iken sayılır, düşünce azalmaz), `coins`, `enemies`, `total` = height × `HEIGHT_POINTS` + coins × `COIN_POINTS`
  + enemies × `ENEMY_POINTS`. ASIL HEDEF YÜKSEKLİK (kullanıcı kararı: oyuncu kendi tırmanış rekorunu geçmek ister):
  `draw(screen)` sol üstte BÜYÜK "37 m", altında küçük "Puan / Altın" (kameradan bağımsız); `record` = oyun
  başındaki yükseklik rekoru, `new_record` = geçildi mi; `update(player)` rekor o an kırıldıysa True döner
  (main "powerup" sesi çalar) ve `toast` = `RECORD_TOAST_TIME` kare "YENİ REKOR!" (ilk oyunda, rekor 0 iken yok);
  `draw_record_line(screen, camera)` haritada rekor yüksekliğinde kesikli çizgi + "Rekor N m" (draw_world, gökten hemen sonra);
  `draw_lives(screen, lives, max_lives)` sağ üstte, durdur düğmesinin solunda kalpler (kaybedilen can gri); `draw_powers(screen, player)` kalplerin
  altında süren güçlendirmelerin simgesi + süre çubuğu (son `POWERUP_WARN_TIME` karede yanıp söner); `draw_text(screen, font, text,
  color, center=/topleft=...)` gölgeli yazı (her yerde bu kullanılır; resimleri `TEXT_CACHE`'te, her karede
  yeniden yazılmaz).
- `storage.py` — kalıcı kayıtlar, `STORES` = tür → (dosya, localStorage adı): "height" (`bestheight.txt`, asıl
  rekor), "score" (`highscore.txt`, en yüksek puan) — rekorlar HER MODUN AYRI: `load_record/save_record(..., mode)`,
  `names(kind, mode)`: Orta eski adları kullanır, diğerlerinde ada `-easy`/`-hard`/`-ultra` eklenir (ör.
  `bestheight-ultra.txt`; .gitignore ve pygbag.ini'de de var), "stats" (`stats.json`: games/climbed/coins/enemies toplamları),
  "options" (`options.json`: muted, difficulty, music_volume, effects_volume). `load_record/save_record` (sayı), `load_dict(kind, defaults)/save_dict`
  (JSON; eksik/bozuk/yanlış tipli değer → default). Dosyalar oyun klasöründe, git ve pygbag dışı; okunamazsa
  default, yazılamazsa sessiz; web'de (`settings.WEB`, `sys.platform == "emscripten"`) `platform.window.localStorage`.
- `ui.py` — `Buttons(actions, top, gap)`: alt alta ortalı düğmeler; `handle_event(event)` basılan düğmenin adını
  döndürür (dokunma `FINGERDOWN`, sol tık, klavye ↑↓/W-S + Enter/Boşluk; `MOUSEMOTION` ile seçili olan değişir;
  `focus` = seçili); `draw(screen, labels)`. `take_click()`: `BUTTON_CLICK_GAP` ms içindeki ikinci tıklama sayılmaz
  (telefonda bir dokunuş hem parmak hem fare olayı gelebilir; ör. menüden dönünce alttaki düğmeye de basılıyordu).
  `PauseButton` oyunda sağ üstte ⏸ (`clicked(event)`). `Slider(center_y)` kaydırma çubuğu: `value` 0..`VOLUME_STEPS`,
  parmak/fareyle sürükle veya dokun (`handle_event` → değişti mi), `nudge(±1)` klavye için. Düğme renk/boyları settings "Menü düğmeleri".
- `screens.py` — `SOUND_MENU` (`SoundMenu`: ses ayarları ekranı; Müzik + Efektler çubukları, "sound" (Ses: Açık/Kapalı)
  ve "back" düğmeleri; ↑↓ seçer, ←→ çubuğu ayarlar; `handle_event` → "music"/"effects"/"sound"/"back"),
  her ekranın `Buttons`'ı (`MAIN_BUTTONS` play/difficulty/howto/records/sound_menu, `BACK_BUTTON`,
  `PAUSE_BUTTONS` resume/sound/menu, `GAME_OVER_BUTTONS` again/menu), `LABELS` sabit yazılar (değişenleri main
  verir); `draw_main_menu` (başlık, "Rekor: N m", düğmeler, web'de HEP `draw_slow_hint` — kullanıcı isteği),
  `draw_howto` (kontroller + `HOWTO_ROWS`: oyundaki resimlerle her şeyin açıklaması — yeni öğe eklenince buraya da
  ekle), `draw_records(best_heights, high_scores, stats, current)` (her modun tırmanış + puan rekoru, seçili mod sarı; altında
  tüm modların toplamları), `draw_pause`, `draw_game_over(screen, score, mode_name, ...)` (başlık altında "Zorluk: ...";
  düğmeler `ready` olunca).
  Oyunun üstüne yarı saydam perde; büyük yazı yükseklik/rekor (m), puan küçük.
- Can sistemi `Player`'da: `Player(x, y, level_width, lives, max_lives)` (moddan), `lives`, `max_lives` (kalp sınırı), `invincible` (kalan kare; `visible` ile yanıp söner), `hurt()`
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
- `main.py` → `StepTimer`: oyun hızı kare hızından bağımsız. `timer.steps()` her karede gerçek geçen süre
  kadar adım (1 adım = 1/`FPS` sn) verir, `update_game` o kadar kez çalışır (30 Hz'de 2, 120 Hz'de iki karede 1;
  en fazla `MAX_CATCH_UP`); tam sayıya 0,1 adımdan yakın süreler yuvarlanır (titreme olmasın); adım yoksa
  çizim yapılmaz. Tüm "kare" sayan ayarlar aslında adım sayar. Sebep: telefonda kare hızı düşünce
  (iPhone Düşük Güç Modu 30 Hz) oyun yarı hızda akıyordu. `FpsMeter`: saniyedeki çizilen kare (üst orta);
  `SHOW_FPS` veya web'de adres sonu `#fps` (ör. .../platform/#fps) ile açılır — telefonda akıcılık testi.
  Kullanıcı iPhone'da doğruladı: Düşük Güç Modu açıkken 30, kapalıyken 60 kare/sn (oyunun elinde değil).
  `FpsMeter.count()` her çizilen karede sayar; `slow` = 2 sn üst üste `LOW_FPS_LIMIT` altı → web'de
  kaybettin ekranının altında `screens.draw_slow_hint` ("Düşük Güç Modu'nu kapat"; ana menüde web'de hep var).
  `Game` sınıfı tüm durumu tutar: rekorlar (`best_heights`/`high_scores` = mod → değer; `mode`, `best_height`,
  `high_score` = seçili modunki), `stats` (tüm modların toplamı), `options` (açılışta yüklenir; muted ise ses kapalı başlar),
  `level/player/camera/score`; `state`: "menu" (ana menü) ↔ "sound"/"howto"/"records" (Geri/ESC);
  ses çubuğu oynayınca `change_volume` (ses kapalıysa açar, kaydeder, efektte örnek "coin" sesi çalar); menü "play" →
  `start()` → "playing" ↔ "paused" (⏸ düğmesi, ESC veya P; durunca Devam/Ses/Ana Menü); can biter → "game_over"
  (`GAME_OVER_DELAY` kare düğme yok) → Tekrar Oyna (`start()`) / Ana Menü (`to_menu()`). `finish()` oyun bitince
  (kaybedince VE durdurup ana menüye dönünce) rekorları + istatistikleri kaydeder. `handle_event`, `update(steps, touch)`,
  `draw(...)`. M tuşu her yerde `toggle_sound()` (kaydedilir). ESC ana menüde oyundan çıkar (web'de hariç).
  `next_difficulty()` Kolay→Orta→Zor→Ultra Zor (`DIFFICULTY_NAMES`), kaydeder ve `reset()` (arkadaki bölüm yeni moda göre).
  `update_game(...)` oyun mantığı, `draw_world(...)` dünyayı çizer (her ekranda arkada görünür).
  `main()` `async`: döngü sonunda `await asyncio.sleep(0)` (web için şart), en altta `asyncio.run(main())`.
  `new_game(best_height, mode)` yeni rastgele bölüm + karakter + kamera + puan kurar; altınlar
  `spritecollide(player, level.coins, True)` ile toplanır. Düşmana değince `player.old_bottom <= enemy.old_top`
  ise düşman ölür (`STOMP_BOUNCE`); kalkan (`player.powers["shield"]`) varken değdiği düşman zıplamadan ölür;
  değilse dokunulmaz değilken `hurt()`. `level.bottom`'ın altına düşerse (kalkan olsa da) `hurt()` +
  `respawn()`. Mıknatıs varken her karede `coin.attract(player.rect.center)`. Kalkan sürerken `draw_world`
  karakterin etrafına `art.shield_bubble` çizer. Düşmanın `color`'ı ölünce saçılan parçacıkların rengi.
- `lava.py` — `Lava(mode)`: aşağıdan yükselen lav, `level.lava`'da (new_game kurar). `y` = yüzey; `lava_delay`
  bekler, sonra `blend(lava_speed, lava_speed_max, hardness(-camera.bottom, mode))` hızla yükselir; ekranın en fazla
  `LAVA_MAX_GAP` altında kalır (< `REMOVE_BELOW` → düşen önce lava değer). `update(camera_bottom)`, `touches(rect)`
  (ayak `LAVA_HIT_DEPTH` içerideyse) → main: kalkan olsa da `hurt()` + `respawn()` + `push_back(ayak)` (lav
  `LAVA_PUSHBACK` aşağı çekilir). `draw(screen, camera)` her şeyin önünde (`art.lava_frames()` dalga şeridi + düz dolgu);
  ekranın altındayken `LAVA_WARN_DISTANCE` içinde `art.lava_glow()` kızıllık. check_chunks lavı hesaba katmaz.
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
  `PIXEL_SCALE` px, çizim alta-ortaya yaslı; hiç `.` yoksa ve ekran açıksa `convert()` = saydamsız → tarayıcıda
  ~5 kat hızlı çizilir), `shade`/`tint` ile tonlar; `player_frames()`,
  `enemy_frames()` ({1: sağ, -1: sol} çiftleri), `flyer_frames()` (kanat çırpma), `crumble_frames()`
  (sağlam, çatlak, silik), `magnet_image()`, `shield_image()`, `shield_bubble(r)`, `coin_frames()` (dönme), `tile_image()`,
  `platform_image()`, `heart_images()`, `Background` (`SKY_THEMES` gökleri, her `SKY_CHANGE_HEIGHT` px tırmanışta sıradakine
  `SKY_BLEND_HEIGHT` boyunca saydamlıkla geçer, döngüsel; + `STAR_PARALLAX` ile kayan yıldızlar).
- `sound.py` — `pre_init()` (pygame.init'ten önce; 22050 Hz mono 16 bit; tampon masaüstünde 512,
  web'de `WEB_AUDIO_BUFFER` = 2048 — tarayıcı 512'de cızırdıyordu; tarayıcı frekansı kendisi seçer, 48000), `Sounds()`: efektler
  (jump, coin, stomp, hurt, start, game_over, life, spring, crumble, powerup, powerdown) ve 8 ölçülük döngü müzik (`MELODY`/`BASS` nota
  numaraları) `array` ile üretilir (numpy YOK); `play(name)`, `start_music/stop_music`, `toggle_mute`,
  `set_levels(music, effects)` (0-1 çarpan; tam = `MUSIC_VOLUME`/`SOUND_VOLUME`)
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
- [ ] 9. Ekstra — yeni parçalar, telefonda çalışır çıktı (pygbag ile tarayıcıda — YAPILDI, yayında)

## Sıradaki adım
Aşama 9 devam. Yapılanlar: yeni parçalar, yükseldikçe değişen gök, can toplama (kalp), yay,
hareketli platform, kırılan platform, uçan düşman (yarasa), mıknatıs ve kalkan güçlendirmeleri.
Web sürümü hazır ve tarayıcıda denendi (menü, klavye, çoklu dokunma, ses, localStorage rekor çalışıyor).
YAYINDA: https://erenalbayrakk04.github.io/platform/ (depo herkese açık, Pages Source = GitHub Actions).
`.github/workflows/web.yml` her push'ta: check_chunks.py → pygbag derleme → Pages'e yükleme (~4 dk);
yani her commit+push oyunu internette de günceller. Parça testi geçmezse yayına çıkmaz.
Açık depoda çalışma durumu girişsiz bakılabilir: https://api.github.com/repos/erenalbayrakk04/platform/actions/runs
- Zorlaştırma yapıldı (kullanıcı seçti: düşmanlar kolaydı, acele yoktu, çok kalp vardı): yükseldikçe zorlaşma +
  yükselen lav. Kullanıcı oynayıp lav/düşman hızı için geri bildirim verecek (sayılar settings.py'de).
  Kolay/orta/zor MODLARI sonra, ana menüyle birlikte (her modun ayrı rekoru olsun).
- Sonra belki: başka güçlendirmeler (ör. jetpack), başka düşman türleri.
- ANA MENÜ yapıldı (Oyna, Zorluk, Nasıl Oynanır, Rekorlar, Ses Ayarları (müzik/efekt seviyesi) + oyunda durdur). Web'de menüde "Düşük Güç Modu'nu
  kapat" sabit yazıyor (otomatik ipucu kullanıcının iPhone'unda çıkmamıştı).
- ZORLUK MODLARI yapıldı: Kolay / Orta / Zor / Ultra Zor (kullanıcı Ultra Zor'u istedi), her modun ayrı rekoru.
  Kullanıcı oynayıp sayılar için geri bildirim verecek (settings `DIFFICULTIES`). Ultra'da kıpırdamayan oyuncuya
  lav ~2,4 sn'de yetişir (lav beklemez — kullanıcı seçimi; çok sert gelirse `lava_delay` artırılır).
