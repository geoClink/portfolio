#!/usr/bin/env python3
"""Build the translated Stamped! landing pages from the English one.

    python3 tools/stamped/build_translations.py

Reads stamped-app.html and writes stamped-app-<lang>.html for every language in LANGS.
Edit the English page, then re-run this. If an English string no longer exists on the page
(or a language is missing a translation) the script stops and names it, so a changed
sentence never silently stays in English.

Where the translations live:
  es, de, ja                 the T table below, one (english, spanish, german, japanese) row per string
  fr, it, ko, pt, zh         tools/stamped/landing_translations/<lang>.json, shaped
                             {"rows": {english: translation, ...}, "copy": "<the stampedCopy block>"}
                             with the same English keys as column one of T
So when you change an English string: update its T row AND the same key in the five JSON files.

It also sets the ?v= hash on the shared CSS and JS links (SHARED) in all four pages.

It also builds the two small sign-up pages Buttondown redirects to (THANKS_PAGES):
  stamped-check-inbox.html   after someone signs up ("check your inbox")
  stamped-subscribed.html    after they confirm ("you're on the list")
into stamped-check-inbox-<lang>.html and stamped-subscribed-<lang>.html. Strings they share with
the landing page come from T and the JSON files; the rest live in THANKS_T, all eight languages per row.

Wording follows the app's own Localizable.strings (sello / Stempel / スタンプ).

Each entry is (english, spanish, german, japanese). The english string is matched as:
  plain text   -> a whole text node:   >text<
  "@" prefix   -> an attribute value:  ="text"
  "!" prefix   -> anywhere, exactly as written (CSS, JSON, URLs)
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "stamped-app.html"
LANGS = ["es", "de", "ja", "fr", "it", "ko", "pt", "zh"]
TABLE_LANGS = ["es", "de", "ja"]                      # the columns of T, in order
JSON_DIR = ROOT / "tools" / "stamped" / "landing_translations"   # the other languages
STORE = {"es": "es", "de": "de", "ja": "jp", "fr": "fr", "it": "it", "ko": "kr", "pt": "br", "zh": "cn"}  # App Store countries
LOCALE = {"es": "es_ES", "de": "de_DE", "ja": "ja_JP", "fr": "fr_FR", "it": "it_IT", "ko": "ko_KR", "pt": "pt_BR",
          "zh": "zh_CN"}
NAME = {"es": "español", "de": "Deutsch", "ja": "日本語", "fr": "Français", "it": "Italiano", "ko": "한국어",
        "pt": "Português", "zh": "简体中文"}
# The page's file name uses the short code; <html lang> and hreflang use this when it differs
HTML_LANG = {"zh": "zh-Hans"}
# Shared files all four pages link to; each link gets ?v=<hash of the file> (versioned())
SHARED = ["assets/css/stamped-app.css", "assets/js/stamped-app.js"]

T = [
    # ----- <head> -----
    ("Stamped! A City Passport: The World's Great Buildings",
     "Stamped! A City Passport: los grandes edificios del mundo",
     "Stamped! A City Passport: die großen Bauwerke der Welt",
     "Stamped! A City Passport：世界の名建築をスタンプで集めよう"),
    ("@Collect a passport stamp at 2,400+ landmarks in 166 cities and 122 campuses. Fly through them in 3D. Free on iPhone, iPad, Mac and Apple Vision Pro.",
     "Consigue un sello en más de 2.400 monumentos de 166 ciudades y 122 campus. Sobrevuélalos en 3D. Gratis para iPhone, iPad, Mac y Apple Vision Pro.",
     "Sammle Stempel an 2.400+ Bauwerken in 166 Städten und auf 122 Campussen. Fliege in 3D hindurch. Kostenlos für iPhone, iPad, Mac und Apple Vision Pro.",
     "156都市と117キャンパス、2,400以上の名建築でスタンプを集めよう。3Dで飛び回れます。iPhone・iPad・Mac・Apple Vision Proで無料。"),
    ("!\"description\": \"Collect a passport stamp at more than 2,400 architectural landmarks in 166 cities on six continents and 122 university campuses. Fly through cities in 3D, meet the architects, take the quiz, and plan your trip.\"",
     "\"description\": \"Consigue un sello en tu pasaporte en más de 2.400 monumentos de arquitectura en 166 ciudades de seis continentes y 122 campus universitarios. Sobrevuela ciudades en 3D, conoce a los arquitectos, haz el quiz y planifica tu viaje.\"",
     "\"description\": \"Sammle Stempel für deinen Reisepass an mehr als 2.400 Bauwerken in 166 Städten auf sechs Kontinenten und auf 122 Universitätscampussen. Fliege in 3D durch Städte, lerne die Architekten kennen, mach das Quiz und plane deine Reise.\"",
     "\"description\": \"6大陸156都市の2,400以上の名建築と、117の大学キャンパスでパスポートスタンプを集めよう。3Dで街を飛び回り、建築家を知り、クイズに挑戦して、旅を計画。\""),
    ("@2,400+ landmarks, 166 cities, six continents, 122 campuses. Fly through them in 3D and collect a stamp at every one you visit.",
     "Más de 2.400 monumentos, 166 ciudades, seis continentes, 122 campus. Sobrevuélalos en 3D y consigue un sello en cada uno que visites.",
     "2.400+ Sehenswürdigkeiten, 166 Städte, sechs Kontinente, 122 Campusse. Fliege in 3D hindurch und sammle an jedem Ort, den du besuchst, einen Stempel.",
     "2,400以上の名建築、156都市、6大陸、117キャンパス。3Dで飛び回り、訪れた場所ごとにスタンプを集めよう。"),

    # ----- Header -----
    ("Skip to content", "Saltar al contenido", "Zum Inhalt springen", "本文へスキップ"),
    ("@Page sections", "Secciones de la página", "Seitenbereiche", "ページ内のセクション"),
    ("Explore", "Explorar", "Entdecken", "探索"),
    ("Quiz", "Quiz", "Quiz", "クイズ"),
    ("Trips", "Viajes", "Reisen", "旅行"),
    ("Campuses", "Campus", "Campusse", "キャンパス"),
    ("Get the app", "Descargar", "App laden", "アプリを入手"),
    ("Enjoying Stamped!? ", "¿Te gusta Stamped!? ", "Gefällt dir Stamped!? ", "Stamped!を楽しんでいますか？ "),
    ("Leave a tip", "Deja una propina", "Gib ein Trinkgeld", "チップを贈る"),
    ("Get an email when new cities and campuses arrive.", "Recibe un correo cuando lleguen nuevas ciudades y campus.", "Erhalte eine E-Mail, wenn neue Städte und Campusse dazukommen.", "新しい都市やキャンパスが追加されたらメールでお知らせします。"),
    ("Notify me", "Avísame", "Benachrichtige mich", "通知を受け取る"),
    ("A few emails a year. Unsubscribe anytime.", "Unos pocos correos al año. Date de baja cuando quieras.", "Ein paar E-Mails im Jahr. Jederzeit abbestellbar.", "メールは年に数回。いつでも配信停止できます。"),
    # The stamped note that replaces the sign-up form once it's sent
    ("ALMOST THERE", "CASI LISTO", "FAST GESCHAFFT", "あと少し"),
    ("INBOX", "CORREO", "E-MAIL", "メール"),
    ("Check your inbox.", "Revisa tu correo.", "Schau in dein Postfach.", "メールを確認してください。"),
    ("Tap the link in our email to confirm, and you're on the list.",
     "Toca el enlace de nuestro correo para confirmar y ya estarás en la lista.",
     "Tippe zur Bestätigung auf den Link in unserer E-Mail, dann bist du dabei.",
     "メール内のリンクをタップして確認すれば、登録完了です。"),
    ("If the new tab asks you to prove you're human, finish that first.",
     "Si la nueva pestaña te pide demostrar que eres humano, hazlo primero.",
     "Falls der neue Tab fragt, ob du ein Mensch bist, erledige das zuerst.",
     "新しいタブで人間であることの確認を求められたら、先にそちらを済ませてください。"),
    (" to help keep new cities coming.", " para que sigan llegando nuevas ciudades.", ", damit weitere Städte dazukommen.", "で、新しい都市の追加を応援してください。"),
    ("Tip jar", "Propinas", "Trinkgeld", "チップ"),

    # ----- Hero -----
    ("A city passport · Free on iPhone, iPad, Mac &amp; Vision Pro",
     "Un pasaporte de ciudades · Gratis para iPhone, iPad, Mac y Vision Pro",
     "Ein Städte-Reisepass · Kostenlos für iPhone, iPad, Mac &amp; Vision Pro",
     "都市のパスポート · iPhone・iPad・Mac・Vision Proで無料"),
    ("The world's great buildings, ", "Los grandes edificios del mundo, ", "Die großen Bauwerke der Welt, ", "世界の名建築を、"),
    ("stamped.", "sellados.", "gestempelt.", "スタンプで。"),
    ("Fade an old street map over today's city, take a Time Walk that turns the map to the year each landmark was built, and collect a stamp at every building you visit. 2,400 landmarks in 166 cities, ready to explore in 3D.",
     "Superpón un antiguo plano de calles sobre la ciudad actual, haz un recorrido en el que el mapa vuelve al año en que se construyó cada monumento y consigue un sello en cada edificio que visites. 2.400 monumentos en 166 ciudades, listos para explorar en 3D.",
     "Lege einen alten Stadtplan über die Stadt von heute, mach eine Tour, bei der die Karte in das Baujahr jedes Wahrzeichens springt, und sammle an jedem besuchten Gebäude einen Stempel. 2.400 Wahrzeichen in 166 Städten, in 3D zu entdecken.",
     "古い街路図を今の街に重ね、各名建築が建てられた年へ地図が移り変わるツアーを楽しみ、訪れた建物ごとにスタンプを集めましょう。166都市2,400件の名建築を3Dで探索できます。"),
    ("!Download_on_the_App_Store_Badge_US-UK_RGB_blk_092917.svg",
     "Download_on_the_App_Store_Badge_ES_RGB_blk_100217.svg",
     "Download_on_the_App_Store_Badge_DE_RGB_blk_092917.svg",
     "Download_on_the_App_Store_Badge_JP_RGB_blk_100317.svg"),
    ("@QR code that opens Stamped! on the App Store",
     "Código QR que abre Stamped! en el App Store",
     "QR-Code, der Stamped! im App Store öffnet",
     "App StoreでStamped!を開くQRコード"),
    ("On your computer?", "¿Estás en el ordenador?", "Am Computer?", "パソコンでご覧ですか？"),
    ("Scan with your iPhone camera.", "Escanéalo con la cámara de tu iPhone.", "Scanne ihn mit der iPhone-Kamera.", "iPhoneのカメラで読み取ってください。"),
    ("Passport · Stamped!", "Pasaporte · Stamped!", "Reisepass · Stamped!", "パスポート · Stamped!"),
    ("Type P", "Tipo P", "Typ P", "タイプ P"),
    ("!<strong>2,400+</strong>",
     "<strong>2.400+</strong>",
     "<strong>2.400+</strong>",
     "<strong>2,400+</strong>"),
    ("A real Apple Map with Look Around, running right here in your browser. Pick a city, tap a pin, look around at street level and stamp it. The app does the same in photoreal 3D, for 2,400+ landmarks.",
     "Un mapa real de Apple con Look Around, aquí mismo en tu navegador. Elige una ciudad, toca un marcador, mira a pie de calle y séllalo. La app hace lo mismo en 3D fotorrealista, para más de 2.400 monumentos.",
     "Eine echte Apple Karte mit Umsehen, direkt hier im Browser. Wähle eine Stadt, tippe auf eine Nadel, sieh dich auf Straßenhöhe um und stempele sie. Die App macht das Gleiche in fotorealistischem 3D, für 2.400+ Sehenswürdigkeiten.",
     "Look Around付きの本物のAppleマップを、このブラウザで。都市を選んでピンをタップし、ストリートレベルで見回してスタンプを押そう。アプリでは同じことを、2,400以上の名建築でフォトリアルな3Dで楽しめます。"),
    ("!See every school and how the road trip works <i",
     "Ver todas las universidades y cómo funciona el viaje <i",
     "Alle Hochschulen ansehen und wie der Roadtrip funktioniert <i",
     "すべての大学とロードトリップの仕組みを見る <i"),
    ("Stamps you collect here stay in this browser. In the app they sync across your devices with iCloud.",
     "Los sellos que consigues aquí se quedan en este navegador. En la app se sincronizan entre tus dispositivos con iCloud.",
     "Stempel, die du hier sammelst, bleiben in diesem Browser. In der App werden sie über iCloud zwischen deinen Geräten synchronisiert.",
     "ここで集めたスタンプはこのブラウザに保存されます。アプリではiCloudでデバイス間で同期されます。"),
    ("Landmarks", "Monumentos", "Bauwerke", "名建築"),
    ("@Landmarks", "Monumentos", "Bauwerke", "名建築"),
    ("Cities", "Ciudades", "Städte", "都市"),
    ("Continents", "Continentes", "Kontinente", "大陸"),
    ("Countries", "Países", "Länder", "か国"),
    ("Languages", "Idiomas", "Sprachen", "言語"),
    ("@Stamped! flying low over a photoreal 3D Manhattan past the Empire State Building, then dropping to a street-level view of Fifth Avenue",
     "Stamped! sobrevolando a baja altura un Manhattan fotorrealista en 3D junto al Empire State Building y bajando después a pie de calle en la Quinta Avenida",
     "Stamped! im Tiefflug über ein fotorealistisches 3D-Manhattan am Empire State Building vorbei, dann hinunter auf Straßenebene an der Fifth Avenue",
     "Stamped!でフォトリアルな3Dのマンハッタンをエンパイア・ステート・ビルの横を低空飛行し、五番街のストリートビューへ降りていく様子"),
    ("@Pause video", "Pausar vídeo", "Video pausieren", "動画を一時停止"),

    # ----- How it works -----
    ("How it works", "Cómo funciona", "So funktioniert's", "使い方"),
    ("Explore. Go. ", "Explora. Viaja. ", "Entdecken. Reisen. ", "探して、旅して、"),
    ("Stamp.", "Sella.", "Stempeln.", "スタンプ。"),
    ("Explore from your couch", "Explora desde el sofá", "Entdecke vom Sofa aus", "ソファから探検"),
    ("Fly through 166 cities in photoreal 3D and read the story behind every building.",
     "Sobrevuela 166 ciudades en 3D fotorrealista y lee la historia de cada edificio.",
     "Fliege in fotorealistischem 3D durch 166 Städte und lies die Geschichte hinter jedem Bauwerk.",
     "156都市をフォトリアルな3Dで飛び回り、すべての建物の物語を読もう。"),
    ("Plan the trip", "Planifica el viaje", "Plane die Reise", "旅を計画"),
    ("Line up landmarks day by day, add hotels and places to eat, and preview the route in 3D.",
     "Organiza los monumentos día a día, añade hoteles y sitios para comer y previsualiza la ruta en 3D.",
     "Ordne Sehenswürdigkeiten Tag für Tag, füge Hotels und Restaurants hinzu und sieh dir die Route vorab in 3D an.",
     "名建築を日ごとに並べ、ホテルや食事の場所を追加して、ルートを3Dで下見。"),
    ("Fill your passport", "Llena tu pasaporte", "Fülle deinen Reisepass", "パスポートを埋めよう"),
    ("Earn a stamp at every landmark you visit and master a city by stamping all of it.",
     "Consigue un sello en cada monumento que visites y domina una ciudad sellándolos todos.",
     "Sammle an jeder besuchten Sehenswürdigkeit einen Stempel und meistere eine Stadt, indem du alle stempelst.",
     "訪れた名建築ごとにスタンプを獲得し、すべて集めて都市を制覇しよう。"),

    # ----- Continents -----
    ("SIX CONTINENTS", "SEIS CONTINENTES", "SECHS KONTINENTE", "6大陸"),
    ("CITIES", "CIUDADES", "STÄDTE", "都市"),
    ("Six continents · 166 cities",
     "Seis continentes · 166 ciudades",
     "Sechs Kontinente · 166 Städte",
     "6大陸 · 156都市"),
    ("Every continent you can fly to.", "Todos los continentes a los que puedes volar.", "Alle Kontinente, die du anfliegen kannst.", "飛行機で行けるすべての大陸へ。"),
    ("Not just the usual capitals. Stamped! covers 166 cities, from Reykjavik to Zanzibar, each with its own landmarks, quiz and stamp.",
     "No solo las capitales de siempre. Stamped! abarca 166 ciudades, de Reikiavik a Zanzíbar, cada una con sus monumentos, su quiz y su sello.",
     "Nicht nur die üblichen Hauptstädte. Stamped! umfasst 166 Städte, von Reykjavík bis Sansibar, jede mit eigenen Sehenswürdigkeiten, Quiz und Stempel.",
     "定番の首都だけではありません。レイキャビクからザンジバルまで156都市を収録。それぞれに名建築、クイズ、スタンプがあります。"),
    ("Europe ", "Europa ", "Europa ", "ヨーロッパ "),
    ("Asia ", "Asia ", "Asien ", "アジア "),
    ("North America ", "Norteamérica ", "Nordamerika ", "北米 "),
    ("South America ", "Sudamérica ", "Südamerika ", "南米 "),
    ("Africa ", "África ", "Afrika ", "アフリカ "),
    ("Oceania ", "Oceanía ", "Ozeanien ", "オセアニア "),
    ("28 cities",
     "28 ciudades",
     "28 Städte",
     "28都市"),
    ("36 cities",
     "36 ciudades",
     "36 Städte",
     "36都市"),
    ("35 cities",
     "35 ciudades",
     "35 Städte",
     "35都市"),
    ("15 cities", "15 ciudades", "15 Städte", "15都市"),
    ("11 cities", "11 ciudades", "11 Städte", "11都市"),
    ("5 cities", "5 ciudades", "5 Städte", "5都市"),
    ("Paris, Rome, Barcelona, London, Prague, Istanbul, Reykjavik, Tbilisi…",
     "París, Roma, Barcelona, Londres, Praga, Estambul, Reikiavik, Tiflis…",
     "Paris, Rom, Barcelona, London, Prag, Istanbul, Reykjavík, Tiflis…",
     "パリ、ローマ、バルセロナ、ロンドン、プラハ、イスタンブール、レイキャビク、トビリシ…"),
    ("Tokyo, Kyoto, Seoul, Singapore, Dubai, Mumbai, Kathmandu, Xi'an…",
     "Tokio, Kioto, Seúl, Singapur, Dubái, Bombay, Katmandú, Xi'an…",
     "Tokio, Kyoto, Seoul, Singapur, Dubai, Mumbai, Kathmandu, Xi'an…",
     "東京、京都、ソウル、シンガポール、ドバイ、ムンバイ、カトマンズ、西安…"),
    ("New York, Chicago, Mexico City, Havana, Toronto, Honolulu, Detroit…",
     "Nueva York, Chicago, Ciudad de México, La Habana, Toronto, Honolulu, Detroit…",
     "New York, Chicago, Mexiko-Stadt, Havanna, Toronto, Honolulu, Detroit…",
     "ニューヨーク、シカゴ、メキシコシティ、ハバナ、トロント、ホノルル、デトロイト…"),
    ("Rio de Janeiro, Buenos Aires, Brasília, Lima, Cartagena, Medellín…",
     "Río de Janeiro, Buenos Aires, Brasilia, Lima, Cartagena, Medellín…",
     "Rio de Janeiro, Buenos Aires, Brasília, Lima, Cartagena, Medellín…",
     "リオデジャネイロ、ブエノスアイレス、ブラジリア、リマ、カルタヘナ、メデジン…"),
    ("Cairo, Marrakech, Cape Town, Lagos, Nairobi, Addis Ababa, Zanzibar…",
     "El Cairo, Marrakech, Ciudad del Cabo, Lagos, Nairobi, Adís Abeba, Zanzíbar…",
     "Kairo, Marrakesch, Kapstadt, Lagos, Nairobi, Addis Abeba, Sansibar…",
     "カイロ、マラケシュ、ケープタウン、ラゴス、ナイロビ、アディスアベバ、ザンジバル…"),
    ("Sydney, Melbourne, Brisbane, Auckland, Queenstown",
     "Sídney, Melbourne, Brisbane, Auckland, Queenstown",
     "Sydney, Melbourne, Brisbane, Auckland, Queenstown",
     "シドニー、メルボルン、ブリスベン、オークランド、クイーンズタウン"),
    ("Browse all 166 city guides ", "Ver las 166 guías de ciudades (en inglés) ", "Alle 166 Stadtführer ansehen (auf Englisch) ", "166都市のガイドを見る（英語） "),

    # ----- 3D map and Look Around -----
    ("Explore · Photoreal 3D + Look Around", "Explorar · 3D fotorrealista + Mirar alrededor", "Entdecken · Fotorealistisches 3D + Umsehen", "探索 · フォトリアル3D + Look Around"),
    ("From the sky ", "Del cielo ", "Vom Himmel ", "空から、"),
    ("to the street.", "a la calle.", "auf die Straße.", "街角へ。"),
    ("Satellite imagery over real building heights. Tap a pin and the camera flies straight to it, or start a guided tour that flies between every landmark for you. Then drop to street level and see exactly what a building looks like before you get there.",
     "Imágenes de satélite sobre las alturas reales de los edificios. Toca un pin y la cámara vuela directo hacia él, o inicia una visita guiada que vuela de un monumento a otro por ti. Después, baja a pie de calle y mira cómo es un edificio antes de llegar.",
     "Satellitenbilder über echten Gebäudehöhen. Tippe auf eine Stecknadel und die Kamera fliegt direkt hin, oder starte eine geführte Tour, die dich von Sehenswürdigkeit zu Sehenswürdigkeit fliegt. Dann geht es hinunter auf Straßenebene, damit du siehst, wie ein Gebäude aussieht, bevor du dort bist.",
     "実際の建物の高さに衛星画像を重ねた3Dマップ。ピンをタップすればカメラがまっすぐ飛んでいき、ガイドツアーを始めればすべての名建築を自動でめぐります。さらに地上に降りて、到着前に建物の見た目を確認できます。"),
    ("Step through landmarks in walking order right from the map card",
     "Recorre los monumentos en orden a pie desde la tarjeta del mapa",
     "Geh die Sehenswürdigkeiten direkt in der Kartenansicht in Laufreihenfolge durch",
     "マップのカードから、歩く順に名建築をたどれる"),
    ("Filter by not visited, stamped, want to visit and architectural style",
     "Filtra por no visitados, sellados, quiero visitar y estilo arquitectónico",
     "Filtern nach nicht besucht, gestempelt, Wunschziele und Baustil",
     "未訪問・スタンプ済み・行きたい場所・建築様式で絞り込み"),
    ("Chips for food, coffee, culture and places to stay",
     "Accesos rápidos a comida, café, cultura y alojamiento",
     "Schnellfilter für Essen, Kaffee, Kultur und Unterkünfte",
     "食事・カフェ・カルチャー・宿泊のショートカット"),
    ("@3D map of New York with a card for the Empire State Building, a Look Around preview and Stamp, Want to Go and Add to Trip buttons",
     "Mapa 3D de Nueva York con la tarjeta del Empire State Building, una vista previa de Mirar alrededor y los botones Sellar, Quiero ir y Añadir al viaje",
     "3D-Karte von New York mit einer Karte zum Empire State Building, einer Umsehen-Vorschau und den Tasten Stempeln, Wunschziel und Zur Reise hinzufügen",
     "エンパイア・ステート・ビルのカード、Look Aroundのプレビュー、スタンプ・行きたい・旅行に追加ボタンがあるニューヨークの3Dマップ"),
    ("Fly in", "Sobrevuela", "Hinfliegen", "飛んでいく"),
    ("Every landmark on a 3D map.", "Todos los monumentos en un mapa 3D.", "Jede Sehenswürdigkeit auf einer 3D-Karte.", "すべての名建築を3Dマップで。"),
    ("@Street-level Look Around view of the glass cube at Apple Fifth Avenue in Manhattan",
     "Vista a pie de calle con Mirar alrededor del cubo de cristal de Apple Fifth Avenue en Manhattan",
     "Umsehen-Ansicht auf Straßenebene vom Glaswürfel des Apple Store Fifth Avenue in Manhattan",
     "マンハッタンのApple Fifth Avenueのガラスキューブを地上から見たLook Aroundの画面"),
    ("Walk the street", "Recorre la calle", "Lauf die Straße entlang", "街を歩く"),
    ("So you never walk right past it.", "Para no pasar de largo nunca más.", "Damit du nie wieder daran vorbeiläufst.", "もう見過ごさない。"),

    # ----- Architects -----
    ("Discover · The people behind the buildings", "Descubre · Las personas detrás de los edificios", "Entdecken · Die Menschen hinter den Bauwerken", "発見 · 建物をつくった人たち"),
    ("Meet the ", "Conoce a los ", "Triff die ", ""),
    ("architects.", "arquitectos.", "Architekten.", "建築家に会おう。"),
    ("History · Old maps and old photos", "Historia · Mapas y fotos antiguos", "Geschichte · Alte Karten und alte Fotos", "歴史 · 古地図と古い写真"),
    ("See the city ", "Mira la ciudad ", "Sieh die Stadt, ", "あの頃の"),
    ("as it was.", "como era.", "wie sie war.", "街を見る。"),
    ("Fade a street map from 1850, 1900, 1925 or 1950 over today's satellite view. Press Time Walk and, as the tour moves on, the map turns to the year each landmark was built.", "Funde un mapa de calles de 1850, 1900, 1925 o 1950 con la vista por satélite de hoy. Pulsa Paseo en el tiempo y, a medida que avanza el recorrido, el mapa cambia al año en que se construyó cada monumento.", "Blende einen Stadtplan von 1850, 1900, 1925 oder 1950 über das heutige Satellitenbild. Tippe auf Zeitreise, und während der Tour springt die Karte in das Baujahr jedes Bauwerks.", "1850年、1900年、1925年、1950年の街路図を、現在の衛星写真に重ねてフェードできます。タイムウォークを押すと、ツアーの進行に合わせて地図が各ランドマークの建設年に変わります。"),
    ("Old photos from public archives, each one credited", "Fotos antiguas de archivos públicos, todas con su crédito", "Alte Fotos aus öffentlichen Archiven, jedes mit Quellenangabe", "公共アーカイブの古い写真を、すべてクレジット付きで"),
    ("Ask a landmark a question and hear it answer, with Apple Intelligence", "Hazle una pregunta a un monumento y escucha su respuesta, con Apple Intelligence", "Stelle einem Bauwerk eine Frage und höre die Antwort, mit Apple Intelligence", "ランドマークに質問して答えを聞けます（Apple Intelligence対応）"),
    ("Step into the Past: public-domain films and old photos of the city", "Entra en el pasado: películas de dominio público y fotos antiguas de la ciudad", "Tauche in die Vergangenheit ein: gemeinfreie Filme und alte Fotos der Stadt", "過去へ：パブリックドメインの映画と街の古い写真"),
    ("City street sounds under the tour", "Sonidos de la calle durante el recorrido", "Straßengeräusche der Stadt während der Tour", "ツアー中に流れる街の音"),
    ("On This Day: what happened at the app's landmarks today", "Un día como hoy: qué pasó hoy en los monumentos de la app", "An diesem Tag: was heute an den Bauwerken der App geschah", "今日は何の日：アプリのランドマークで今日起きた出来事"),
    ("The same streets, decades apart.", "Las mismas calles, décadas después.", "Dieselben Straßen, Jahrzehnte später.", "同じ通りの、数十年の違い。"),
    ("Old photos", "Fotos antiguas", "Alte Fotos", "昔の写真"),
    ("Every one credited.", "Todas con su crédito.", "Alle mit Quellenangabe.", "すべてクレジット付き。"),
    ("@London's 1900 street map faded over today's satellite view, with landmark pins", "Mapa de calles de Londres de 1900 fundido con la vista por satélite actual, con marcadores de monumentos", "Londoner Stadtplan von 1900 über dem heutigen Satellitenbild, mit Stecknadeln für Bauwerke", "現在の衛星写真に重ねた1900年のロンドンの街路図とランドマークのピン"),
    ("@A row of old drawings of St Paul's Cathedral, each with its credit underneath", "Una fila de dibujos antiguos de la catedral de San Pablo, cada uno con su crédito debajo", "Eine Reihe alter Zeichnungen der St Paul's Cathedral, jede mit Quellenangabe darunter", "セント・ポール大聖堂の古い図面の列、それぞれの下にクレジット"),
    ("Then &amp; Now", "Antes y ahora", "Damals &amp; heute", "今と昔"),
    ("Every landmark comes with its architect, style, build date, height and history. Tap an architect to see all their buildings in the app. Stamped! keeps track of whose buildings you've seen and shows your favorite architect.",
     "Cada monumento incluye su arquitecto, estilo, fecha de construcción, altura e historia. Toca un arquitecto para ver todos sus edificios en la app. Stamped! recuerda de quién son los edificios que has visto y te muestra tu arquitecto favorito.",
     "Zu jeder Sehenswürdigkeit gibt es Architekt, Stil, Baujahr, Höhe und Geschichte. Tippe auf einen Architekten, um alle seine Bauwerke in der App zu sehen. Stamped! merkt sich, wessen Bauwerke du gesehen hast, und zeigt deinen Lieblingsarchitekten.",
     "名建築ごとに建築家、様式、建築年、高さ、歴史を紹介。建築家をタップすると、アプリ内のその人の建物がすべて見られます。Stamped!は見た建物の建築家を記録し、お気に入りの建築家を表示します。"),
    ("@Some of the architects in Stamped!, with how many of their buildings are in the app",
     "Algunos de los arquitectos de Stamped!, con cuántos de sus edificios hay en la app",
     "Einige Architekten in Stamped! und wie viele ihrer Bauwerke in der App sind",
     "Stamped!に登場する建築家の一部と、アプリ内の作品数"),
    ("@Landmarks span from 2560 BC to 2026", "Los monumentos van del 2560 a. C. a 2026", "Die Sehenswürdigkeiten reichen von 2560 v. Chr. bis 2026", "紀元前2560年から2026年までの名建築"),
    ("2560 BC", "2560 a. C.", "2560 v. Chr.", "紀元前2560年"),
    ("Great Pyramid of Giza", "Gran Pirámide de Guiza", "Cheops-Pyramide von Gizeh", "ギザの大ピラミッド"),
    ("Waterline, Austin", "Waterline, Austin", "Waterline, Austin", "ウォーターライン（オースティン）"),
    ("@4,500+ years", "más de 4.500 años", "über 4.500 Jahre", "4,500年以上"),
    ("@My Journey screen with 171 stamps, cities visited and mastered, and a favorite architect card for Albert Kahn",
     "Pantalla Mi viaje con 171 sellos, ciudades visitadas y dominadas, y Albert Kahn como arquitecto favorito",
     "Bildschirm Meine Reise mit 171 Stempeln, besuchten und gemeisterten Städten und Albert Kahn als Lieblingsarchitekt",
     "171個のスタンプ、訪れた都市と制覇した都市、お気に入りの建築家アルバート・カーンを表示したマイジャーニー画面"),
    ("FAVORITE ARCHITECT", "ARQUITECTO FAVORITO", "LIEBLINGSARCHITEKT", "お気に入りの建築家"),

    # ----- Quiz -----
    ("Play · Architecture quiz", "Juega · Quiz de arquitectura", "Spielen · Architektur-Quiz", "遊ぶ · 建築クイズ"),
    ("Test your ", "Pon a prueba ", "Teste dein ", "あなたの"),
    ("smarts.", "lo que sabes.", "Wissen.", "知識を試そう。"),
    ("Every city and every campus has its own 10-question quiz built from its real landmarks: the style, the year, the architect, the number of floors. 273 quizzes in all, in 9 languages. Tap your answer or say it out loud.",
     "Cada ciudad y cada campus tiene su propio quiz de 10 preguntas sobre sus monumentos reales: el estilo, el año, el arquitecto, el número de plantas. 273 quizzes en total, en 9 idiomas. Toca tu respuesta o dila en voz alta.",
     "Jede Stadt und jeder Campus hat ein eigenes Quiz mit 10 Fragen zu den echten Bauwerken: Stil, Baujahr, Architekt, Anzahl der Stockwerke. 273 Quizze insgesamt, in 9 Sprachen. Tippe deine Antwort an oder sag sie laut.",
     "各都市・各キャンパスに、実在の名建築から作った10問のクイズがあります。様式、建築年、建築家、階数。全273クイズ、9言語に対応。タップでも声でも答えられます。"),
    ("Question 1 of 3", "Pregunta 1 de 3", "Frage 1 von 3", "第1問（全3問）"),
    ("How many stories tall is the Flatiron Building?", "¿Cuántas plantas tiene el Flatiron Building?", "Wie viele Stockwerke hat das Flatiron Building?", "フラットアイアン・ビルは何階建て？"),
    ("Try it. Three questions.", "Pruébalo. Tres preguntas.", "Probier's aus. Drei Fragen.", "3問だけ、挑戦してみよう。"),
    ("Next", "Siguiente", "Weiter", "次へ"),
    ("QUIZ RESULT", "RESULTADO", "QUIZ-ERGEBNIS", "クイズ結果"),
    ("EXPERT", "EXPERTO", "EXPERTE", "エキスパート"),
    ("@New York quiz asking how many stories tall the Flatiron Building is, with an Answer via voice button",
     "Quiz de Nueva York que pregunta cuántas plantas tiene el Flatiron Building, con un botón para responder por voz",
     "New-York-Quiz mit der Frage, wie viele Stockwerke das Flatiron Building hat, und einer Taste für die Antwort per Sprache",
     "フラットアイアン・ビルの階数を尋ねるニューヨークのクイズと、音声で答えるボタン"),

    # ----- Trips -----
    ("Plan · Trips", "Planifica · Viajes", "Planen · Reisen", "計画 · 旅行"),
    ("Plan the trip, ", "Planifica el viaje, ", "Plane die Reise, ", "旅の計画を、"),
    ("day by day.", "día a día.", "Tag für Tag.", "1日ずつ。"),
    ("Build a trip over several days with landmarks and your own saved places, then fly through it on the 3D map before you leave.",
     "Crea un viaje de varios días con monumentos y tus propios lugares guardados, y sobrevuélalo en el mapa 3D antes de salir.",
     "Stell eine mehrtägige Reise aus Sehenswürdigkeiten und eigenen gespeicherten Orten zusammen und fliege sie vor der Abreise auf der 3D-Karte ab.",
     "名建築や保存した場所で数日間の旅程を作り、出発前に3Dマップで旅をたどれます。"),
    ("Reorder stops, see walking times and optimize the route in one tap",
     "Reordena paradas, consulta los tiempos a pie y optimiza la ruta con un toque",
     "Stopps umsortieren, Gehzeiten sehen und die Route mit einem Tipp optimieren",
     "立ち寄り先を並べ替え、徒歩時間を確認し、ワンタップでルートを最適化"),
    ("Add any restaurant, shop or venue from Apple Maps",
     "Añade cualquier restaurante, tienda o local de Apple Maps",
     "Jedes Restaurant, jeden Laden oder Veranstaltungsort aus Apple Karten hinzufügen",
     "Appleマップのレストラン、ショップ、会場を追加"),
    ("Find hotels for each night with a hotel search for your dates",
     "Encuentra hotel para cada noche con una búsqueda para tus fechas",
     "Hotels für jede Nacht finden, mit einer Hotelsuche für deine Reisedaten",
     "日程に合わせたホテル検索で、毎晩の宿を見つける"),
    ("Trips sync with iCloud between iPhone, iPad and Mac",
     "Los viajes se sincronizan con iCloud entre iPhone, iPad y Mac",
     "Reisen werden per iCloud zwischen iPhone, iPad und Mac synchronisiert",
     "旅程はiCloudでiPhone・iPad・Macに同期"),
    ("@NYC Long Weekend trip with a route map, three days, a Tour This Trip in 3D button and stops at the Flatiron and Empire State buildings",
     "Viaje «NYC Long Weekend» con mapa de la ruta, tres días, un botón para recorrer el viaje en 3D y paradas en el Flatiron y el Empire State Building",
     "Reise „NYC Long Weekend“ mit Routenkarte, drei Tagen, einer Taste für die 3D-Tour und Stopps am Flatiron und Empire State Building",
     "ルートマップ、3日間の日程、3Dで旅程をたどるボタン、フラットアイアンとエンパイア・ステート・ビルへの立ち寄りがある「NYC Long Weekend」の旅程"),
    ("LONG WEEKEND", "ESCAPADA", "KURZTRIP", "週末旅行"),
    ("3 DAYS", "3 DÍAS", "3 TAGE", "3日間"),

    # ----- Once you land -----
    ("Every city page", "En cada ciudad", "Auf jeder Stadtseite", "各都市のページで"),
    ("Everything you need ", "Todo lo que necesitas ", "Alles, was du brauchst, sobald du ", "着いたらすぐに、"),
    ("once you land.", "al aterrizar.", "landest.", "必要なものがすべて。"),
    ("Each city page answers \"what now?\", so you don't need five other apps.",
     "Cada ciudad responde al «¿y ahora qué?», así que no necesitas otras cinco apps.",
     "Jede Stadtseite beantwortet „Und jetzt?“, damit du keine fünf anderen Apps brauchst.",
     "各都市のページが「次はどうする？」に答えるので、ほかのアプリを5つも使う必要はありません。"),
    ("Hotels", "Hoteles", "Hotels", "ホテル"),
    ("Hotels near each landmark, with street photos, and a hotel search for your trip dates.",
     "Hoteles cerca de cada monumento, con fotos de la calle, y una búsqueda de hoteles para las fechas de tu viaje.",
     "Hotels in der Nähe jeder Sehenswürdigkeit, mit Straßenfotos, und eine Hotelsuche für deine Reisedaten.",
     "各名建築の近くのホテルをストリートの写真付きで表示。旅行の日程でホテル検索も。"),
    ("Places to eat", "Dónde comer", "Essen gehen", "食事"),
    ("Restaurants near each landmark with walking times, food tours, and coffee on the map.",
     "Restaurantes cerca de cada monumento con tiempos a pie, tours gastronómicos y cafés en el mapa.",
     "Restaurants in der Nähe jeder Sehenswürdigkeit mit Gehzeiten, Food-Touren und Cafés auf der Karte.",
     "各名建築の近くのレストランを徒歩時間付きで。フードツアーや地図上のカフェも。"),
    ("Events", "Eventos", "Events", "イベント"),
    ("Concerts, shows and games up to six months ahead, plus library and museum calendars in some cities.",
     "Conciertos, espectáculos y partidos hasta seis meses por delante, y en algunas ciudades, la agenda de bibliotecas y museos.",
     "Konzerte, Shows und Spiele bis zu sechs Monate im Voraus, in manchen Städten auch die Kalender von Bibliotheken und Museen.",
     "6か月先までのコンサート、公演、試合。一部の都市では図書館や美術館のイベントも。"),
    ("Weather", "El tiempo", "Wetter", "天気"),
    ("The forecast for the city you're exploring.", "La previsión de la ciudad que estás explorando.", "Die Vorhersage für die Stadt, die du erkundest.", "探索中の都市の天気予報。"),
    ("Currency", "Moneda", "Währung", "通貨"),
    ("A quick converter for the local currency.", "Un conversor rápido para la moneda local.", "Ein schneller Umrechner für die Landeswährung.", "現地通貨のかんたん換算。"),
    ("Airport", "Aeropuerto", "Flughafen", "空港"),
    ("The main airport, its code, and what makes it worth a look.", "El aeropuerto principal, su código y lo que lo hace especial.", "Der wichtigste Flughafen, sein Code und was ihn sehenswert macht.", "主要空港とそのコード、見どころ。"),
    ("Say hello", "Saluda", "Sag Hallo", "あいさつ"),
    ("How to greet people in the local language.", "Cómo saludar en el idioma local.", "So begrüßt du Menschen in der Landessprache.", "現地の言葉でのあいさつの仕方。"),
    ("Want to Visit", "Quiero visitar", "Wunschziele", "行きたい場所"),
    ("Heart any landmark or Apple Maps place to save it for later.", "Marca con un corazón cualquier monumento o lugar de Apple Maps para guardarlo.", "Markiere jede Sehenswürdigkeit oder jeden Ort aus Apple Karten mit einem Herz, um ihn zu merken.", "名建築やAppleマップの場所をハートで保存。"),

    # ----- Campuses -----
    ("@Conferences covered", "Conferencias incluidas", "Enthaltene Conferences", "収録カンファレンス"),
    ("+ around the world", "+ todo el mundo", "+ weltweit", "+ 世界各地"),
    ("@My College List with five saved schools and a Plan a College Road Trip button",
     "Mi lista de universidades con cinco centros guardados y un botón Planificar un viaje por universidades",
     "Meine College-Liste mit fünf gespeicherten Unis und einer Taste College-Roadtrip planen",
     "5校を保存したマイ大学リストと「大学めぐりの旅を計画」ボタン"),
    ("My College List", "Mi lista de universidades", "Meine College-Liste", "マイ大学リスト"),
    ("Save the schools you're considering.", "Guarda las universidades que te interesan.", "Speichere die Unis, die für dich infrage kommen.", "気になる大学を保存。"),
    ("@College Road Trip listing five schools in a short driving order",
     "Viaje por universidades con cinco centros en un orden de conducción corto",
     "College-Roadtrip mit fünf Unis in einer kurzen Fahrreihenfolge",
     "5校を短い移動順に並べた大学めぐりの旅"),
    ("College Road Trip", "Viaje por universidades", "College-Roadtrip", "大学めぐりの旅"),
    ("A day at each school, in a short driving order.", "Un día en cada universidad, en el orden de ruta más corto.", "Ein Tag pro Uni, in einer kurzen Fahrreihenfolge.", "1校につき1日、移動の少ない順に。"),
    ("@Campus traditions checklist for Michigan State with two traditions checked off",
     "Lista de tradiciones del campus de Michigan State con dos tradiciones marcadas",
     "Checkliste der Campus-Traditionen von Michigan State mit zwei abgehakten Traditionen",
     "2つのチェックが入ったミシガン州立大学のキャンパス伝統チェックリスト"),
    ("250+ traditions", "Más de 250 tradiciones", "250+ Traditionen", "250以上の伝統"),
    ("Rub the lucky statue, ring the bell, check it off.", "Frota la estatua de la suerte, toca la campana y márcalo.", "Die Glücksstatue reiben, die Glocke läuten, abhaken.", "幸運の像をなでて、鐘を鳴らして、チェック。"),

    ("For college visits · New in 2.7",
     "Para visitar universidades · Novedad en la 2.7",
     "Für Hochschulbesuche · Neu in 2.7",
     "大学見学に · 2.7の新機能"),
    ("Read each school's history, see upcoming home games, and browse campus events",
     "Lee la historia de cada universidad, consulta los próximos partidos en casa y explora los eventos del campus",
     "Lies die Geschichte jeder Hochschule, sieh dir kommende Heimspiele an und stöbere in Campus-Veranstaltungen",
     "各大学の歴史を読み、ホームゲームの予定を確認し、キャンパスのイベントをチェック"),
    ("Planning college visits? ", "¿Planeando visitas a universidades? ", "College-Besuche geplant? ", "大学見学の計画なら、"),
    ("Let Stamped! map it.", "Stamped! traza la ruta.", "Stamped! plant die Route.", "Stamped!におまかせ。"),
    ("Save the schools your family is looking at, and Stamped! lines them up into a road trip: one campus a day, in a short driving order. Every Big Ten, SEC, ACC and Big 12 school, the Ivy League, and great campuses from Oxford to Melbourne.",
     "Guarda las universidades que te interesan y Stamped! las ordena en un viaje por carretera: un campus al día, en el orden de ruta más corto. Todas las universidades del Big Ten, la SEC, la ACC y el Big 12, la Ivy League y grandes campus de Oxford a Melbourne.",
     "Speichere die Unis, die infrage kommen, und Stamped! macht daraus einen Roadtrip: ein Campus pro Tag, in kurzer Fahrreihenfolge. Jede Uni aus Big Ten, SEC, ACC und Big 12, die Ivy League und großartige Campusse von Oxford bis Melbourne.",
     "検討中の大学を保存すれば、Stamped!が1日1校、移動の少ない順にロードトリップを組み立てます。Big Ten、SEC、ACC、Big 12の全校、アイビーリーグ、オックスフォードからメルボルンまでの名門キャンパスに対応。"),
    ("Tour each campus in 3D before you drive there", "Recorre cada campus en 3D antes de ir en coche", "Jeden Campus in 3D erkunden, bevor du hinfährst", "車で行く前に、各キャンパスを3Dで下見"),
    ("See the landmark buildings and the stories behind them", "Descubre sus edificios emblemáticos y su historia", "Die bekanntesten Gebäude und ihre Geschichte kennenlernen", "象徴的な建物とその物語を知る"),
    ("Check off the traditions students actually do, like rubbing the lucky statue", "Marca las tradiciones que de verdad hacen los estudiantes, como frotar la estatua de la suerte", "Traditionen abhaken, die Studierende wirklich pflegen, etwa die Glücksstatue reiben", "幸運の像をなでるなど、学生が実際にしている伝統をチェック"),
    ("Free on iPhone, iPad and Mac, with trips synced over iCloud", "Gratis para iPhone, iPad y Mac, con los viajes sincronizados por iCloud", "Kostenlos für iPhone, iPad und Mac, Reisen per iCloud synchronisiert", "iPhone・iPad・Macで無料。旅程はiCloudで同期"),

    # ----- Collect -----
    ("Collect · Your passport", "Colecciona · Tu pasaporte", "Sammeln · Dein Reisepass", "集める · あなたのパスポート"),
    ("Collect them ", "Colecciónalos ", "Sammle sie ", "ぜんぶ"),
    ("all.", "todos.", "alle.", "集めよう。"),
    ("Earn a stamp for every landmark you visit and watch your passport fill in, city by city and country by country. Master a city when you've stamped every landmark in it.",
     "Consigue un sello por cada monumento que visites y mira cómo se llena tu pasaporte, ciudad a ciudad y país a país. Domina una ciudad cuando hayas sellado todos sus monumentos.",
     "Sammle einen Stempel für jede besuchte Sehenswürdigkeit und sieh zu, wie sich dein Reisepass füllt, Stadt für Stadt und Land für Land. Du meisterst eine Stadt, wenn du alle ihre Sehenswürdigkeiten gestempelt hast.",
     "訪れた名建築ごとにスタンプを獲得し、都市ごと、国ごとにパスポートが埋まっていく。すべての名建築にスタンプを押せば、その都市を制覇。"),
    ("Achievements for first stamps, night owls, weekend wanderers and more",
     "Logros por primeros sellos, noctámbulos, viajeros de fin de semana y más",
     "Erfolge für erste Stempel, Nachteulen, Wochenend-Entdecker und mehr",
     "はじめてのスタンプ、夜ふかし派、週末の散策家などの実績"),
    ("A world map of everywhere you've been", "Un mapa del mundo con todos los lugares donde has estado", "Eine Weltkarte mit allen Orten, an denen du warst", "訪れたすべての場所を示す世界地図"),
    ("Campus stamps in school colors", "Sellos de campus con los colores de cada universidad", "Campus-Stempel in den Farben der Uni", "スクールカラーのキャンパススタンプ"),
    ("Share your passport, and see it on your Home Screen with the widget",
     "Comparte tu pasaporte y míralo en la pantalla de inicio con el widget",
     "Teile deinen Reisepass und sieh ihn per Widget auf dem Home-Bildschirm",
     "パスポートを共有したり、ウィジェットでホーム画面に表示したり"),
    ("@Achievements screen with First Stamp, On The Move, Passport Regular and Century Club unlocked",
     "Pantalla de logros con varios logros desbloqueados, entre ellos Primer sello y Club de los cien",
     "Erfolge-Bildschirm mit mehreren freigeschalteten Erfolgen, darunter Erster Stempel und Hunderter-Club",
     "「はじめてのスタンプ」「センチュリークラブ」などの実績が解除された実績画面"),
    ("ACHIEVEMENT", "LOGRO", "ERFOLG", "実績"),
    ("CITY MASTERED", "CIUDAD DOMINADA", "STADT GEMEISTERT", "都市制覇"),
    ("★ GOLD ★", "★ ORO ★", "★ GOLD ★", "★ ゴールド ★"),

    # ----- Little things -----
    ("And the little things.", "Y los pequeños detalles.", "Und die kleinen Dinge.", "細かなところまで。"),
    ("iCloud sync", "Sincronización con iCloud", "iCloud-Sync", "iCloud同期"),
    ("Stamps, trips and lists follow you between devices.", "Sellos, viajes y listas te acompañan en todos tus dispositivos.", "Stempel, Reisen und Listen sind auf all deinen Geräten dabei.", "スタンプ、旅程、リストがデバイス間で同期。"),
    ("9 languages", "9 idiomas", "9 Sprachen", "9言語"),
    ("English, German, Spanish, French, Italian, Japanese, Korean, Portuguese and Chinese.",
     "Inglés, alemán, español, francés, italiano, japonés, coreano, portugués y chino.",
     "Englisch, Deutsch, Spanisch, Französisch, Italienisch, Japanisch, Koreanisch, Portugiesisch und Chinesisch.",
     "英語、ドイツ語、スペイン語、フランス語、イタリア語、日本語、韓国語、ポルトガル語、中国語。"),
    ("Made for everyone", "Para todo el mundo", "Für alle gemacht", "だれでも使いやすく"),
    ("VoiceOver, Dynamic Type and Reduce Motion, plus high contrast and a dark mode.",
     "VoiceOver, texto dinámico y reducir movimiento, además de alto contraste y modo oscuro.",
     "VoiceOver, dynamische Schrift und „Bewegung reduzieren“, dazu hoher Kontrast und ein Dunkelmodus.",
     "VoiceOver、Dynamic Type、視差効果を減らす設定に加え、高コントラストとダークモードにも対応。"),

    # ----- Closing call to action -----
    ("BON VOYAGE", "BUEN VIAJE", "GUTE REISE", "よい旅を"),
    ("DEPART", "SALIDA", "ABFLUG", "出発"),
    ("WELCOME", "BIENVENIDO", "WILLKOMMEN", "ようこそ"),
    ("ARRIVE", "LLEGADA", "ANKUNFT", "到着"),
    ("Your passport is waiting.", "Tu pasaporte te espera.", "Dein Reisepass wartet.", "パスポートが待っています。"),
    ("2,400+ landmarks. One stamp each. Free on iPhone, iPad, Mac and Apple Vision Pro.",
     "Más de 2.400 monumentos. Un sello en cada uno. Gratis para iPhone, iPad, Mac y Apple Vision Pro.",
     "2.400+ Sehenswürdigkeiten. Ein Stempel für jede. Kostenlos für iPhone, iPad, Mac und Apple Vision Pro.",
     "2,400以上の名建築。それぞれにスタンプ。iPhone・iPad・Mac・Apple Vision Proで無料。"),

    # ----- Landmark photos and guided tours -----
    ("Inside the app · 2,400+ landmarks",
     "Dentro de la app · Más de 2.400 monumentos",
     "In der App · 2.400+ Sehenswürdigkeiten",
     "アプリの中 · 2,400以上の名建築"),
    ('A few of the places ', 'Algunos de los lugares ', 'Ein paar der Orte, ', 'あなたを待つ'),
    ('waiting for you.', 'que te esperan.', 'die auf dich warten.', '名建築の一部。'),
    ('Each one opens its city guide, with the architect, the year it was built and the story behind it.', 'Cada uno abre su guía de la ciudad (en inglés), con el arquitecto, el año de construcción y su historia.', 'Jeder öffnet den Stadtführer (auf Englisch) mit Architekt, Baujahr und der Geschichte dahinter.', 'タップすると都市ガイド（英語）が開き、建築家、建築年、建物の物語を読めます。'),
    ('@Landmarks in Stamped!', 'Monumentos en Stamped!', 'Sehenswürdigkeiten in Stamped!', 'Stamped!の名建築'),
    ('Photo: ', 'Foto: ', 'Foto: ', '写真: '),
    ('Guided tour · Recorded in the app', 'Visita guiada · Grabada en la app', 'Geführte Tour · In der App aufgenommen', 'ガイドツアー · アプリで収録'),
    ('Press play and ', 'Dale al play y ', 'Play drücken und ', '再生を押せば、'),
    ('let it fly.', 'a volar.', 'abheben.', '空の旅へ。'),
    ('The guided tour flies from landmark to landmark on its own, with a card and a Look Around preview at every stop.', 'La visita guiada vuela sola de monumento en monumento, con una tarjeta y una vista previa de Mirar alrededor en cada parada.', 'Die geführte Tour fliegt von selbst von Sehenswürdigkeit zu Sehenswürdigkeit, mit Infokarte und Umsehen-Vorschau an jedem Stopp.', 'ガイドツアーは名建築から名建築へ自動で飛び、各スポットでカードとLook Aroundのプレビューを表示します。'),
    ('@Guided tour of Paris in the Stamped! app: the camera flies over 3D Paris from the Palais Garnier to the Louvre, Sainte-Chapelle, the Centre Pompidou, the Panthéon and the Eiffel Tower', 'Visita guiada de París en la app Stamped!: la cámara sobrevuela París en 3D desde el Palais Garnier hasta el Louvre, la Sainte-Chapelle, el Centro Pompidou, el Panteón y la Torre Eiffel', 'Geführte Tour durch Paris in der Stamped!-App: Die Kamera fliegt über das 3D-Paris vom Palais Garnier zum Louvre, zur Sainte-Chapelle, zum Centre Pompidou, zum Panthéon und zum Eiffelturm', 'Stamped!アプリでのパリのガイドツアー：3Dのパリをガルニエ宮からルーヴル美術館、サント・シャペル、ポンピドゥー・センター、パンテオン、エッフェル塔へと飛ぶ様子'),
    ('@Guided tour of Chicago in the Stamped! app: the camera flies over 3D downtown Chicago past the Carbide and Carbon Building, the Wrigley Building, Tribune Tower and the St. Regis', 'Visita guiada de Chicago en la app Stamped!: la cámara sobrevuela el centro de Chicago en 3D junto al Carbide and Carbon Building, el Wrigley Building, la Tribune Tower y el St. Regis', 'Geführte Tour durch Chicago in der Stamped!-App: Die Kamera fliegt über das 3D-Zentrum von Chicago vorbei am Carbide and Carbon Building, Wrigley Building, Tribune Tower und St. Regis', 'Stamped!アプリでのシカゴのガイドツアー：3Dのシカゴ中心部をカーバイド・アンド・カーボン・ビル、リグレー・ビル、トリビューン・タワー、セント・レジスへと飛ぶ様子'),
    ('Palais Garnier to the Eiffel Tower', 'Del Palais Garnier a la Torre Eiffel', 'Vom Palais Garnier zum Eiffelturm', 'ガルニエ宮からエッフェル塔へ'),
    ('Michigan Avenue to the St. Regis', 'De Michigan Avenue al St. Regis', 'Von der Michigan Avenue zum St. Regis', 'ミシガン・アベニューからセント・レジスへ'),
    ('Eiffel Tower', 'Torre Eiffel', 'Eiffelturm', 'エッフェル塔'),
    ('@Eiffel Tower', 'Torre Eiffel', 'Eiffelturm', 'エッフェル塔'),
    ('The Colosseum', 'El Coliseo', 'Kolosseum', 'コロッセオ'),
    ('@The Colosseum', 'El Coliseo', 'Kolosseum', 'コロッセオ'),
    ('Sagrada Família', 'Sagrada Família', 'Sagrada Família', 'サグラダ・ファミリア'),
    ('@Sagrada Família', 'Sagrada Família', 'Sagrada Família', 'サグラダ・ファミリア'),
    ('Sydney Opera House', 'Ópera de Sídney', 'Sydney Opera House', 'シドニー・オペラハウス'),
    ('@Sydney Opera House', 'Ópera de Sídney', 'Sydney Opera House', 'シドニー・オペラハウス'),
    ('Christ the Redeemer', 'Cristo Redentor', 'Cristo Redentor', 'コルコバードのキリスト像'),
    ('@Christ the Redeemer', 'Cristo Redentor', 'Cristo Redentor', 'コルコバードのキリスト像'),
    ('Empire State Building', 'Empire State Building', 'Empire State Building', 'エンパイア・ステート・ビル'),
    ('@Empire State Building', 'Empire State Building', 'Empire State Building', 'エンパイア・ステート・ビル'),
    ('Kinkaku-ji', 'Kinkaku-ji', 'Kinkaku-ji', '金閣寺'),
    ('@Kinkaku-ji', 'Kinkaku-ji', 'Kinkaku-ji', '金閣寺'),
    ('Hagia Sophia', 'Santa Sofía', 'Hagia Sophia', 'アヤソフィア'),
    ('@Hagia Sophia', 'Santa Sofía', 'Hagia Sophia', 'アヤソフィア'),
    ('Petronas Towers', 'Torres Petronas', 'Petronas Towers', 'ペトロナスツインタワー'),
    ('@Petronas Towers', 'Torres Petronas', 'Petronas Towers', 'ペトロナスツインタワー'),
    ('Fallingwater', 'Casa de la Cascada', 'Fallingwater', '落水荘'),
    ('@Fallingwater', 'Casa de la Cascada', 'Fallingwater', '落水荘'),
    ('Hallgrímskirkja', 'Hallgrímskirkja', 'Hallgrímskirkja', 'ハットルグリムス教会'),
    ('@Hallgrímskirkja', 'Hallgrímskirkja', 'Hallgrímskirkja', 'ハットルグリムス教会'),
    ('@Great Pyramid of Giza', 'Gran Pirámide de Guiza', 'Cheops-Pyramide von Gizeh', 'ギザの大ピラミッド'),
    ('Paris', 'París', 'Paris', 'パリ'),
    ('Rome', 'Roma', 'Rom', 'ローマ'),
    ('Barcelona', 'Barcelona', 'Barcelona', 'バルセロナ'),
    ('Cairo', 'El Cairo', 'Kairo', 'カイロ'),
    ('Sydney', 'Sídney', 'Sydney', 'シドニー'),
    ('Rio de Janeiro', 'Río de Janeiro', 'Rio de Janeiro', 'リオデジャネイロ'),
    ('New York', 'Nueva York', 'New York', 'ニューヨーク'),
    ('Kyoto', 'Kioto', 'Kyoto', '京都'),
    ('Istanbul', 'Estambul', 'Istanbul', 'イスタンブール'),
    ('Kuala Lumpur', 'Kuala Lumpur', 'Kuala Lumpur', 'クアラルンプール'),
    ('Pittsburgh', 'Pittsburgh', 'Pittsburgh', 'ピッツバーグ'),
    ('Reykjavik', 'Reikiavik', 'Reykjavík', 'レイキャビク'),
    ('Chicago', 'Chicago', 'Chicago', 'シカゴ'),
    ('Tokyo', 'Tokio', 'Tokio', '東京'),

    # "Try it" section (live Apple Maps demo) and the text stamped-try.js shows from try-strings
    ("Try it · Live Apple Maps", "Pruébalo · Apple Maps en vivo", "Ausprobieren · Live in Apple Karten", "試してみよう · 本物のAppleマップ"),
    ("!>Tap a landmark. <", ">Toca un monumento. <", ">Tippe auf ein Wahrzeichen. <", ">名建築をタップして、<"),
    ("Stamp it.", "Séllalo.", "Stempel drauf.", "スタンプを押そう。"),
    ("Stamp it", "Sellar", "Stempeln", "スタンプを押す"),
    ("Open in Apple Maps", "Abrir en Apple Maps", "In Apple Karten öffnen", "Appleマップで開く"),
    ("@Choose a city", "Elige una ciudad", "Stadt wählen", "都市を選ぶ"),
    ("@Map of the landmarks in the chosen city", "Mapa de los monumentos de la ciudad elegida",
     "Karte der Sehenswürdigkeiten in der gewählten Stadt", "選んだ都市の名建築の地図"),
    ('!"stamp": "Stamp it"', '"stamp": "Sellar"', '"stamp": "Stempeln"', '"stamp": "スタンプを押す"'),
    ('!"stamped": "Stamped ✓"', '"stamped": "Sellado ✓"', '"stamped": "Gestempelt ✓"', '"stamped": "スタンプ済み ✓"'),
    ('!"loading": "Loading Look Around…"', '"loading": "Cargando Look Around…"',
     '"loading": "Look Around wird geladen…"', '"loading": "Look Aroundを読み込み中…"'),
    ('!"hint": "Tap the preview to walk around in Look Around."',
     '"hint": "Toca la vista previa para recorrer la calle en Look Around."',
     '"hint": "Tippe auf die Vorschau, um dich in Look Around umzusehen."',
     '"hint": "プレビューをタップしてLook Aroundで見回そう。"'),
    ('!"noImagery": "Apple doesn\'t have street-level imagery here yet."',
     '"noImagery": "Apple aún no tiene imágenes a pie de calle aquí."',
     '"noImagery": "Apple hat hier noch keine Bilder auf Straßenebene."',
     '"noImagery": "ここにはまだAppleのストリートレベルの画像がありません。"'),
    ('!"progress": "{n} of {total} stamped in {city}"', '"progress": "{n} de {total} sellados en {city}"',
     '"progress": "{n} von {total} in {city} gestempelt"', '"progress": "{city}で{n}/{total}件スタンプ済み"'),
    ('!"guide": "{city} guide"', '"guide": "Guía de {city}"', '"guide": "{city}-Guide"', '"guide": "{city}ガイド"'),
    # City names in the demo's data (try-data), used in the progress line and guide link
    ('!"code": "NYC", "name": "New York"', '"code": "NYC", "name": "Nueva York"', '"code": "NYC", "name": "New York"', '"code": "NYC", "name": "ニューヨーク"'),
    ('!"code": "PARIS", "name": "Paris"', '"code": "PARIS", "name": "París"', '"code": "PARIS", "name": "Paris"', '"code": "PARIS", "name": "パリ"'),
    ('!"code": "LONDON", "name": "London"', '"code": "LONDON", "name": "Londres"', '"code": "LONDON", "name": "London"', '"code": "LONDON", "name": "ロンドン"'),
    ('!"code": "ROME", "name": "Rome"', '"code": "ROME", "name": "Roma"', '"code": "ROME", "name": "Rom"', '"code": "ROME", "name": "ローマ"'),
    ('!"code": "TOKYO", "name": "Tokyo"', '"code": "TOKYO", "name": "Tokio"', '"code": "TOKYO", "name": "Tokio"', '"code": "TOKYO", "name": "東京"'),
    ('!"code": "CHICAGO", "name": "Chicago"', '"code": "CHICAGO", "name": "Chicago"', '"code": "CHICAGO", "name": "Chicago"', '"code": "CHICAGO", "name": "シカゴ"'),

    ("London", "Londres", "London", "ロンドン"),
    ("@Guided tour of London in the Stamped! app: the camera flies over 3D London from Tate Modern to St Paul's Cathedral, the Barbican, the Gherkin and the Lloyd's Building",
     "Visita guiada de Londres en la app Stamped!: la cámara sobrevuela Londres en 3D desde la Tate Modern hasta la catedral de San Pablo, el Barbican, el Gherkin y el edificio Lloyd's",
     "Geführte Tour durch London in der Stamped!-App: Die Kamera fliegt über das 3D-London von der Tate Modern zur St Paul's Cathedral, zum Barbican, zur Gherkin und zum Lloyd's Building",
     "Stamped!アプリでのロンドンのガイドツアー：3Dのロンドンをテート・モダンからセント・ポール大聖堂、バービカン、ガーキン、ロイズ・ビルへと飛ぶ様子"),
    ("Tate Modern to the Lloyd's Building", "De la Tate Modern al edificio Lloyd's", "Von der Tate Modern zum Lloyd's Building", "テート・モダンからロイズ・ビルへ"),
    ("@Guided tour of Rome in the Stamped! app: the camera flies over 3D Rome from the Pantheon to Palazzo Doria Pamphilj, the Altare della Patria and San Carlo alle Quattro Fontane",
     "Visita guiada de Roma en la app Stamped!: la cámara sobrevuela Roma en 3D desde el Panteón hasta el Palazzo Doria Pamphilj, el Altare della Patria y San Carlo alle Quattro Fontane",
     "Geführte Tour durch Rom in der Stamped!-App: Die Kamera fliegt über das 3D-Rom vom Pantheon zum Palazzo Doria Pamphilj, zum Altare della Patria und nach San Carlo alle Quattro Fontane",
     "Stamped!アプリでのローマのガイドツアー：3Dのローマをパンテオンからドーリア・パンフィーリ宮殿、ヴィットーリオ・エマヌエーレ2世記念堂、サン・カルロ・アッレ・クアットロ・フォンターネ聖堂へと飛ぶ様子"),
    ("The Pantheon to the Altare della Patria", "Del Panteón al Altare della Patria", "Vom Pantheon zum Altare della Patria", "パンテオンからヴィットーリオ・エマヌエーレ2世記念堂へ"),

    # ----- Footer -----
    ("@App links", "Enlaces de la app", "App-Links", "アプリのリンク"),
    ("Support", "Soporte", "Support", "サポート"),
    ("Privacy", "Privacidad", "Datenschutz", "プライバシー"),
    ("City guides", "Guías de ciudades", "Stadtführer", "都市ガイド"),
    ("How it was built", "Cómo se hizo", "So wurde es gebaut", "開発の舞台裏"),
    ("@Languages", "Idiomas", "Sprachen", "言語"),
    ("Stamped! is not affiliated with or endorsed by any university. School names and colors are used only to identify them.",
     "Stamped! no está afiliado ni respaldado por ninguna universidad. Los nombres y colores de las universidades se usan solo para identificarlas.",
     "Stamped! ist mit keiner Universität verbunden und wird von keiner unterstützt. Namen und Farben der Unis dienen nur der Identifikation.",
     "Stamped!はいかなる大学とも提携しておらず、承認も受けていません。大学名とスクールカラーは識別のためにのみ使用しています。"),
    ("Apple, the Apple logo, iPhone, iPad, Mac and Apple Vision Pro are trademarks of Apple Inc. App Store and Mac App Store are service marks of Apple Inc.",
     "Apple, el logotipo de Apple, iPhone, iPad, Mac y Apple Vision Pro son marcas comerciales de Apple Inc. App Store y Mac App Store son marcas de servicio de Apple Inc.",
     "Apple, das Apple Logo, iPhone, iPad, Mac und Apple Vision Pro sind Marken der Apple Inc. App Store und Mac App Store sind Dienstleistungsmarken der Apple Inc.",
     "Apple、Appleのロゴ、iPhone、iPad、Mac、Apple Vision Proは、Apple Inc.の商標です。App StoreおよびMac App Storeは、Apple Inc.のサービスマークです。"),

    # ----- Added with the Vision Pro, Mac and feature cards (2.10 refresh) -----
    ("@Stamped! A City Passport: passport stamps over a 3D city map",
     "Stamped! A City Passport: sellos de pasaporte sobre un mapa 3D de una ciudad",
     "Stamped! A City Passport: Reisepass-Stempel über einer 3D-Stadtkarte",
     "Stamped! A City Passport：3D都市マップに重なるパスポートスタンプ"),
    ("10 more cities, from Porto and Kraków to Hiroshima and Hanoi, arrive in the next update.",
     "10 ciudades más, de Oporto y Cracovia a Hiroshima y Hanói, llegan en la próxima actualización.",
     "10 weitere Städte, von Porto und Krakau bis Hiroshima und Hanoi, kommen mit dem nächsten Update.",
     "ポルト、クラクフから広島、ハノイまで、さらに10都市が次のアップデートで登場します。"),
    ("Save for Offline",
     "Guardar sin conexión",
     "Offline sichern",
     "オフライン保存"),
    ("Keep a city's photos and stories on your device for flights and trips abroad.",
     "Guarda las fotos y las historias de una ciudad en tu dispositivo para vuelos y viajes al extranjero.",
     "Speichere Fotos und Geschichten einer Stadt auf deinem Gerät, für Flüge und Reisen ins Ausland.",
     "都市の写真と物語を端末に保存。機内や海外旅行でも読めます。"),
    ("Listen",
     "Escuchar",
     "Anhören",
     "読み上げ"),
    ("Any landmark's story, read aloud while you stand in front of it.",
     "La historia de cualquier monumento, leída en voz alta mientras lo tienes delante.",
     "Die Geschichte jedes Bauwerks, vorgelesen, während du davor stehst.",
     "名建築の物語を、目の前に立ちながら音声で聞けます。"),
    ("Share a stamp",
     "Comparte un sello",
     "Stempel teilen",
     "スタンプを共有"),
    ("Send a city or campus stamp to friends as a picture card.",
     "Envía el sello de una ciudad o un campus a tus amigos como tarjeta con imagen.",
     "Schick Freunden den Stempel einer Stadt oder eines Campus als Bildkarte.",
     "都市やキャンパスのスタンプを画像カードにして友だちに送れます。"),
    ("Siri and Shortcuts",
     "Siri y Atajos",
     "Siri und Kurzbefehle",
     "Siriとショートカット"),
    ("Say \"Open Paris in Stamped!\" or add Stamped! to a shortcut.",
     "Di «Abre París en Stamped!» o añade Stamped! a un atajo.",
     "Sag „Öffne Paris in Stamped!“ oder füge Stamped! einem Kurzbefehl hinzu.",
     "「Stamped!でパリを開いて」と話しかけたり、ショートカットに追加したりできます。"),
    ("Tours and tickets",
     "Visitas y entradas",
     "Touren und Tickets",
     "ツアーとチケット"),
    ("Find tours and tickets for any city landmark with GetYourGuide.",
     "Encuentra visitas y entradas para cualquier monumento con GetYourGuide.",
     "Finde Touren und Tickets für jedes Bauwerk in der Stadt mit GetYourGuide.",
     "GetYourGuideで、都市の名建築のツアーやチケットを探せます。"),
    ("Historic photos",
     "Fotos históricas",
     "Historische Fotos",
     "歴史的な写真"),
    ("Old photos and drawings of US landmarks from the Library of Congress.",
     "Fotos y planos antiguos de monumentos de EE. UU. de la Biblioteca del Congreso.",
     "Alte Fotos und Zeichnungen von US-Bauwerken aus der Library of Congress.",
     "米国議会図書館所蔵の、アメリカの名建築の古い写真や図面。"),
    ("Apple Vision Pro · Spatial",
     "Apple Vision Pro · Espacial",
     "Apple Vision Pro · Räumlich",
     "Apple Vision Pro · 空間"),
    ("Stand inside ",
     "Entra en ",
     "Steh mitten ",
     "名建築の"),
    ("the landmark.",
     "el monumento.",
     "im Bauwerk.",
     "中に立とう。"),
    ("On Apple Vision Pro, every city floats in your room on a photoreal 3D map, and the stamps you collect on iPhone come with you.",
     "En Apple Vision Pro, cada ciudad flota en tu habitación sobre un mapa 3D fotorrealista, y los sellos que consigues en el iPhone te acompañan.",
     "Auf der Apple Vision Pro schwebt jede Stadt als fotorealistische 3D-Karte in deinem Raum, und deine Stempel vom iPhone sind dabei.",
     "Apple Vision Proでは、すべての都市がフォトリアルな3Dマップとして部屋に浮かび、iPhoneで集めたスタンプもそのまま使えます。"),
    ("A 3D globe of every city, with live pins for the places you've stamped",
     "Un globo 3D con todas las ciudades y marcadores en vivo de los lugares que has sellado",
     "Ein 3D-Globus mit allen Städten und Live-Nadeln für die Orte, die du gestempelt hast",
     "全都市を収めた3D地球儀。スタンプ済みの場所がピンでリアルタイムに表示"),
    ("360° panoramas: stand inside 26 landmarks",
     "Panorámicas de 360°: entra en 26 monumentos",
     "360°-Panoramen: Steh mitten in 26 Bauwerken",
     "360°パノラマ：26の名建築の中に立てます"),
    ("Play Tour: a narrated flight from landmark to landmark",
     "Play Tour: un vuelo narrado de monumento en monumento",
     "Play Tour: ein kommentierter Flug von Bauwerk zu Bauwerk",
     "Play Tour：ナレーション付きで名建築から名建築へ飛ぶツアー"),
    ("Detroit in full 3D, downloaded only when you want it",
     "Detroit en 3D completo, que se descarga solo cuando quieras",
     "Detroit komplett in 3D, nur geladen, wenn du es willst",
     "デトロイトをまるごと3Dで。必要なときだけダウンロード"),
    ("Explore Together with SharePlay, so friends on a FaceTime call fly through a city with you",
     "Explorar juntos con SharePlay, para que tus amigos en una llamada de FaceTime sobrevuelen una ciudad contigo",
     "Gemeinsam entdecken mit SharePlay, damit Freunde in einem FaceTime-Anruf mit dir durch eine Stadt fliegen",
     "SharePlayの「一緒に探索」。FaceTime中の友だちと一緒に街を飛び回れます"),
    ("@Download on the App Store for Apple Vision Pro",
     "Descargar en el App Store para Apple Vision Pro",
     "Im App Store für Apple Vision Pro laden",
     "Apple Vision Pro向けにApp Storeからダウンロード"),
    ("On Apple Vision Pro",
     "En Apple Vision Pro",
     "Auf der Apple Vision Pro",
     "Apple Vision Pro版"),
    ("@Stamped! on Apple Vision Pro: the Mumbai map window floating inside a 360° panorama of the Taj Mahal Palace Hotel's staircase",
     "Stamped! en Apple Vision Pro: la ventana del mapa de Bombay flotando dentro de una panorámica de 360° de la escalera del hotel Taj Mahal Palace",
     "Stamped! auf der Apple Vision Pro: Das Kartenfenster von Mumbai schwebt in einem 360°-Panorama der Treppe des Taj Mahal Palace Hotels",
     "Apple Vision ProのStamped!：タージ・マハル・パレス・ホテルの階段の360°パノラマの中に浮かぶムンバイの地図ウインドウ"),
    ("360° panoramas",
     "Panorámicas de 360°",
     "360°-Panoramen",
     "360°パノラマ"),
    ("Stand inside the landmark.",
     "Entra en el monumento.",
     "Steh mitten im Bauwerk.",
     "名建築の中に立とう。"),
    ("@A 3D globe with stamp pins floating in a living room in front of the Stamped! New York map",
     "Un globo 3D con marcadores de sellos flotando en un salón delante del mapa de Nueva York de Stamped!",
     "Ein 3D-Globus mit Stempel-Nadeln schwebt in einem Wohnzimmer vor der New-York-Karte von Stamped!",
     "Stamped!のニューヨークの地図の前、リビングに浮かぶスタンプのピン付き3D地球儀"),
    ("The globe",
     "El globo",
     "Der Globus",
     "地球儀"),
    ("Spin it, and a city turns toward you.",
     "Hazlo girar y una ciudad se vuelve hacia ti.",
     "Dreh ihn, und eine Stadt wendet sich dir zu.",
     "回すと、都市があなたの方を向きます。"),
    ("Mac · The big screen",
     "Mac · La pantalla grande",
     "Mac · Der große Bildschirm",
     "Mac · 大きな画面で"),
    ("Plan it all ",
     "Planifícalo todo ",
     "Plane alles ",
     "すべての計画を"),
    ("on your Mac.",
     "en tu Mac.",
     "auf dem Mac.",
     "Macで。"),
    ("The same passport on a bigger screen: your cities in the sidebar, the 3D map in the middle and the city page beside it. Plan on the Mac, then pick the trip up on your iPhone with iCloud.",
     "El mismo pasaporte en una pantalla más grande: tus ciudades en la barra lateral, el mapa 3D en el centro y la página de la ciudad al lado. Planifica en el Mac y retoma el viaje en tu iPhone con iCloud.",
     "Derselbe Reisepass auf einem größeren Bildschirm: deine Städte in der Seitenleiste, die 3D-Karte in der Mitte und die Stadtseite daneben. Plane auf dem Mac und mach auf dem iPhone mit iCloud weiter.",
     "同じパスポートを大きな画面で。サイドバーに都市、中央に3Dマップ、その横に都市のページ。Macで計画して、iCloudでiPhoneに引き継げます。"),
    ("World Map, My Journey, Achievements, My College List, trips and the quiz each open in their own window",
     "El mapa del mundo, Mi viaje, Logros, Mi lista de universidades, los viajes y el quiz se abren cada uno en su propia ventana",
     "Weltkarte, Meine Reise, Erfolge, Meine College-Liste, Reisen und das Quiz öffnen sich jeweils in einem eigenen Fenster",
     "世界地図、マイジャーニー、実績、マイ大学リスト、旅程、クイズをそれぞれ別のウインドウで開けます"),
    ("Drag landmarks into a trip, with hover effects and keyboard shortcuts",
     "Arrastra monumentos a un viaje, efectos al pasar el puntero y atajos de teclado",
     "Bauwerke in eine Reise ziehen, Hover-Effekte und Tastaturkurzbefehle",
     "名建築をドラッグして旅程に追加、ホバー効果、キーボードショートカット"),
    ("@Stamped! on a Mac: a sidebar of cities, a 3D map of Chicago with stamped landmarks, and the Chicago city page with 17 of 17 landmarks stamped",
     "Stamped! en un Mac: una barra lateral de ciudades, un mapa 3D de Chicago con monumentos sellados y la página de Chicago con 17 de 17 monumentos sellados",
     "Stamped! auf dem Mac: eine Seitenleiste mit Städten, eine 3D-Karte von Chicago mit gestempelten Bauwerken und die Chicago-Seite mit 17 von 17 gestempelten Bauwerken",
     "MacのStamped!：都市のサイドバー、スタンプ済みの名建築が並ぶシカゴの3Dマップ、17件中17件スタンプ済みのシカゴのページ"),
    # Hero shortcuts for the two main audiences
    ("Planning a city trip?", "¿Planeas un viaje a una ciudad?", "Städtereise geplant?", "都市旅行の計画中？"),
    ("Visiting colleges?", "¿Visitas universidades?", "College-Besuche geplant?", "大学見学に行く？"),
    # Header menu link, the Mac App Store badge file and both badges' alt text
    ("!Download_on_the_Mac_App_Store_Badge_US-UK_RGB_blk_092917.svg", "Download_on_the_Mac_App_Store_Badge_ES_RGB_blk_100217.svg", "Download_on_the_Mac_App_Store_Badge_DE_RGB_blk_092917.svg", "Download_on_the_Mac_App_Store_Badge_JP_RGB_blk_100317.svg"),
    ("Try it", "Pruébalo", "Ausprobieren", "試す"),
    ("@Download on the App Store", "Descargar en el App Store", "Laden im App Store", "App Storeからダウンロード"),
    ("@Download on the Mac App Store", "Descargar en el Mac App Store", "Laden im Mac App Store", "Mac App Storeからダウンロード"),
]

# Text the quiz and video script (assets/js/stamped-app.js) write at runtime
# (replaces the whole `window.stampedCopy = {...};` block)
COPY = {
    "es": """{
                pause: 'Pausar vídeo',
                play: 'Reproducir vídeo',
                question: 'Pregunta {n} de {total}',
                correct: '¡Correcto! ',
                wrong: 'Casi. ',
                next: 'Siguiente',
                seeStamp: 'Ver tu sello',
                done: 'Listo',
                perfect: '¡Puntuación perfecta!',
                yourScore: 'Has acertado {score} de {total}.',
                more: 'La app tiene 273 quizzes y 2.730 preguntas.',
                playAgain: 'Jugar otra vez',
                intro: 'Pruébalo. Tres preguntas.',
                ranks: ['TURISTA', 'VIAJERO', 'LOCAL', 'EXPERTO'],
                questions: [
                    { q: '¿Cuántas plantas tiene el Flatiron Building?', options: ['16', '22', '31'], answer: 1,
                      note: '22 plantas, terminado en 1902.' },
                    { q: '¿Quién diseñó la Casa de la Cascada (Fallingwater)?', options: ['Le Corbusier', 'Frank Lloyd Wright', 'Frank Gehry'], answer: 1,
                      note: 'Frank Lloyd Wright, sobre una cascada en Pensilvania.' },
                    { q: '¿Quién diseñó la Ópera de Sídney?', options: ['Zaha Hadid', 'Renzo Piano', 'Jørn Utzon'], answer: 2,
                      note: 'Jørn Utzon, arquitecto danés, ganó el concurso de diseño en 1957.' }
                ]
            }""",
    "de": """{
                pause: 'Video pausieren',
                play: 'Video abspielen',
                question: 'Frage {n} von {total}',
                correct: 'Richtig. ',
                wrong: 'Leider falsch. ',
                next: 'Weiter',
                seeStamp: 'Zu deinem Stempel',
                done: 'Fertig',
                perfect: 'Volle Punktzahl.',
                yourScore: 'Du hast {score} von {total} richtig.',
                more: 'Die App hat 273 Quizze mit 2.730 Fragen.',
                playAgain: 'Noch mal spielen',
                intro: "Probier's aus. Drei Fragen.",
                ranks: ['TOURIST', 'REISENDER', 'KENNER', 'EXPERTE'],
                questions: [
                    { q: 'Wie viele Stockwerke hat das Flatiron Building?', options: ['16', '22', '31'], answer: 1,
                      note: '22 Stockwerke, fertiggestellt 1902.' },
                    { q: 'Wer hat Fallingwater entworfen?', options: ['Le Corbusier', 'Frank Lloyd Wright', 'Frank Gehry'], answer: 1,
                      note: 'Frank Lloyd Wright, über einem Wasserfall in Pennsylvania.' },
                    { q: 'Wer hat das Sydney Opera House entworfen?', options: ['Zaha Hadid', 'Renzo Piano', 'Jørn Utzon'], answer: 2,
                      note: 'Jørn Utzon, ein dänischer Architekt, gewann 1957 den Wettbewerb.' }
                ]
            }""",
    "ja": """{
                pause: '動画を一時停止',
                play: '動画を再生',
                question: '第{n}問（全{total}問）',
                correct: '正解！',
                wrong: '残念。',
                next: '次へ',
                seeStamp: 'スタンプを見る',
                done: '結果',
                perfect: '満点です。',
                yourScore: '{total}問中{score}問正解。',
                more: 'アプリには273のクイズ、2,730問があります。',
                playAgain: 'もう一度',
                intro: '3問だけ、挑戦してみよう。',
                ranks: ['旅行者', 'トラベラー', '地元通', 'エキスパート'],
                questions: [
                    { q: 'フラットアイアン・ビルは何階建て？', options: ['16', '22', '31'], answer: 1,
                      note: '22階建てで、1902年に完成しました。' },
                    { q: '落水荘（フォーリングウォーター）を設計したのは？', options: ['ル・コルビュジエ', 'フランク・ロイド・ライト', 'フランク・ゲーリー'], answer: 1,
                      note: 'フランク・ロイド・ライト。ペンシルベニア州の滝の上に建っています。' },
                    { q: 'シドニー・オペラハウスを設計したのは？', options: ['ザハ・ハディド', 'レンゾ・ピアノ', 'ヨーン・ウツソン'], answer: 2,
                      note: 'デンマークの建築家ヨーン・ウツソン。1957年に設計競技で選ばれました。' }
                ]
            }""",
}


# ----- Sign-up pages Buttondown redirects to -----
# Every string on each page, in English. Each one is translated by T / the JSON files, or by THANKS_T.
_FRAME = ["Skip to content", "BON VOYAGE", "DEPART", "WELCOME", "ARRIVE", "Back to Stamped!",
          "Support", "Privacy", "City guides"]
THANKS_PAGES = {
    "stamped-check-inbox": _FRAME + [
        "Check your inbox · Stamped! A City Passport", "ALMOST THERE", "INBOX", "Check your inbox.",
        "Tap the link in our email to confirm, and you're on the list.",
        "Can't find it? Look in your spam or promotions folder."],
    "stamped-subscribed": _FRAME + [
        "You're on the list · Stamped! A City Passport", "ON THE LIST", "NEWS", "You're on the list.",
        "Thanks for confirming. We'll email you when new cities and campuses arrive.",
        "A few emails a year. Unsubscribe anytime."],
}
# Strings only these pages have: english -> {language: translation}
THANKS_T = {
    "Check your inbox · Stamped! A City Passport": {
        "es": "Revisa tu correo · Stamped! A City Passport",
        "de": "Schau in dein Postfach · Stamped! A City Passport",
        "ja": "メールを確認してください · Stamped! A City Passport",
        "fr": "Vérifiez votre boîte mail · Stamped! A City Passport",
        "it": "Controlla la posta · Stamped! A City Passport",
        "ko": "받은편지함을 확인하세요 · Stamped! A City Passport",
        "pt": "Confira seu e-mail · Stamped! A City Passport",
        "zh": "请查看你的邮箱 · Stamped! A City Passport"},
    "Can't find it? Look in your spam or promotions folder.": {
        "es": "¿No lo encuentras? Mira en la carpeta de spam o de promociones.",
        "de": "Nicht gefunden? Schau im Spam- oder Werbung-Ordner nach.",
        "ja": "見つからない場合は、迷惑メールやプロモーションのフォルダを確認してください。",
        "fr": "Vous ne le trouvez pas ? Regardez dans vos spams ou dans l'onglet Promotions.",
        "it": "Non la trovi? Controlla nella cartella spam o promozioni.",
        "ko": "메일이 보이지 않나요? 스팸함이나 프로모션함을 확인해 보세요.",
        "pt": "Não encontrou? Veja na pasta de spam ou de promoções.",
        "zh": "找不到？请查看垃圾邮件或推广邮件文件夹。"},
    "You're on the list · Stamped! A City Passport": {
        "es": "Ya estás en la lista · Stamped! A City Passport",
        "de": "Du bist dabei · Stamped! A City Passport",
        "ja": "登録が完了しました · Stamped! A City Passport",
        "fr": "Vous êtes inscrit · Stamped! A City Passport",
        "it": "Sei nella lista · Stamped! A City Passport",
        "ko": "구독 완료 · Stamped! A City Passport",
        "pt": "Você está na lista · Stamped! A City Passport",
        "zh": "订阅成功 · Stamped! A City Passport"},
    "ON THE LIST": {"es": "EN LA LISTA", "de": "DABEI", "ja": "登録完了", "fr": "INSCRIT",
                    "it": "NELLA LISTA", "ko": "구독 완료", "pt": "NA LISTA", "zh": "订阅成功"},
    "NEWS": {"es": "NOTICIAS", "de": "NEWS", "ja": "ニュース", "fr": "INFOS",
             "it": "NOVITÀ", "ko": "소식", "pt": "NOVIDADES", "zh": "资讯"},
    "You're on the list.": {
        "es": "Ya estás en la lista.", "de": "Du bist dabei.", "ja": "登録が完了しました。",
        "fr": "Vous êtes inscrit.", "it": "Sei nella lista.", "ko": "구독이 완료되었어요.",
        "pt": "Você está na lista.", "zh": "订阅成功。"},
    "Thanks for confirming. We'll email you when new cities and campuses arrive.": {
        "es": "Gracias por confirmar. Te escribiremos cuando lleguen nuevas ciudades y campus.",
        "de": "Danke für die Bestätigung. Wir schreiben dir, wenn neue Städte und Campusse dazukommen.",
        "ja": "ご確認ありがとうございます。新しい都市やキャンパスが追加されたらメールでお知らせします。",
        "fr": "Merci d'avoir confirmé. Nous vous écrirons quand de nouvelles villes et de nouveaux campus arriveront.",
        "it": "Grazie per la conferma. Ti scriveremo quando arriveranno nuove città e nuovi campus.",
        "ko": "확인해 주셔서 감사합니다. 새로운 도시와 캠퍼스가 추가되면 이메일로 알려 드릴게요.",
        "pt": "Obrigado por confirmar. Vamos avisar você por e-mail quando chegarem novas cidades e campi.",
        "zh": "感谢确认。新的城市和校园上线时，我们会发邮件通知你。"},
    "Back to Stamped!": {
        "es": "Volver a Stamped!", "de": "Zurück zu Stamped!", "ja": "Stamped!に戻る",
        "fr": "Retour à Stamped!", "it": "Torna a Stamped!", "ko": "Stamped!로 돌아가기",
        "pt": "Voltar ao Stamped!", "zh": "返回 Stamped!"},
}


def build_thanks(name, lang, source):
    """One sign-up page (a THANKS_PAGES name) in one language. Stops if a string is missing, like build()."""
    html = source
    table = dict(translations(lang)[0])
    table.update({english: by_lang[lang] for english, by_lang in THANKS_T.items()})
    for english in THANKS_PAGES[name]:
        find, wrap = pattern(english)
        if find not in html:
            raise SystemExit(f"{name}.html no longer has: {english}")
        html = html.replace(find, wrap(table[english]))
    # The page's language, and links back to the landing page in the same language
    html = html.replace('<html lang="en">', f'<html lang="{HTML_LANG.get(lang, lang)}">')
    html = html.replace('href="stamped-app.html"', f'href="stamped-app-{lang}.html"')
    return html


def pattern(english):
    if english.startswith("!"):
        return english[1:], lambda t: t
    if english.startswith("@"):
        return f'="{english[1:]}"', lambda t: f'="{t}"'
    return f">{english}<", lambda t: f">{t}<"


def translations(lang):
    """(rows, copy) for one language: rows are (english, translation) pairs in T's order."""
    if lang in TABLE_LANGS:
        col = TABLE_LANGS.index(lang) + 1
        return [(row[0], row[col]) for row in T], COPY[lang]
    data = json.loads((JSON_DIR / f"{lang}.json").read_text(encoding="utf-8"))
    untranslated = [row[0] for row in T if row[0] not in data["rows"]]
    if untranslated:
        raise SystemExit(f"{lang}.json has no translation for:\n  " + "\n  ".join(untranslated))
    return [(row[0], data["rows"][row[0]]) for row in T], data["copy"]


def build(lang, source):
    html = source
    rows, copy = translations(lang)
    hl = HTML_LANG.get(lang, lang)
    missing = []
    for english, translated in rows:
        find, wrap = pattern(english)
        if find not in html:
            missing.append(english)
            continue
        html = html.replace(find, wrap(translated))
    if missing:
        raise SystemExit("These English strings are no longer on the page; update the table:\n  " + "\n  ".join(missing))

    # The runtime text block
    start = html.index("            window.stampedCopy = {")
    end = html.index("};", start) + 2
    html = html[:start] + "            window.stampedCopy = " + copy + ";" + html[end:]

    page = f"stamped-app-{lang}.html"
    swaps = [
        ('<html lang="en">', f'<html lang="{hl}">'),
        ('<link rel="canonical" href="https://georgeclinkscalesdev.com/stamped-app.html" />',
         f'<link rel="canonical" href="https://georgeclinkscalesdev.com/{page}" />'),
        ('<meta property="og:url" content="https://georgeclinkscalesdev.com/stamped-app.html" />',
         f'<meta property="og:url" content="https://georgeclinkscalesdev.com/{page}" />'),
        ('"url": "https://georgeclinkscalesdev.com/stamped-app.html"', f'"url": "https://georgeclinkscalesdev.com/{page}"'),
        ('content="en_US"', f'content="{LOCALE[lang]}"'),
        ('https://apps.apple.com/us/app/stamped-a-city-passport/id6759680336',
         f'https://apps.apple.com/{STORE[lang]}/app/stamped-a-city-passport/id6759680336'),
        # The label starts with the visible code, so voice control ("tap DE") and screen readers agree
        ('<summary aria-label="EN · English"><i class="fas fa-globe" aria-hidden="true"></i>EN</summary>',
         f'<summary aria-label="{lang.upper()} · {NAME[lang]}"><i class="fas fa-globe" aria-hidden="true"></i>{lang.upper()}</summary>'),
        ('hreflang="en" lang="en" aria-current="page">', 'hreflang="en" lang="en">'),
        (f'<li><a href="{page}" hreflang="{hl}" lang="{hl}">',
         f'<li><a href="{page}" hreflang="{hl}" lang="{hl}" aria-current="page">'),
        ('<a class="brand" href="stamped-app.html">', f'<a class="brand" href="{page}">'),
        ('"downloadUrl": "https://apps.apple.com/us/', f'"downloadUrl": "https://apps.apple.com/{STORE[lang]}/'),
    ]
    for old, new in swaps:
        if old in html:
            html = html.replace(old, new)
        elif not old.startswith('"downloadUrl"'):
            raise SystemExit(f"Expected to find: {old}")
    return html


def versioned(html):
    """`html` with each shared file's ?v= set to a hash of the file, so browsers fetch the new copy
    after a change instead of a cached old one (like the city pages' versioned())."""
    for name in SHARED:
        stamp = hashlib.sha1((ROOT / name).read_bytes()).hexdigest()[:8]
        html = re.sub(rf'"{re.escape(name)}(\?v=[0-9a-f]+)?"', f'"{name}?v={stamp}"', html)
    return html


def main():
    source = versioned(SOURCE.read_text(encoding="utf-8"))
    SOURCE.write_text(source, encoding="utf-8")
    for lang in LANGS:
        out = ROOT / f"stamped-app-{lang}.html"
        out.write_text(build(lang, source), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))
    for name in THANKS_PAGES:
        page = ROOT / f"{name}.html"
        english = versioned(page.read_text(encoding="utf-8"))
        page.write_text(english, encoding="utf-8")
        for lang in LANGS:
            out = ROOT / f"{name}-{lang}.html"
            out.write_text(build_thanks(name, lang, english), encoding="utf-8")
            print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
