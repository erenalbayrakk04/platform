# Platformin — Proje Hafızası

## Proje
- Python + pygame-ce ile 2D platform (zıplama) oyunu.
- MOBİL oyun olacak: ekran dikey (telefon gibi, 400x720) ve bölüm YUKARI doğru ilerler
  (Doodle Jump / Icy Tower tarzı tırmanma). Kullanıcı yana kayan haritayı istemedi.
- Kullanıcı hiç kod yazmamış: kodu Claude yazar, kullanıcı test eder ve geri bildirim verir.
- Kullanıcıyla Türkçe konuş, teknik terimleri basitçe açıkla.
- OYUN İKİ DİLLİ (Türkçe + İngilizce, `lang.py`): kodda yazılar Türkçe yazılır, `draw_text` çizerken çevirir. YENİ YAZI
  EKLEYİNCE `lang.EN`'e İngilizcesini de yaz ve `python check_lang.py` çalıştır (eksik çeviri varsa yayına çıkmaz).
- Çalıştırma: `python main.py` (ESC veya pencereyi kapatmak oyundan çıkar).
- Web sürümü (pygbag 0.9.3, tarayıcıda Python 3.12 çalışır): `python -m pygbag --width 400 --height 720
  --title "Platformin" --template web.tmpl .` → derler ve http://localhost:8000'de test sunucusu açar
  (`--build` = sadece derle; çıktı `build/web`, git dışı). Windows'ta başına `PYTHONUTF8=1` koy (yoksa pygbag
  web.tmpl'i cp1254 ile okuyup ▶ ■ gibi karakterlerde çöküyor). Yerel `--build` çıktısı pygame'i localhost:8000'deki
  pygbag sunucusundan ister → tarayıcı testi pygbag'in kendi sunucusuyla (başka sunucuyla "Hazırlanıyor"da takılır).
  `pygbag.ini` pakete girmeyecek dosyalar
  (check_chunks.py, CLAUDE.md, highscore.txt...). `web.tmpl` = sayfa şablonu (pygbag default.tmpl'den:
  koyu arka plan; Python'dan tarayıcıya (platform.window...) giden yazıda Türkçe harfler BOZULUYOR
  (UTF-8 → Latin-1) → şablondaki Python yazıları sadece ASCII + HTML kodu (`&#351;`) ve `innerHTML`,
  telefonda kaydırma/yakınlaştırma kapalı, `image-rendering: pixelated`). pygbag şablonda sadece
  `{{cookiecutter.x}}` doldurur (Jinja yorumu vb. çalışmaz). Tarayıcıda test: Chrome görünmez modda
  CDP ile denendi (Edge görünmez modu wasm'da çöküyor); `window.python.PyRun_SimpleString(code)` ile
  sayfadaki Python'a komut gönderilebilir (sonuç bazen bir kare sonra gelir → `platform.window.probe`'a yazdırıp
  JS'ten birkaç kez yokla; `gc.get_objects()` ile Player/Level bulunur). Hız testi: CDP
  `Emulation.setCPUThrottlingRate` ile işlemci yavaşlatılır (telefon taklidi); görünmez Chrome ekranı ~240 Hz yeniler.
  CDP'ye Python `websocket-client` ile bağlanırken `suppress_origin=True` (yoksa 403); yavaş internet taklidi
  `Network.emulateNetworkConditions`; dokunuş `Emulation.setTouchEmulationEnabled` + `Input.dispatchTouchEvent`.
  CDP ile fare tıklamadan ÖNCE `mouseMoved` gönder: SDL tıklamayı farenin son hareket ettiği yerde sayar
  (yoksa tıklama bir önceki yere düşer; gerçek parmak/farede sorun yok).
  pygbag döngüyü tarayıcının ekran yenilemesine bağlar (her yenilemede bir tur) ve `clock.tick()` tarayıcıda
  ~16 ms MEŞGUL BEKLER (tarayıcıyı kilitler, kare kaçırtır) → web'de çağrılmaz.
- `web.tmpl`'in giriş ekranıyla gelen kısımları: pygbag'in "Başlamak için ekrana dokun" beklemesi (`MM.UME`)
  KALDIRILDI — oyun hemen açılır, ilk ekran oyunun kendi giriş ekranı (title.py). SES KİLİDİ: tarayıcı ilk dokunuşa
  kadar ses çalmaz; SDL açılışta AudioContext'i "suspended" kurar → şablon `window.AudioContext`'i `TrackedAudioContext`
  alt sınıfıyla değiştirip kurulanları tutar, `touchend/pointerup/mousedown/click/keydown` olayında (window, capture)
  `resume()` + boş ses çalar (iPhone'da dokunma olayının İÇİNDE olmalı; emscripten'in kendi touchstart dinleyicisi
  iPhone'da yetmez). Askıda kalırken SDL ses karıştırmaz → müzik dokununca baştan başlar. Görünmez Chrome'da
  doğrulandı (dokunmadan suspended → dokununca running). YÜKLEME EKRANI `#loader`: oyunla aynı oranda kutu, ilk gök
  renkleri, dönen piksel altın (art.py COIN_ROWS'un JS kopyası), "Yükleniyor..." + pygbag'in gizli `#progress`'inden
  indirme çubuğu (sadece ilk/yavaş indirmede görünür); Python başlayınca `loader_ready()` → "Hazırlanıyor". Yazıların
  dili: localStorage'daki seçeneklerde `language` (oyunda seçilen), yoksa `navigator.language` (lang.py ile aynı kural).
  main.py ilk kareyi çizince `hide_web_loader()` → JS `loader_done()`: önce `window_resize()` (pygbag oranı oyun
  ekranı kurulmadan hesaplarsa kare sanıp 400x400 BASIK çiziyordu), sonra solarak kaybolur. DİKKAT: şablondaki
  `config = {...}` noktalı virgülsüz biter → arkasına `(function...)` yazılırsa hiç çalışmaz (TypeError) → yeni JS
  ayrı `<script>` bloğunda.

## Çalışma kuralları
- Her aşama sonunda oyun çalışır durumda olmalı.
- Kullanıcının isteği: HER eklemeden/değişiklikten sonra (aşamanın bitmesini bekleme) git commit at
  ve hemen `git push` ile GitHub'a gönder. Kullanıcıya ayrıca sorma; bu kalıcı izin.
  Depo: https://github.com/erenalbayrakk04/platform, dal `main`. Commit mesajları Türkçe ve kısa.
- Ayarlanabilir sayılar (hız, zıplama gücü, renkler) `settings.py` içinde dursun.
- Görseller ve sesler dosya DEĞİL, kodla üretiliyor (kullanıcı kararı, Aşama 8): piksel sanatı
  `art.py`'de (skin çizimleri, fiyatları ve görevleri `skins.py`'de), Modern temanın yumuşak çizimleri `modern.py`'de
  (theme.py), retro sesler/müzik `sound.py`'de. Renkler settings.py'deki ana renklerden gelir.

## Dosyalar
- `main.py` — oyun döngüsü (olaylar → güncelleme → çizim)
- `settings.py` — tüm ayarlar
- `player.py` — karakter (`Player` sprite'ı; `update(tiles, controls)` — tuşları kendisi okumaz,
  `controls.left/right/jump` alır; `jumped` = bu karede zıpladı (ses için); `animate(dx)` resim seçer
  (idle/walk1/walk2/jump × `facing`); yerçekimi `velocity_y` + ondalıklı `pos_y`; yatay ve dikey
  çarpışmayı ayrı çözer; `on_ground` ayağın 1 px altını kontrol eder; `respawn()` başlangıca döndürür;
  `Player(x, y, level_width, lives, max_lives, skin)` — bölüm kenarından dışarı çıkamaz; `set_skin(id)` görünüşü
  değiştirir: `frames` = `skins.frames(id)`, `pose` = şu anki resim adı, `color` = can kaybında saçılan parçacık rengi,
  `trail` = efsanevi skinin izi (`Trail`) ya da None)
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
  yol en az `FLYER_MIN_PATH` kare; en iyisi bir platformun hemen üstündeki satır). `walker_spots(rows)` /
  `flyer_spots(rows)` = ek rastgele düşman konabilecek yerler [(satır, boş sütunlar)] (kurallara uyan). `mirror(chunk)` sağ-sol
  aynası; `MIRRORED_CHUNKS` içindeki parçalar oyuna hem kendisi hem aynası olarak girer (yeni parçaları
  buraya ekle → iki giriş tarafı otomatik). Toplam 44 parça; 2 yaylı, 2 hareketli platformlu, 3 kırılan platformlu, 3 yarasalı tasarım (+aynaları). Birleşme kuralı: en alt satır boş, sondan ikinci satır giriş (sadece `-`, giriş
  tarafında; sol = sütun 0-4 ve 4 dolu, sağ = 5-9 ve 5 dolu), en üst satır çıkış (aynı kural). Çıkışı
  sol olanın üstüne girişi sağ olan gelir → birleşmede 2 satır fark, üst üste binme yok.
  `check_chunk` yanlış parçada oyun açılırken hata verir. Yeni parça eklerken her iki giriş
  tarafı için her zorlukta parça olsun. `FINISH_CHUNKS` = {giriş tarafı: bitiş parçası} (bölüm modu; çıkışı `None`,
  `goal_row` = zirve satırı, `G` = bayrak; `mirror` çıkışsızı da aynalar).
- `stages.py` — BÖLÜM MODU (kullanıcı kararı: sonsuz oyun da kalır; bölümler mevcut parçalardan, 3 yıldız, lav bazı
  bölümlerde). HER ZORLUĞUN KENDİ 20 BÖLÜMÜ (kullanıcı kararı: "tamamen farklı bölümler", hepsi baştan açık, seçim
  bölümler ekranındaki sekmelerden = ana menüdeki zorluk ayarıyla aynı): `STAGE_SETS` = {"easy": EASY_STAGES, "normal":
  NORMAL_STAGES (ilk yazılan liste, haritaları korunsun diye seed 1000+), "hard": HARD_STAGES, "ultra": ULTRA_STAGES},
  `STAGE_COUNT` = 20 (hepsinde aynı olmalı). Kolay/Orta mekanikleri tek tek tanıtır; Zor/Ultra'da her bölüm bir şeyin
  sınavı (ör. "Diken Tarlası", "Lav Nehri"); `hard`/`ultra` = o listelerin varsayılanlı `partial(stage, ...)`'ı.
  `stage(name, goal, intro, ...)` alanları dosyanın başında: `max_chunk`, `features` (SMK), `focus` (bu işaretli parçalar
  `FOCUS_WEIGHT` kat sık; planda hiç yoksa Level ilk parçayı onlardan seçer), `walkers`/`flyers` tür ağırlıkları (boşsa
  o düşman yok), `items`, `boost` (tanıtılan eşya: `ITEM_BOOST` kat sık + ilk altının yerine kesin gelir), `lava`
  (None / (bekleme, hız, en yüksek)), `hardness` (t aralığı), `base` mod, `extra`. Her bölüme `seed` (SEED_BASE[mod] +
  sıra) ve `difficulty` yazılır; canlar settings `STAGE_LIVES[mod]`. `stage_mode(stage)` → Level/Lava'nın
  mod sözlüğü (base + `walker_kinds`, `flyer_kinds`, `magnet_chance`, `shield_chance`, `lava` bool, `hardness`);
  `allowed_chunks(stage, entry)`, `focused`, `check_stages()` (açılışta). Bölüm değişince bir betikle her bölümü
  üretip bak (Level kur, plan bitene kadar `update` → bayrak yüksekliği, çıkan düşman/yapı/eşya, aynı seed aynı harita).
  ARI: `Level.bee_spot` aynı satırda aşağı-yukarı uçacak yeri olan en yakın sütunu arar (uçan düşman yerleri çoğu zaman
  platformun hemen üstünde, orada yer yok; eskiden hep yarasaya dönüyordu). `bee_path` ayrıca arıyı bir platformun
  KENARINA, tam o platformun hizasına inecek sütuna koymaz (None → yan sütun): orada çıkışın tek yolunu kapatıyordu
  (Ultra 13. bölüm 36 m: dokunmadan geçmek imkânsızdı; ancak 45 karenin 4'ünde, kusursuz tuşlamayla arıya basılabiliyordu).
  Bir yerin geçilebilirliğini ölçmek için: arının her evresi × zıplama yeri için gerçek fizikle BFS (karakter + arı kopyalanır).
- `enemy.py` — ortak `Patrol` (`patrol()`: `start`-`end` piksel arasında gidip gelir, `vertical` ise dikeyde; ondalıklı `pos`,
  `old_top` = önceki karedeki üst kenar, `spiky` = üstüne basılamaz); resimler `frames(tür)` ile bir kere hazırlanır.
  Hepsinin `update(target)`'ı karakterin kutusunu alır (`level.enemies.update(player.rect)`; sadece topçu kullanır).
  Yürüyenler (E yeri): `Enemy(center_x, bottom, left, right, speed)` kırmızı; `Spiky` kirpi (`Enemy` gibi, `SPIKY_SPEED` kat
  yavaş, `spiky = True`); `Slime` sümük (`SLIME_JUMP_TIME`'da bir `SLIME_SQUASH_TIME` basılıp bekler, `SLIME_JUMP_POWER` +
  `GRAVITY` ile zıplar, havada da yürür); `Cannon(center_x, bottom, shots, fire_time)` topçu (yürümez, karaktere döner; karakter dikeyde
  `CANNON_RANGE` içindeyken `fire_time` (mod `cannon_fire_time`, yoksa `CANNON_FIRE_TIME`) karede bir `Fireball` atar, önceki `CANNON_WARN_TIME` karede kızarır — kızarma ancak
  karakter yakındayken başlar). `Fireball(center_x, center_y, direction)`: `level.shots`'ta, `update(tiles, level_width)` katıya
  /kenara gelince söner. Uçanlar (F yeri): `FlyingEnemy(center_x, center_y, left, right, speed)` yarasa: `FLYER_BOB` kadar
  süzülür; `Bee(center_x, center_y, top, bottom, speed, facing)` arı: dikey `Patrol`, ekranın ortasına bakar.
  Hızları level.py moda göre verir. Hepsi `level.enemies`'te; tile'larla çarpışma yok (sınırlar parçadan hesaplanır).
- `level.py` — `Tile`, `Platform`, `Coin`, `Pickup`, `Spring` (`level.springs`; `Spring.squash()` basık resim), `MovingPlatform` (`level.movers` VE
  `level.tiles`; `move()` kaydığı pikseli döndürür; `unsafe = True`), `CrumblingPlatform` (`level.crumblers`;
  sağlamken `level.tiles`'ta da; `step(player, tiles)` her karede: basılınca `CRUMBLE_DELAY` kare titrer
  (`draw_rect` ile çizim kayar, `rect` sabit), sonra tiles'tan çıkar → "break"; `CRUMBLE_RESPAWN` kare sonra
  geri gelir, son `GHOST_TIME` karede `ghost` = silik çizilir; `unsafe = True`) sprite'ları (her `C` için `pick_item()`: `PICKUP_CHANCES`
  ihtimalleriyle altın yerine `Pickup(x, y, kind)` olur → `level.pickups`; kind "heart": `player.heal()` +1 can,
  can doluysa `score.add_bonus(HEART_POINTS)`; kind "magnet"/"shield" güçlendirme → `player.power_up(kind)`;
  kind "gem" = ELMAS (skin parası, `art.gem_frames()` ışıldar — Pickup birden çok resmi sırayla gösterir; ihtimal
  `blend(GEM_CHANCE, GEM_CHANCE_MAX, t)` → 100 m'de ~1; listede EN SONDA, böylece bölüm haritalarındaki kalp/güçlendirme
  yerleri değişmedi, sadece bazı altınlar elmas oldu) → `score.add_gem()`, "gem" sesi;
  `Coin.attract(target)` mıknatısla `MAGNET_RADIUS` içindeyse `MAGNET_PULL` hızla uçar) ve `Level(mode, seed)` (mode = `DIFFICULTIES[...]` sözlüğü): y=0 zeminin altı, yukarı çıktıkça
  y EKSİ. `add_chunk`, `pick_chunk` (giriş = önceki çıkışın tersi; yükseklik = tırmanılan + `map_head_start`,
  zorluk ≤ 1 + yükseklik // `DIFFICULTY_STEP`; `random.choices` ağırlığı `1 + t·HARD_CHUNK_BIAS·(zorluk−1)` → yukarıda zor parçalar sık), `update(view_top, view_bottom)` (`GENERATE_AHEAD` kadar yukarıyı doldurur,
  `REMOVE_BELOW`'dan aşağıdaki parçaları siler). `tiles` = çarpılan her şey, `coins` = altınlar,
  `enemies` = düşmanlar (katı değiller; parça silinince onunkiler de silinir).
  BÖLÜMDE `Level(mode, seed, stage)`: `make_plan()` bütün parça sırasını baştan seçer (sonunda bitiş parçası) →
  `goal_height` (bayrağın zirvesi, blok) baştan belli; `update` planı tembel kurar, bitince durur. `pick_chunk(top, side)`
  bölümde `allowed_chunks` + focus ağırlığı. Bölümde olmayan düşman türünün E/F'si '.' olur; `pick_enemy` uyan tür
  yoksa None (yerleştirilmez). `Goal` bayrak sprite'ı `level.goals`; `coins_total` = konan altın (yıldız için).
  `hardness()` modda `hardness` (low, high) varsa t'yi o aralığa sıkıştırır.
  ZORLUK MODLARI: settings `DIFFICULTIES` = mod → sayılar sözlüğü ("easy" Kolay, "normal" Orta = eski oyunun
  sayıları, "hard" Zor, "ultra" Ultra Zor; `DIFFICULTY_NAMES` ekrandaki adlar). Anahtarlar: `lives`/`max_lives`,
  `hard_height`, `map_head_start` (harita parçaları baştan o kadar yukarıdaymış gibi), `lava_delay`, `lava_speed(_max)`,
  `enemy_speed(_max)`, `flyer_speed(_max)`, `extra_enemy_chance(_max)`, `extra_flyer_chance(_max)`, `heart_chance(_min)`; isteğe bağlı `walker_kinds`/`flyer_kinds` (tür
  ağırlıkları) ve `cannon_fire_time` — bunları `stage_mode` bölümün kendi değerleriyle/varsayılanla EZER (bölümler etkilenmez;
  bölümler moddan sadece `enemy_speed`/`flyer_speed`/`heart_chance`'ı alır). Ultra Zor (kullanıcı kararı): baştan en zor
  (sayıları Orta'nın en zor hâlinden başlar, zor parçalar hemen), lav beklemez ve hızlı, 1 canla başlar (kalp nadir,
  en fazla 3), kalkan/mıknatıs normal çıkar. Güçlendirme ihtimalleri modlara göre değişmez.
  ULTRA SONSUZ SERTLEŞTİ (2026-10-10, kullanıcı: "Ultra Zor, Zor gibi" — ölçünce 150 m'den sonra parça başı düşman Zor
  1,00 / Ultra 1,03, lav 1,0 / 1,15'ti): lav 1,0→1,35, ek düşman 0,4→0,55 + uçan 0,16→0,22 (parça başı ~1,2-1,5; Zor
  0,6-1,0), türler çoğu sümük/kirpi/topçu + yarasa/arı yarı yarıya, topçu 100 karede bir ateş. 80 bölümün haritası
  eskisiyle birebir aynı (git worktree + imza betiği). LAV SINIRI: kusursuz tırmanış (gerçek fizikle Dijkstra, maliyet =
  kare) ~4,4 px/kare (3 satır ~27 karede), en yavaş parça (zorluk 3, hareketli platformlu) ~1,8 px/kare → lav hızı bunun
  epey altında kalmalı (oyuncu kusursuz değil; dururken lav ~448 px = 11 blok geride).
  YÜKSELDİKÇE ZORLAŞMA: `hardness(height, mode)` = 0 (başlangıç) → 1 (modun `hard_height` px tırmanınca), `blend(easy, hard, t)`.
  `add_chunk` parçanın yüksekliğinden `t` hesaplar: düşman hızı `enemy_speed`→`enemy_speed_max`,
  `pick_item(t)` kalp ihtimali `heart_chance`→`heart_chance_min`.
  EK RASTGELE DÜŞMANLAR (kullanıcı "daha fazla düşman" istedi): `add_extra_enemies(rows, t)` her parçada (başlangıç hariç)
  satırların kopyasına 'E'/'F' yazar: `walker_spots`'taki her platforma `extra_enemy_chance`, `flyer_spots`'taki her
  satıra `extra_flyer_chance` ihtimalle (t ile `_max`'a artar). Orta'da parça başı düşman: eklerden önce ~0,57,
  ilk hâli ~1,35-1,47 (kullanıcı fazla buldu) → şimdi ~0,83-0,86 (arası, eskiye yakın — kullanıcı isteği).
  DÜŞMAN TÜRLERİ: her E/F yeri `pick_enemy(kinds, t, banned)` ile settings `WALKER_KINDS` (walker/slime/spiky/cannon) /
  `FLYER_KINDS` (bat/bee) ağırlıklarıyla (başta, en zorda) bir türe dönüşür. KULLANICI KARARI: düşman ORANI (sayısı) böyle
  kalsın — yeni tür eklenince sayı artmaz, var olan yerlerin türü değişir. Sümük: platformun iki üstünde katı varsa gelmez. TOPÇU platformun KENARINA konmaz (`Level.cannon_spot`: iç karelerden E'ye en yakını; yoksa gelmez) — kıpırdamadığı ve boyu + 3 blok zıplamadan yüksek olduğu için kenarda dururken alttan gelen o platforma inemiyordu (Ultra 5. bölüm 31 m, kullanıcı geçemedi).
  Arı: `bee_path(rows, top, row, col)` (chunks `column_span` + `BEE_RANGE`; alttaki platformda (2 satıra kadar) duran
  karakterin kafasına inmesin diye `PLAYER_HEIGHT` kadar kısaltılır; `BEE_MIN_PATH` bloktan kısaysa None → yarasa). Tile/Platform/Coin resimleri `level.image()`
  ile bir kere hazırlanıp paylaşılır; `Coin.update()` dönme animasyonu., `bottom` = en alttaki parçanın altı, `width` piksel.
- `score.py` — `Score(start_y, record, goal)` (goal = bölümde bayrak yüksekliği: `draw` "37 / 62 m" + altın + ilerleme çubuğu): `height` = üstüne basılan en yüksek yer (blok = ekranda "m", sadece `on_ground`
  iken sayılır, düşünce azalmaz), `coins`, `gems` (haritada toplanan elmas), `enemies`, `total` = height × `HEIGHT_POINTS`
  + coins × `COIN_POINTS` + gems × `GEM_POINTS` + enemies × `ENEMY_POINTS`; `loot_text()` = "Altın: 5" (elmas varsa
  "   Elmas: 1" eklenir; HUD ve oyun sonu ekranları). ASIL HEDEF YÜKSEKLİK (kullanıcı kararı: oyuncu kendi tırmanış rekorunu geçmek ister):
  `draw(screen)` sol üstte BÜYÜK "37 m", altında küçük "Puan / Altın" (kameradan bağımsız); `record` = oyun
  başındaki yükseklik rekoru, `new_record` = geçildi mi; `update(player)` rekor o an kırıldıysa True döner
  (main "powerup" sesi çalar) ve `toast` = `RECORD_TOAST_TIME` kare "YENİ REKOR!" (ilk oyunda, rekor 0 iken yok);
  `draw_record_line(screen, camera)` haritada rekor yüksekliğinde kesikli çizgi + "Rekor N m" (draw_world, gökten hemen sonra);
  `draw_lives(screen, lives, max_lives)` sağ üstte, durdur düğmesinin solunda kalpler (kaybedilen can gri); `draw_powers(screen, player)` kalplerin
  altında süren güçlendirmelerin simgesi + süre çubuğu (son `POWERUP_WARN_TIME` karede yanıp söner); `draw_text(screen, font, text,
  color, center=/topleft=...)` gölgeli yazı (her yerde bu kullanılır; yazıyı `lang.t` ile seçili dile ÇEVİRİR; resimleri
  `TEXT_CACHE`'te, her karede yeniden yazılmaz).
- `lang.py` — DİL (kullanıcı kararı: İngilizce eklensin, web oyun sitelerindeki oyuncuların çoğu Türk değil). `t(text,
  count=None)`: Türkçe yazı anahtar, `EN` sözlüğünde İngilizcesi (tekil/çoğul farkı olanda ikili, `count` ile seçilir);
  Türkçede ya da çevirisi yoksa aynen. Kurallar: sabit yazı doğrudan `draw_text`'e (kendisi çevirir); sayılı yazı
  `t("Rekor: {} m").format(n)` (f-string ÇEVRİLEMEZ); değişkende saklanıp sonra çizilen yazı `mark("...")` (sadece
  check_lang bulsun diye). Bölüm (stage) İngilizcede "Level". `LANGUAGES` (tr, en), `set_language`, `language()`,
  `device_language(web)` (web: `navigator.language`, bilgisayar: `locale.getlocale()` "Turkish_Türkiye"/"tr_TR"; Türkçe
  değilse İngilizce). OYUNUN ADI "Platformin" (iki dilde aynı; kullanıcı seçti, 2026-10-09 — "Lava Leap" çok kalabalıktı, "Platform Up!"/"Hopcano" istenmedi). Logo tek satır, tamamen altın, harfler bitişik (`LOGO_SPACING` 1).
- `check_lang.py` — çeviri testi (`python check_lang.py`, GitHub'da yayından önce de çalışır): kodda `t`/`mark` ve
  `draw_text`/`draw_title`/`draw_note`/`show_note`'a verilen yazılar + bölüm adı/tanıtımı, skin adı, zorluk adı listeleri →
  her birinin `EN`'de olması, `{}` yer tutucularının aynı olması; bu fonksiyonlara f-string verilmesi HATA. Yeni bir yazı
  listesi (dict) eklenirse değerlerini `mark` ile işaretle ya da check_lang'in `data_texts`'ine ekle. Yazıların ekrana
  sığdığını ölçmek için scratchpad betiği yazılabilir (font boyu × yer); İngilizcesi Türkçesi kadar kısa tutuldu.
- `storage.py` — kalıcı kayıtlar, `STORES` = tür → (dosya, localStorage adı): "height" (`bestheight.txt`, asıl
  rekor), "score" (`highscore.txt`, en yüksek puan) — rekorlar HER MODUN AYRI: `load_record/save_record(..., mode)`,
  "stages" (`stages.json`: `{"stars": [...]}` her bölümün en iyi yıldızı; HER ZORLUĞUN AYRI — `load_dict/save_dict(kind,
  data, mode)`, Orta eski ad, diğerleri `stages-easy.json`...; `main.load_stars(mode)` uzunluğu STAGE_COUNT'a uydurur),
  `names(kind, mode)`: Orta eski adları kullanır, diğerlerinde ada `-easy`/`-hard`/`-ultra` eklenir (ör.
  `bestheight-ultra.txt`; .gitignore ve pygbag.ini'de de var), "stats" (`stats.json`: games/climbed/coins/enemies toplamları),
  "options" (`options.json`: muted, difficulty, music_volume, effects_volume), "skins" (`skins.json`: coins + gems =
  cüzdan, owned, selected, known — bkz. skins.py `Wardrobe`), "ads" (`ads.json`: day + free_gems = bugün reklamla kaç
  kez bedava elmas alındı). `load_record/save_record` (sayı), `load_dict(kind, defaults)/save_dict`
  (JSON; eksik/bozuk/yanlış tipli değer → default). Dosyalar oyun klasöründe, git ve pygbag dışı; okunamazsa
  default, yazılamazsa sessiz; web'de (`settings.WEB`, `sys.platform == "emscripten"`) `platform.window.localStorage`.
- `ui.py` — `draw_box(screen, rect, fill, border, width, radius)`: düğme/kutu/sekme çizimi (Nostalji düz, Modern
  `modern.box_image`; düğmeler, bölüm kutuları, sekmeler, skin kutuları, bilgi kutusu hep bununla).
  `Buttons(actions, top, gap)`: alt alta ortalı düğmeler; `handle_event(event)` basılan düğmenin adını
  döndürür (dokunma `FINGERDOWN`, sol tık, klavye ↑↓/W-S + Enter/Boşluk; `MOUSEMOTION` ile seçili olan değişir;
  `focus` = seçili); `draw(screen, labels, disabled=())` (disabled = gri, basılamaz görünen düğmeler). `take_click()`: `BUTTON_CLICK_GAP` ms içindeki ikinci tıklama sayılmaz
  (telefonda bir dokunuş hem parmak hem fare olayı gelebilir; ör. menüden dönünce alttaki düğmeye de basılıyordu).
  `PauseButton` oyunda sağ üstte ⏸ (`clicked(event)`). `StageGrid(count, modes, back_top)`: üstte zorluk sekmeleri,
  bölüm kutuları (4 sütun) + Geri; `handle_event(event, unlocked, mode)` → sıra / "locked" / "back" / zorluk adı (sekme);
  `set_focus(i)` (-1 = sekmeler: sağ/sol zorluğu değiştirir, count = Geri); `draw(screen, stars, unlocked, mode)`. `Slider(center_y)` kaydırma çubuğu: `value` 0..`VOLUME_STEPS`,
  parmak/fareyle sürükle veya dokun (`handle_event` → değişti mi), `nudge(±1)` klavye için. Düğme renk/boyları settings "Menü düğmeleri".
- `screens.py` — `SOUND_MENU` (`SoundMenu`: AYARLAR ekranı (eski adı Ses Ayarları; ana menüde "sound_menu" düğmesi
  "Ayarlar"); Müzik + Efektler çubukları, "sound" (Ses: Açık/Kapalı), "language" (Dil: Türkçe / Language: English —
  main `next_language()`, options `language`, boş = cihaz dili), "theme" (Tema: Nostalji / Modern — theme.py) ve "back"
  düğmeleri; ↑↓ seçer, ←→ çubuğu ayarlar; `handle_event` → "music"/"effects"/"sound"/"language"/"theme"/"back"),
  her ekranın `Buttons`'ı (`MAIN_BUTTONS` play/skins/difficulty/howto/records/sound_menu — 6 düğme, `gap=60`; web'de
  altta "Düşük Güç Modu" yazısı olduğu için daha fazla düğme sığmaz, `BACK_BUTTON`,
  `PAUSE_BUTTONS` resume/sound/menu, `PLAY_BUTTONS` stages/endless/back, `STAGE_GRID`, Devam Et: `revive_buttons(ad)`
  (`REVIVE_BUTTONS` revive/give_up, reklam varsa `REVIVE_AD_BUTTONS` revive/revive_ad/give_up), oyun sonu:
  `end_buttons(kind, double)` → `END_BUTTONS[(game_over|clear|last_clear, 2 kat teklifi var mı)]` (2 kat = "double", hep
  en altta); oyun sonu ekran fonksiyonları düğme ÇİZMEZ, main `draw_end_buttons(screen, buttons, stage_failed, double,
  earned)` ile çizer (`DOUBLE_LABELS`; ▶ = `ad_icon()`, `draw_button_icons`), `draw_note` = alttaki kısa bilgi kutusu), bölüm ekranları: `draw_play_select` (Sonsuz Oyun düğmesinin altında seçili zorluğun "Rekor: N m"si), `draw_stages` (seçili bölümün adı + hedefi; KİLİTLİ bölümün de adı asma kilitle yazar
  ama hedefi gizli — kullanıcı: "merak uyandırsın"),
  ekran fonksiyonları `mode` alır (`STAGE_SETS[mode]`), `stage_title(mode, index)`;
  `draw_stage_intro` (bölüm başında ad + intro + hedef), `draw_stage_clear(screen, mode, index, result, shown)` (yıldızlar
  sırayla, 3 şart: bayrak / altın ≥ `stars_needed(total)` (`STAR_COIN_SHARE`) / hiç can kaybetmeden), `draw_stage_failed`, `LABELS` sabit yazılar (değişenleri main
  verir); `draw_main_menu` (logo = `title.draw_logo`, "Rekor: N m", düğmeler, web'de HEP `draw_slow_hint` — kullanıcı isteği),
  `draw_howto` (kontroller + `HOWTO_ROWS`: oyundaki resimlerle her şeyin açıklaması — yeni öğe eklenince buraya da
  ekle; 15 satır `HOWTO_TOP` (198) / `HOWTO_GAP` (29) ile sığıyor, daha fazlası için aralık daralt; `HOWTO_WARN_ROWS` sarı yazı), `draw_records(best_heights, high_scores, stats, current)` (her modun tırmanış + puan rekoru, seçili mod sarı; altında
  tüm modların toplamları), `draw_pause`, `draw_game_over(screen, score, mode_name, ...)` (başlık altında "Zorluk: ...";
  düğmeleri main çizer: `draw_end_buttons`). `draw_new_skins(screen, skinler, y)`: oyun sonu ekranlarında (`NEW_SKIN_Y` = durum → y)
  görevi yeni tamamlanan efsanevinin küçük resmi + "Yeni karakter: Ejderha!". `draw_gems_earned(screen, found, bonus,
  reason, y)`: `gems_text` ile nereden geldiği (uzunsa küçük yazı; `GEMS_EARNED_Y`: game_over / stage_failed / stage_clear).
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
  `level/player/camera/score`; `state`: "title" (giriş ekranı, oyun bununla açılır; `title` = `TitleScreen`, dokununca
  "spring" sesi, geçiş bitince "menu" ve `title = None`; geçişte menü çizilip üstüne `title.draw_fading`) →
  "menu" (ana menü) ↔ "sound"/"howto"/"records" (Geri/ESC);
  ses çubuğu oynayınca `change_volume` (ses kapalıysa açar, kaydeder, efektte örnek "coin" sesi çalar); menü "play" →
  `start()` → "playing" ↔ "paused" (⏸ düğmesi, ESC veya P; durunca Devam/Ses/Ana Menü); can biter → `lose()`:
  DEVAM ET (oyun başına bir kez — `revived`, cüzdanda `REVIVE_GEMS` elmas varsa; sonsuz ve bölüm) → "revive" durumu:
  oyun donar, `screens.draw_revive` (yükseklik, "Rekora / Bayrağa N m kaldı!", geri sayım çubuğu, `REVIVE_BUTTONS`
  Devam Et / Hayır — `GAME_OVER_DELAY` kare sonra çıkar, ölürken basılan tuş elması harcamasın; cüzdan). Devam Et →
  `revive()`: `wardrobe.spend("gems", ...)`, 1 can, `respawn()`, `REVIVE_INVINCIBLE`, lav `push_back`, müzik baştan.
  Hayır / ESC / `REVIVE_TIME` bitince → `game_over()` → "game_over"
  (`GAME_OVER_DELAY` kare düğme yok; `finish()` burada) → Tekrar Oyna (`start()`) / Ana Menü (`to_menu()`).
  REKLAMLAR (ödüllü, oyuncu seçer; `ads` = `ads.Ads`): `ads_allowed()` = reklam var VE bu açılışta `session_games` ≥
  `ADS_AFTER_GAMES`. Devam Et'te `revive_ad` (None/"offer"/"failed"): elmas yetmese de reklamla teklif çıkar (Devam Et
  gri, reklam düğmesi seçili). Oyun sonunda `offer_double()` (game_over ve clear_stage'de finish'ten sonra): kazanılan
  elmas > 0 ise `double` = "offer" → "2 Kat: +N" → reklam → elmas bir daha ("done", gri "+N elmas alındı!"). Karakterler
  ekranında `free_gems_offer()` → `SKIN_MENU.offer`. `watch_ad(reward)` → "ad" durumu (oyun durur, `ads.draw`; ses
  `quiet_for_ad` ile kısılır) → `end_ad(watched)`: ödül ya da "Şu an reklam yok" (`show_note`, `NOTE_TIME`) + düğme
  "failed" (gri). `web_hash()` = web adresinin # sonrası (`#fps`, `#reklam`). `finish()` oyun bitince
  (kaybedince VE durdurup ana menüye dönünce) rekorları + istatistikleri kaydeder. `handle_event`, `update(steps, touch)`,
  `draw(...)`. M tuşu her yerde `toggle_sound()` (kaydedilir).
  BÖLÜM AKIŞI: menü "play" → "play_select" (Bölümler / Sonsuz Oyun / Geri) → "stages" (`open_stages()`; arkada sonsuz harita)
  → `start(index)` (`Game.stage` = seçili zorluğun listesinde sıra, None = sonsuz; `Game.stages`/`Game.stars` seçili
  zorluğunkiler, `stage_stars` = mod → liste, `all_stars()` toplam; sekme → `set_difficulty(mode)`; `intro` = `STAGE_INTRO_TIME`) → bayrağa değince `clear_stage()`
  → "stage_clear" (`clear_result`, `stars_shown`, `STAGE_CLEAR_DELAY`; "win" sesi) → Sonraki/Tekrar/Bölümler. Bölümde can
  biterse `draw_stage_failed` (Tekrar Dene / Bölümler); durdurunca "menu" düğmesi "Bölümler" yazar, `to_menu()` bölümdeyse
  `open_stages()`. `unlocked(i)`: ilki hep açık, sonraki önceki ≥1 yıldızla (`UNLOCK_ALL_STAGES` deneme için). `finish()`
  bölümde sonsuz rekorlarına dokunmaz, sadece istatistik. `Player.hurts` = can kaybı sayısı (3. yıldız). ESC ana menüde oyundan çıkar (web'de hariç).
  `next_difficulty()` Kolay→Orta→Zor→Ultra Zor (`DIFFICULTY_NAMES`), kaydeder ve `reset()` (arkadaki bölüm yeni moda göre).
  SKİNLER: `wardrobe` (`skins.Wardrobe`; açılışta giyilen skin artık açık değilse klasiğe döner), `progress()` = görev
  sayıları (stats toplamları, `all_stars()` toplamı, `height-<mod>` = her modun tırmanış rekoru); menü "skins" → "skins"
  durumu (`SKIN_MENU.open(selected)`, `update`'te `SKIN_MENU.update(steps)`) → `choose_skin(action, id)`: "select" →
  `wear(id)` ("coin" sesi; menünün arkasındaki karakter de `set_skin` ile değişir), "buy" → `wardrobe.buy` + `celebrate()`
  ("buy" sesi), "locked"/"poor" → "powerdown". `finish(ended=True, gem_bonus=0)` toplanan altını ve elması cüzdana
  ekler (`wardrobe.add_money`); ELMAS ÖDÜLLERİ: sonsuz oyunda rekor kırınca her `GEM_RECORD_METERS` (10) m için 1
  (en az 1, en fazla `GEM_RECORD_MAX` (5); o MODDAKİ İLK oyunda — rekor 0 — YOK: eskiden bütün tırmanış ödül sayılıyordu,
  kullanıcı 2 elmas toplayıp 36 aldı, "bug" sandı; durdurup çıkınca da verilir), bölümde `clear_stage` İLK KEZ kazanılan
  her yıldız için `GEMS_PER_STAR` (aynı yıldızı tekrar almak vermez) → `gems_found` / `gems_bonus` / `gems_reason`
  ("rekor"/"yıldız"; oyun sonu ekranlarında `screens.draw_gems_earned`, nereden geldiğiyle: "+5 elmas: 2 toplandı + 3
  rekor ödülü" — ekranda neden yazmayınca kullanıcı hata sanıyor); `ended` ise
  `new_skins` = `wardrobe.new_unlocks(progress)` (oyun sonu ekranlarında yazar; durdurup ana menüye dönünce `ended=False`
  → bir sonraki oyunun sonunda söylenir). `new_game(..., skin)`; `update_game` sonunda `player.trail.update(...)`,
  `draw_world` izi karakterden hemen önce çizer.
  `update_game(...)` oyun mantığı, `draw_world(...)` dünyayı çizer (her ekranda arkada görünür).
  `main()` `async`: döngü sonunda `await asyncio.sleep(0)` (web için şart), en altta `asyncio.run(main())`.
  Web'de ilk kare çizilince `hide_web_loader()` (sayfanın yükleme ekranını kaldırır, bkz. web.tmpl).
  `new_game(best_height, mode)` yeni rastgele bölüm + karakter + kamera + puan kurar; altınlar
  `spritecollide(player, level.coins, True)` ile toplanır. Düşmana değince `player.old_bottom <= enemy.old_top`
  ise (ve `enemy.spiky` değilse — kirpiye basan yanar) düşman ölür (`STOMP_BOUNCE`); topçu ateş edince (level.shots
  arttıysa) "shoot" sesi; ateş topu değerse `hurt()` (kalkan varsa sadece söner); kalkan (`player.powers["shield"]`) varken değdiği düşman zıplamadan ölür;
  değilse dokunulmaz değilken `hurt()`. `level.bottom`'ın altına düşerse (kalkan olsa da) `hurt()` +
  `respawn()`. Mıknatıs varken her karede `coin.attract(player.rect.center)`. Kalkan sürerken `draw_world`
  karakterin etrafına `art.shield_bubble` çizer. Düşmanın `color`'ı ölünce saçılan parçacıkların rengi.
- `lava.py` — `Lava(mode)` (modda `lava` False ise `active = False`: hiçbir şey yapmaz/çizmez): aşağıdan yükselen lav, `level.lava`'da (new_game kurar). `y` = yüzey; `lava_delay`
  bekler, sonra `blend(lava_speed, lava_speed_max, hardness(-camera.bottom, mode))` hızla yükselir; ekranın en fazla
  `LAVA_MAX_GAP` altında kalır (< `REMOVE_BELOW` → düşen önce lava değer). `update(camera_bottom)`, `touches(rect)`
  (ayak `LAVA_HIT_DEPTH` içerideyse) → main: `hurt()` + `respawn()` + `push_back(ayak)` (lav
  `LAVA_PUSHBACK` aşağı çekilir). Kalkan varsa (kullanıcı isteği) can gitmez: `bounce(SHIELD_LAVA_BOUNCE)` ile
  lavdan fırlar, kalkan kırılır (bir kez kurtarır), lav yine `push_back`. `draw(screen, camera)` her şeyin önünde (`art.lava_frames()` dalga şeridi + düz dolgu);
  ekranın altındayken `LAVA_WARN_DISTANCE` içinde `art.lava_glow()` kızıllık. check_chunks lavı hesaba katmaz.
- `check_chunks.py` — çıkılabilirlik testi: `python check_chunks.py` (~20 sn, çok çekirdekli).
  Gerçek `Player` fiziğiyle (sahte `Controls`) BFS: her parçanın (bitiş parçaları dahil, onlarda zirveye) girişinden (başlangıçta P) tepesine
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
- `art.py` — piksel sanatı (Nostalji teması; modern temada `render` ve `@themed` fonksiyonlar modern.py'ye gider;
  `render(..., zoom)` / `player_frames(skin, zoom)` / `coin_frames(zoom)` / `island_image(zoom)` /
  `platform_image(ends, zoom)` büyük çizer — giriş ekranı ve Karakterler önizlemesi böyle; `resize(image, size)`
  Nostalji'de keskin, Modern'de yumuşak büyütür/küçültür): harf haritası + palet → `render(rows, palette, size)` (her harf
  `PIXEL_SCALE` px, çizim alta-ortaya yaslı; hiç `.` yoksa ve ekran açıksa `convert()` = saydamsız → tarayıcıda
  ~5 kat hızlı çizilir), `shade`/`tint`/`mix` ile tonlar; `player_frames(skin)` (gövde ve renkler skinden,
  bacaklar skinde yoksa `PLAYER_LEGS` — harfi "L", rengi verilmezse "K"; "W"/"E" verilmezse oyunun göz renkleri),
  `enemy_frames()` ({1: sağ, -1: sol} çiftleri), `flyer_frames()` (kanat çırpma), `slime_frames()` (walk1/walk2/squash/jump),
  `spiky_frames()`, `cannon_frames()` ([normal, kızarmış]; `CANNON_MUZZLE_Y` namlu yüksekliği), `fireball_frames()`,
  `bee_frames()`, `flag_frames()` (damalı bayrak), `star_image(filled, size)`, `lock_image()`, `crumble_frames()`
  (sağlam, çatlak, silik), `magnet_image()`, `shield_image()`, `shield_bubble(r)`, `coin_frames()` (dönme), `tile_image()`,
  `platform_image()`, `heart_images()`, `Background` (`SKY_THEMES` gökleri, her `SKY_CHANGE_HEIGHT` px tırmanışta sıradakine
  `SKY_BLEND_HEIGHT` boyunca saydamlıkla geçer, döngüsel; + `STAR_PARALLAX` ile kayan yıldızlar), `island_image()`
  (giriş ekranındaki uçan adacık), logo: `LOGO_FONT` (kalın piksel harfler, çizgi 2 kare; "PLATFORMIN" ve eski ad
  "PLATFORM OYUNU"nun harfleri — `TITLE` değişirse eksik harf eklenmeli, yoksa açılışta hata) + `logo_letters(text, üst, alt)`
  (her kare 2x2 "ince kareye" bölünür, ince kare `LOGO_PIXEL` px: koyu kenar 1, alttaki 3B kalınlık `LOGO_DEPTH` ince
  kare; içi renk geçişli, çizgilerin üst kenarı parlak; harf başına (resim, parıltı, x)).
- `theme.py` — GÖRÜNÜŞ TEMASI (kullanıcı kararı, 2026-10-10: NSS adlı oyundaki gibi eski usul + modern iki görünüş):
  "retro" = Nostalji (piksel sanatı, VARSAYILAN), "modern" = yumuşak kenarlı, renk geçişli, parlak (modern.py). Ayarlar
  ekranında "Tema: Nostalji / Modern" (main `next_theme()`, options `theme`, EN "Theme: Retro / Modern"). Sadece görünüş:
  resim boyları ve oyun aynı. `current()`, `modern()`, `set_theme()`, `cached(store, key, make)` = resmi temaya göre bir
  kere hazırla — resim saklayan HER yer bunu kullanır (level.IMAGES, enemy.FRAMES, skins.frames, score kalpleri/yazıları,
  screens._images, ui._boxes, skin_menu.cache, title._logo, lava.IMAGES, main.SHIELD_BUBBLE/DEPTH, effects.IMAGES).
  Tema değişince `Game.reset()` (arkadaki harita yeni resimlerle kurulur). Web'de `web_smoothing()`: tuvalin büyütülmesi
  Nostalji'de `pixelated`, Modern'de `auto` (yumuşak). web.tmpl yükleme ekranı da temayı localStorage'dan okur (Modern'de
  altın yumuşak çizilir).
- `modern.py` — MODERN TEMANIN ÇİZİMLERİ. art.py'de `@themed` işaretli fonksiyonların yerine buradaki AYNI ADLI fonksiyon
  çalışır; `art.render()` modern temada `smooth()`'u çağırır → harf haritalı her şey (skinler, düşmanlar, mıknatıs,
  kalkan, kilit...) kendiliğinden yumuşatılır: her harfin bölgesi büyütülüp hafifçe bulanıklaştırılır, her nokta en
  baskın harfin rengini alır (köşeler yuvarlanır), üstüne ışık (`add_light`) ve göz bebeklerine (E) parıltı. Kodla
  çizilenler: blok (üstü dalgalı çimen, sıranın uçları yuvarlak — `Tile/Platform(x, y, ends)`, `level.run_ends`), tahta
  platform (üst yüzey + yan yüz), hareketli/kırılan platform, yay, altın (dönerken daralır), elmas (yüzeyli), kalp,
  yıldız (her boyda keskin), bayrak, ateş topu, lav (+ `lava_body` renk geçişi, `lava_light` ışık), kalkan baloncuğu,
  adacık, gökyüzü (`Background`: bulutsu ışıklar + kenar karartma gökyüzüne işlenir, yuvarlak parlayan yıldızlar, yavaş
  kayan ışık topları, başlangıçta uzakta tepeler `hills_image`), logo (`logo_letters`: pygame yazı tipiyle, renk geçişi
  + koyu kenar + 3B kalınlık), menü kutuları (`box_image` → `ui.draw_box`: gölge, renk geçişi, seçiliyse altın ışık),
  `knob_image`, yazı gölgesi (`text_shadow`, bulanık), parçacıklar (yuvarlak, küçülür), iz parıltıları. Oyunda ayrıca
  (main `draw_shadows`/`draw_glows`): platformların altında gölge, altın ve toplananların arkasında yanıp sönen ışık,
  yerde duranların (`enemy.grounded`) ayağının altında gölge. Her şey AA (4) kat büyük çizilip küçültülür; `bleed`
  saydam kenarların kararmasını önler. KURALLAR: resim boyları Nostalji'dekiyle AYNI olmalı (çarpışma kutuları resimden
  geliyor; kontrol: iki temada her resmi üretip boyları karşılaştıran betik); yeni bir art.py resmi modern'de otomatik
  yumuşar, özel çizim istenirse `@themed` + modern.py'de aynı adlı fonksiyon. Nostalji'nin çıktısı eski kodla PİKSEL
  PİKSEL aynı kaldı (eski commit'i git worktree ile açıp aynı betikle karşılaştırıldı) — Nostalji'ye dokunulmasın.
  WEB HIZI: tarayıcıda (wasm) yarı saydam çizim piksel başına ~15 ns (400x230'luk resim 1,4 ms!), opak (`convert()`)
  çizim neredeyse bedava. `fast(image)` = RLE (`set_alpha(255, RLEACCEL)`): tamamen saydam/opak sıralar ayrılır, aynı
  görüntü 100 kata kadar hızlı (tepeler 1,4 → 0,01 ms) — sabit resimlere uygulanır; her karede `set_alpha` değişen
  resimlere (yıldızlar, ışıklar) UYGULANMAZ. Ölçüm (görünmez Chrome, oyun sırasında bir kare): Nostalji ~1,0 ms, Modern
  ~1,9 ms; işlemci 4 kat yavaşken ikisi de 60 kare/sn, 6 katta Nostalji 60 / Modern ~52. İlk kullanımda resim hazırlama
  (masaüstü): skin başına ~10 ms, gökyüzü ~40 ms, lav ~30 ms.
- `skins.py` — SKİNLER (karakter görünüşleri; SADECE GÖRÜNÜŞ: hitbox/hız/zıplama aynı, rekorlar adil). `SKINS` listesi,
  her biri `skin(id, ad, grup, gövde, renkler, coins/gems, goal, legs, trail, color)`: gövde 10x10 harf (+2 satır bacak:
  `art.PLAYER_LEGS` ya da kendi `legs`'i, ör. hayalet/ahtapot), harfler art.py gibi. Gruplar (`GROUP_NAMES`, ekranda
  sekme): "colors" Renkler (11; klasik karakterin renk/desenleri, `blob_palette(renk, legs)`), "characters" Karakterler
  (15; kedi, kurbağa, penguen, panda, tavşan, mantar, kardan adam, ahtapot, hayalet (yarı saydam: renkte 4. sayı),
  uzaylı, korsan, robot, ninja, şövalye, astronot), "legendary" Efsanevi (7; GÖREVLE açılır, parayla alınmaz, arkasında
  iz bırakır): Şimşek (40 oyun), Ejderha (150 düşman), Kozmik (toplam 2500 m), Tekboynuz (toplam 1000 altın), Kral
  (75 yıldız), Buz (Zor'da 150 m, sonsuz), Gölge (Ultra Zor'da 75 m, sonsuz). Bir grupta en fazla `GROUP_SIZE` (15)
  skin. İKİ PARA (kullanıcı kararı): Renkler `coins=` ALTINLA (50-1200), Karakterler `gems=` ELMASLA (10-200; kullanıcı ödüller kalınca elmas fiyatlarını yükseltmek istedi, ~2 kat); skinde
  `currency` ("coins"/"gems"/None) + `price` (fiyat yazısı skin_menu `PRICE_TEXTS`/`SHORT_TEXTS`). Ucuzdan pahalıya dizili. `goal` = ("games"/"climbed"/"enemies"/"coins"/"stars"/
  "height-<mod>", hedef), `goal_text(goal)` (`GOAL_TEXTS`, çevrilmiş döner). Koyu gökte kaybolan bacaklar için açık renk "L" (lavanta, gece, gökkuşağı).
  `frames(id)` resimleri bir kere hazırlar; `get(id)`, `in_group(g)`. `Wardrobe(lifetime_coins)`: kayıt (storage
  "skins"): `coins` = cüzdandaki altın (ilk açılışta şimdiye kadar toplanan altınlarla başlar — eski oyunlar da sayılsın),
  `gems` = elmas (0'dan başlar), `owned`, `selected`, `known` (görevi tamamlandığı söylenmiş efsaneviler);
  `balance(currency)`, `can_afford(skin)`, `owns(skin, progress)` (`UNLOCK_ALL_SKINS` deneme için hepsi), `spend(currency,
  n)` (yetmezse False; kaydeder — Devam Et de kullanır), `buy` (doğru paradan düşer, giyer de), `select`, `add_money(coins, gems)`, `new_unlocks(progress)`. Eskiden altınla alınmış
  karakterler `owned`'da kalır (kullanıcı kararı: alınanlar kalsın). `check_skins()` açılışta (boy, harf
  renkleri, fiyat/görev). Yeni skin eklerken önizleme betiğiyle büyütülmüş resmine bak (koyu gökte okunuyor mu).
- `skin_menu.py` — KARAKTERLER EKRANI `SKIN_MENU` (`SkinMenu`): üstte grup sekmeleri, ortada koyu panoda önizlenen skin
  2 kat büyük platformda yürüyüp zıplar (efsanevinin izi de görünür), adı + bilgi (giyiliyor / fiyat / "N elmas daha
  topla" / görev ve ilerleme), 5 sütun kutular (sahip olunmayan sönük + fiyat etiketi (altın ya da elmas resmi) ya da kilit;
  giyilende yeşil tik), cüzdan (altın ve elmas resmi + sayı; yetmeyen para kırmızı yanar, `flash_currency`), "Seç /
  Seçili / Satın Al: N (para resmi) / Kilitli" düğmesi, Geri. Kutuya dokunmak
  önizler; sahip olunan skine dokunmak hemen giyer; SATIN ALMAK sadece alttaki düğmeyle (yanlışlıkla alınmasın). Fare
  üstünden geçmek önizlemeyi DEĞİŞTİRMEZ (düğmeye giderken geçilen kutu alınmasın). Klavye: oklar (en üst satırdan
  yukarı = sekmeler, sağ/sol grup değiştirir), Enter (sahip olunmayan kutuda alttaki düğmeye geçer). `handle_event(event,
  wardrobe, progress)` → ("select"/"buy"/"locked"/"poor", id) / "back" / "free_gems" / None; `celebrate()` satın alınca
  konfeti. `offer` > 0 ise cüzdan sola kayar, sağında "▶ +2 (elmas)" düğmesi (`free_rect`; klavye odağı n+2: kutulardan
  aşağı → bu → Seç → Geri).
- `ads.py` — ÖDÜLLÜ REKLAMLAR (para kazanma hazırlığı; kullanıcı kararı: oyuncu reklamı KENDİSİ seçer, zorunlu reklam
  yok): `Ads(test)`: `available()` (reklam sistemi var ve `retry_at` geçti), `show()`, `update(steps)` → "done" /
  "failed" / None, `end(result)` ("failed" → `AD_RETRY_TIME` ms teklif yok), `playing`, `free_gems_left()` /
  `count_free_gems()` (günde `FREE_GEM_ADS`, storage "ads"), `draw(screen)`. ŞİMDİLİK GERÇEK REKLAM YOK (backend None →
  reklam düğmeleri hiç görünmez); `ADS_TEST` ya da web adresi sonu `#reklam` → "test" backend: `AD_TEST_TIME` karelik
  sahte "REKLAM" ekranı, sonra ödül. Platform seçilince (CrazyGames SDK `requestAd("rewarded", {adStarted, adFinished,
  adError})` vb.) sadece buraya bağlayıcı yazılacak: web.tmpl'de JS reklamın durumunu window'a yazar, `update` okur.
- `trail.py` — `Trail(kind, scale)`: efsanevi izleri (kısa ömürlü parçacıklar, çıktıkları yerde kalır; en fazla
  `TRAIL_LIMIT`): "spark" şimşek kıvılcımı + elektrik tozu, "fire" yükselen alev, "stars" yıldız tozu, "gold" dökülen
  altın pırıltı, "snow" süzülen kar, "rainbow" gökkuşağı şeridi (sadece hareket ederken), "shadow" silinen gölgeler
  (resmin düz renkli hâli, BLEND ile; `pygame.mask` kullanılmadı). `update(rect, image, facing)` her adımda,
  `draw(screen, dy)` (dy = kamera kaydırması). Oyunda, giriş ekranında (2 kat) ve Karakterler önizlemesinde kullanılır.
- `title.py` — GİRİŞ EKRANI (kullanıcı isteği: düz "Başlamak için ekrana dokun" kutusu yerine güzel bir ekran):
  `TitleScreen(web, skin)`: gök + parlayan yıldızlar, logo (harfler `DROP_*` ile sırayla yukarıdan düşüp `bounce` ile sekerek
  oturur), uçan adacıkta gezinip arada zıplayan karakter (giyilen skin, `TITLE_SCALE` kat büyük; efsaneviyse izi de —
  fırlarken arkasında kalır), iki yanda dönen altınlar, uçan yarasa,
  dipte lav + kıvılcımlar (`embers`), logonun altında "Lavdan kaç, en yükseğe tırman!", nefes alan "Dokun ve Başla"
  (masaüstünde "Tıkla ve Başla") düğmesi. `handle_event` dokunma/tık/tuş (+ `take_click`) → True; `leaving`: karakter
  `TITLE_LAUNCH_POWER` ile fırlar, `TITLE_LEAVE_TIME` adımda ana menü belirir (`draw_fading`: giriş ekranı `layer`'a
  çizilip altta çizilmiş menünün üstünde silinir), `done` bitti mi. `Logo`/`draw_logo(screen, drop)`: oyunun adı
  (`TITLE.upper().split()` → satırlar, `LOGO_COLORS`), her harf ayrı resim, `LOGO_WAVE` dalgalanma + her `LOGO_SHINE_TIME`
  sn'de çapraz parıltı; zaman `get_ticks` → ana menüdeki logo aynı yerde ve aynı dalgada, geçişte kıpırdamaz.
  Yerleşim sabitleri dosyanın başında; ayarlar settings "Oyunun adı (logo)" ve "Giriş ekranı".
- `sound.py` — `pre_init()` (pygame.init'ten önce; 22050 Hz mono 16 bit; tampon masaüstünde 512,
  web'de `WEB_AUDIO_BUFFER` = 2048 — tarayıcı 512'de cızırdıyordu; tarayıcı frekansı kendisi seçer, 48000), `Sounds()`: efektler
  (jump, coin, stomp, hurt, start, game_over, win, life, spring, crumble, shoot, powerup, powerdown, buy = skin satın alındı,
  gem = elmas toplandı) ve 8 ölçülük döngü müzik (`MELODY`/`BASS` nota
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
- Sonra belki: başka güçlendirmeler (ör. jetpack).
- BÖLÜM MODU yapıldı (2026-10-09; kullanıcı fikri: "Oyna'ya basınca bölümler, biri bitince sonrakinin kilidi açılsın").
  20 bölüm, 3 yıldız, lav bazı bölümlerde, sonsuz oyun da duruyor. Sonra her zorluğa ayrı 20 bölüm (toplam 80;
  canlar Kolay 4, Orta 3, Zor 2, Ultra 1). Kullanıcı oynayıp bölüm zorluğu/sayıları için geri bildirim verecek (stages.py).
- YENİ DÜŞMANLAR yapıldı (kullanıcı dördünü de seçti): zıplayan sümük, dikenli kirpi, ateş atan topçu, dikey uçan arı.
  Düşman sayısı/oranı değişmedi (kullanıcı isteği). Tür sıklığı settings `WALKER_KINDS`/`FLYER_KINDS`.
- ANA MENÜ yapıldı (Oyna, Zorluk, Nasıl Oynanır, Rekorlar, Ses Ayarları (müzik/efekt seviyesi) + oyunda durdur). Web'de menüde "Düşük Güç Modu'nu
  kapat" sabit yazıyor (otomatik ipucu kullanıcının iPhone'unda çıkmamıştı).
- ZORLUK MODLARI yapıldı: Kolay / Orta / Zor / Ultra Zor (kullanıcı Ultra Zor'u istedi), her modun ayrı rekoru.
  Kullanıcı oynayıp sayılar için geri bildirim verecek (settings `DIFFICULTIES`). Ultra'da kıpırdamayan oyuncuya
  lav ~2,2 sn'de yetişir (lav beklemez — kullanıcı seçimi; çok sert gelirse `lava_delay` artırılır).
  Ultra sonsuz 2026-10-10'da sertleştirildi (yukarıda "ULTRA SONSUZ SERTLEŞTİ"); kullanıcı oynayıp geri bildirim verecek.
- GİRİŞ EKRANI yapıldı (kullanıcı: "başlamak için ekrana dokun yerine daha güzel bir şey"): oyunun içinde (title.py,
  masaüstünde de var) + web'de yeni yükleme ekranı + ses kilidi (web.tmpl). Ana menünün başlığı da aynı piksel logo oldu.
  Kullanıcı iPhone'da doğruladı: "Dokun ve Başla"ya basınca müzik geliyor (ses kilidi çalışıyor).
- AYRI AÇILIŞ MÜZİĞİ denendi ve GERİ ALINDI (kullanıcı kararı: "yok eski müziği geri getir"). Giriş ekranı ve menülerde
  yine tek oyun müziği çalıyor (eskisi gibi). Kullanıcı kendisi istemedikçe yeni müzik önerme. Denenen hâli f7d2a8f'de
  (La minör, 120 vuruş). O denemedeki ses üretimini hızlandırma (notalar liste olarak, sesler `map(operator.add)` ile
  toplanır; tarayıcıda 48000 Hz yerine yarı hızda üretip her örneği iki kez yazmak) de onunla geri alındı. Telefonda
  açılış yavaş gelirse oradan alınabilir.
- KARAKTERLER (SKİNLER) yapıldı (2026-10-09; kullanıcı: "oyuna bir sürü skin ekleyeceğiz"). Kullanıcı kararları:
  açılma = ALTIN + GÖREV (çoğu toplanan altınla alınır, en havalıları sadece görevle), çeşit = KARAKTERLER + RENKLER,
  en nadirlerde İZ/PARILTI efekti. Toplam 33 (11 renk, 15 karakter, 7 efsanevi). Ana menüde "Karakterler" düğmesi.
  Skinler sadece görünüş (Claude kararı: fizik/hitbox aynı, yoksa rekorlar ve check_chunks bozulur). Kullanıcı
  oynayıp fiyat/görev zorluğu için geri bildirim verecek. Tarayıcıda (görünmez Chrome) denendi: satın alma,
  localStorage kaydı, iz çalışıyor.
- İKİNCİ PARA: ELMAS (aynı gün; kullanıcı: "fiyatlar çok ucuz, altın harici bir para birimi olmalı"). Kullanıcı kararları:
  elmas haritada nadir (yükseldikçe biraz sık) + başarılar (yeni bölüm yıldızı, sonsuz oyunda rekor); Renkler altınla,
  Karakterler elmasla; "pahalı" (eskinin ~6 katı: ilk skin ~5 oyunda, en pahalısı ~120 oyunda — 100 m'lik oyunla);
  alınan skinler ve cüzdandaki altın kalsın. ÖLÇÜM (30 rastgele harita): 100 m'de haritada ~12 altın ve ~0,7-1 elmas
  (ilk 100 m ~0,7, yükseklerde ~1) çıkar; oyuncu hepsini toplayamaz. Ucuz gelmesinin bir sebebi: cüzdan ilk açılışta
  eski oyunların bütün altınıyla dolmuştu. Elmas yeşil (Türkçe oyunlarda elmas çoğu zaman yeşil; mavi kalkanla
  karışıyordu).
- PARA KAZANMA HAZIRLIĞI (2026-10-09; kullanıcı: "para kazanabileceğim bir sistem"). Oyun hakkı/enerji sistemi YOK
  (oyuncuyu kaçırır; kullanıcı kabul etti). Kullanıcı kararları: platform (CrazyGames web portalı önerildi / Google Play)
  SONRA, önce oyun hazır olsun; oyuncunun SEÇEREK izlediği 3 ödüllü reklama hazırlık ("reklam izle devam et", "elmasları
  2 kat", "bedava elmas"); oyun arası (zorunlu) reklam istenmedi; İngilizce eklenecek. Plan: 1) Devam Et elmasla —
  YAPILDI; 2) reklam yeri (`ads.py`, şimdilik görünmez, `#reklam` ile deneme reklamı) — YAPILDI; 3) İngilizce (`lang.py`)
  — YAPILDI (306 yazı; görünmez Chrome'da en-US tarayıcıda İngilizce, tr-TR'de Türkçe açıldığı doğrulandı). Sırada
  (kullanıcıyla konuşulacak): platform seçimi. (Oyunun adı seçildi: Platformin.) localStorage anahtarları eski adla ("platform-oyunu-...") kalır — değiştirilirse kayıtlar kaybolur.
  CrazyGames kuralları (koda uyulacak): ödülün reklamsız yolu da olsun (elmas), oyun sırasında reklam yok, can her
  gidişte teklif yok, reklam düğmesi Hayır'la aynı boy ve reklam olduğu belli, reklam yoksa düğme görünmesin, reklamda
  ses kısılır. Ayrıca: Basic Launch'ta reklam kapalı (~2 hafta), oyuncular severse Full Launch'ta SDK + reklam + Data
  modülü. Hesaplar (18 yaş, kimlik, banka) ve vergi (mali müşavir) kullanıcının işi.
- TEMA yapıldı (2026-10-10; kullanıcı: "NSS diye bir oyunda old school bir de modern görünüm var, bizimki de aynı
  olacak; varsayılan şu anki (nostalji), bir de modern eklenecek"). Ayarlar → "Tema: Nostalji / Modern". Modern = aynı
  oyunun yumuşak, renk geçişli, gölgeli/ışıklı hâli (theme.py, modern.py). Kullanıcı deneyip geri bildirim verecek
  (beğenmediği öğe modern.py'de tek tek değiştirilebilir). Müzik/sesler iki temada aynı (yeni müzik önerme).
- OYUNCU KAYITLARI (2026-10-09, kullanıcı kararı: şimdilik böyle kalsın): her şey sadece oyuncunun cihazında
  (web: localStorage, bilgisayar: dosya), sunucu yok → kişisel veri toplanmıyor. Sorunlar: cihaz değişince / tarayıcı
  verisi silinince kayıt gider (iPhone Safari uzun süre girilmeyen sitenin verisini silebilir), elmas elle
  değiştirilebilir (sıralama/satış olmadığı için şimdilik zararsız). Platform seçilince bulut kaydı platformun kendi
  sistemiyle bağlanacak (CrazyGames SDK Data modülü / Google Play Saved Games); kendi sunucumuz önerilmedi. Değişecek
  yer sadece `storage.py` `load_text`/`save_text` (bütün kayıtlar oradan geçiyor).
