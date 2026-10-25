#!/usr/bin/env python3
"""Build the Spanish, German and Japanese Stamped! landing pages from the English one.

    python3 tools/stamped/build_translations.py

Reads stamped-app.html and writes stamped-app-es.html, stamped-app-de.html and
stamped-app-ja.html. Edit the English page, then re-run this. If an English string
below no longer exists on the page the script stops and names it, so a changed
sentence never silently stays in English.

Wording follows the app's own Localizable.strings (sello / Stempel / スタンプ).

Each entry is (english, spanish, german, japanese). The english string is matched as:
  plain text   -> a whole text node:   >text<
  "@" prefix   -> an attribute value:  ="text"
  "!" prefix   -> anywhere, exactly as written (CSS, JSON, URLs)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "stamped-app.html"
LANGS = ["es", "de", "ja"]
STORE = {"es": "es", "de": "de", "ja": "jp"}          # App Store country codes
LOCALE = {"es": "es_ES", "de": "de_DE", "ja": "ja_JP"}
NAME = {"es": "español", "de": "Deutsch", "ja": "日本語"}

T = [
    # ----- <head> -----
    ("Stamped! A City Passport: The World's Great Buildings",
     "Stamped! A City Passport: los grandes edificios del mundo",
     "Stamped! A City Passport: die großen Bauwerke der Welt",
     "Stamped! A City Passport：世界の名建築をスタンプで集めよう"),
    ("@Collect a passport stamp at more than 1,800 architectural landmarks in 140 cities on six continents and 101 university campuses. Fly through cities in 3D, meet the architects, take the quiz, and plan your trip. Free on iPhone and iPad.",
     "Consigue un sello en tu pasaporte en más de 1.800 monumentos arquitectónicos de 140 ciudades en seis continentes y 101 campus universitarios. Sobrevuela ciudades en 3D, conoce a los arquitectos, haz el quiz y planifica tu viaje. Gratis para iPhone y iPad.",
     "Sammle Passstempel an mehr als 1.800 architektonischen Sehenswürdigkeiten in 140 Städten auf sechs Kontinenten und an 101 Universitäten. Fliege in 3D durch Städte, lerne die Architekten kennen, mach das Quiz und plane deine Reise. Kostenlos für iPhone und iPad.",
     "6大陸140都市の1,800以上の名建築と、101の大学キャンパスでパスポートスタンプを集めよう。3Dで街を飛び回り、建築家を知り、クイズに挑戦して、旅を計画。iPhoneとiPadで無料。"),
    ("!\"description\": \"Collect a passport stamp at more than 1,800 architectural landmarks in 140 cities on six continents and 101 university campuses. Fly through cities in 3D, meet the architects, take the quiz, and plan your trip.\"",
     "\"description\": \"Consigue un sello en tu pasaporte en más de 1.800 monumentos arquitectónicos de 140 ciudades en seis continentes y 101 campus universitarios. Sobrevuela ciudades en 3D, conoce a los arquitectos, haz el quiz y planifica tu viaje.\"",
     "\"description\": \"Sammle Passstempel an mehr als 1.800 architektonischen Sehenswürdigkeiten in 140 Städten auf sechs Kontinenten und an 101 Universitäten. Fliege in 3D durch Städte, lerne die Architekten kennen, mach das Quiz und plane deine Reise.\"",
     "\"description\": \"6大陸140都市の1,800以上の名建築と、101の大学キャンパスでパスポートスタンプを集めよう。3Dで街を飛び回り、建築家を知り、クイズに挑戦して、旅を計画。\""),
    ("@1,800+ landmarks, 140 cities, six continents, 101 campuses. Fly through them in 3D and collect a stamp at every one you visit.",
     "Más de 1.800 monumentos, 140 ciudades, seis continentes, 101 campus. Sobrevuélalos en 3D y consigue un sello en cada uno que visites.",
     "1.800+ Sehenswürdigkeiten, 140 Städte, sechs Kontinente, 101 Campusse. Fliege in 3D hindurch und sammle an jedem Ort, den du besuchst, einen Stempel.",
     "1,800以上の名建築、140都市、6大陸、101キャンパス。3Dで飛び回り、訪れた場所ごとにスタンプを集めよう。"),

    # ----- Header -----
    ("Skip to content", "Saltar al contenido", "Zum Inhalt springen", "本文へスキップ"),
    ("@Page sections", "Secciones de la página", "Seitenbereiche", "ページ内のセクション"),
    ("Explore", "Explorar", "Entdecken", "探索"),
    ("Quiz", "Quiz", "Quiz", "クイズ"),
    ("Trips", "Viajes", "Reisen", "旅行"),
    ("Campuses", "Campus", "Campusse", "キャンパス"),
    ("Get the app", "Descargar", "App laden", "アプリを入手"),

    # ----- Hero -----
    ("A city passport · Free on iPhone &amp; iPad",
     "Un pasaporte de ciudades · Gratis para iPhone y iPad",
     "Ein Städte-Reisepass · Kostenlos für iPhone &amp; iPad",
     "都市のパスポート · iPhone・iPadで無料"),
    ("The world's great buildings, ", "Los grandes edificios del mundo, ", "Die großen Bauwerke der Welt, ", "世界の名建築を、"),
    ("stamped.", "sellados.", "gestempelt.", "スタンプで。"),
    ("From the Great Pyramid to Fallingwater, fly through real cities in 3D, learn who built what and why, and earn a passport stamp at every landmark you visit.",
     "De la Gran Pirámide a la Casa de la Cascada: sobrevuela ciudades reales en 3D, descubre quién construyó qué y por qué, y consigue un sello en tu pasaporte en cada monumento que visites.",
     "Von der Großen Pyramide bis Fallingwater: Fliege in 3D durch echte Städte, erfahre, wer was warum gebaut hat, und sammle an jeder Sehenswürdigkeit, die du besuchst, einen Stempel für deinen Reisepass.",
     "ギザの大ピラミッドから落水荘まで。リアルな3Dの街を飛び回り、誰が何をなぜ建てたのかを知り、訪れた名建築ごとにパスポートスタンプを集めよう。"),
    ("!<small>Download on the</small><strong>App Store</strong>",
     "<small>Descárgalo en el</small><strong>App Store</strong>",
     "<small>Laden im</small><strong>App Store</strong>",
     "<small>App Storeから</small><strong>ダウンロード</strong>"),
    ("Free · iPhone &amp; iPad", "Gratis · iPhone y iPad", "Kostenlos · iPhone &amp; iPad", "無料 · iPhone・iPad"),
    ("@QR code that opens Stamped! on the App Store",
     "Código QR que abre Stamped! en el App Store",
     "QR-Code, der Stamped! im App Store öffnet",
     "App StoreでStamped!を開くQRコード"),
    ("On your computer?", "¿Estás en el ordenador?", "Am Computer?", "パソコンでご覧ですか？"),
    ("Scan with your iPhone camera.", "Escanéalo con la cámara de tu iPhone.", "Scanne ihn mit der iPhone-Kamera.", "iPhoneのカメラで読み取ってください。"),
    ("Passport · Stamped!", "Pasaporte · Stamped!", "Reisepass · Stamped!", "パスポート · Stamped!"),
    ("Type P", "Tipo P", "Typ P", "タイプ P"),
    ("!<strong>1,800+</strong>", "<strong>1.800+</strong>", "<strong>1.800+</strong>", "<strong>1,800+</strong>"),
    ("Landmarks", "Monumentos", "Bauwerke", "名建築"),
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
    ("Fly through 140 cities in photoreal 3D and read the story behind every building.",
     "Sobrevuela 140 ciudades en 3D fotorrealista y lee la historia de cada edificio.",
     "Fliege in fotorealistischem 3D durch 140 Städte und lies die Geschichte hinter jedem Gebäude.",
     "140都市をフォトリアルな3Dで飛び回り、建物ごとの物語を読もう。"),
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
    ("Six continents · 140 cities", "Seis continentes · 140 ciudades", "Sechs Kontinente · 140 Städte", "6大陸 · 140都市"),
    ("Every continent you can fly to.", "Todos los continentes a los que puedes volar.", "Alle Kontinente, die du anfliegen kannst.", "飛行機で行けるすべての大陸へ。"),
    ("Not just the usual capitals. Stamped! covers 140 cities, from Reykjavik to Zanzibar, each with its own landmarks, quiz and stamp.",
     "No solo las capitales de siempre. Stamped! cubre 140 ciudades, de Reikiavik a Zanzíbar, cada una con sus monumentos, su quiz y su sello.",
     "Nicht nur die üblichen Hauptstädte. Stamped! umfasst 140 Städte von Reykjavík bis Sansibar, jede mit eigenen Sehenswürdigkeiten, eigenem Quiz und eigenem Stempel.",
     "定番の首都だけではありません。レイキャビクからザンジバルまで140都市を収録。どの都市にも名建築、クイズ、スタンプがあります。"),
    ("Europe ", "Europa ", "Europa ", "ヨーロッパ "),
    ("Asia ", "Asia ", "Asien ", "アジア "),
    ("North America ", "Norteamérica ", "Nordamerika ", "北米 "),
    ("South America ", "Sudamérica ", "Südamerika ", "南米 "),
    ("Africa ", "África ", "Afrika ", "アフリカ "),
    ("Oceania ", "Oceanía ", "Ozeanien ", "オセアニア "),
    ("34 cities", "34 ciudades", "34 Städte", "34都市"),
    ("38 cities", "38 ciudades", "38 Städte", "38都市"),
    ("37 cities", "37 ciudades", "37 Städte", "37都市"),
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
    ("Browse all 140 city guides ", "Ver las 140 guías de ciudades (en inglés) ", "Alle 140 Stadtführer ansehen (auf Englisch) ", "140都市のガイドを見る（英語） "),

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
    ("Every landmark comes with its architect, style, build date, height and history. Stamped! keeps track of whose buildings you've seen and shows your favorite architect.",
     "Cada monumento incluye su arquitecto, estilo, año de construcción, altura e historia. Stamped! recuerda de quién son los edificios que has visto y te muestra tu arquitecto favorito.",
     "Zu jeder Sehenswürdigkeit gibt es Architekt, Stil, Baujahr, Höhe und Geschichte. Stamped! merkt sich, wessen Bauwerke du gesehen hast, und zeigt deinen Lieblingsarchitekten.",
     "名建築ごとに建築家、様式、建築年、高さ、歴史を収録。誰の建物を見たかを記録し、お気に入りの建築家を表示します。"),
    ("@Some of the architects in Stamped!, with how many of their buildings are in the app",
     "Algunos de los arquitectos de Stamped!, con cuántos de sus edificios hay en la app",
     "Einige Architekten in Stamped! und wie viele ihrer Bauwerke in der App sind",
     "Stamped!に登場する建築家の一部と、アプリ内の作品数"),
    ("@Landmarks span from 2560 BC to 2026", "Los monumentos van del 2560 a. C. a 2026", "Die Sehenswürdigkeiten reichen von 2560 v. Chr. bis 2026", "紀元前2560年から2026年までの名建築"),
    ("2560 BC", "2560 a. C.", "2560 v. Chr.", "紀元前2560年"),
    ("Great Pyramid of Giza", "Gran Pirámide de Guiza", "Cheops-Pyramide von Gizeh", "ギザの大ピラミッド"),
    ("Waterline, Austin", "Waterline, Austin", "Waterline, Austin", "ウォーターライン（オースティン）"),
    ("!content: \"4,500+ years\";", "content: \"más de 4.500 años\";", "content: \"über 4.500 Jahre\";", "content: \"4,500年以上\";"),
    ("@My Journey screen with 171 stamps, cities visited and mastered, and a favorite architect card for Albert Kahn",
     "Pantalla Mi viaje con 171 sellos, ciudades visitadas y dominadas, y Albert Kahn como arquitecto favorito",
     "Bildschirm Meine Reise mit 171 Stempeln, besuchten und gemeisterten Städten und Albert Kahn als Lieblingsarchitekt",
     "171個のスタンプ、訪れた都市と制覇した都市、お気に入りの建築家アルバート・カーンを表示したマイジャーニー画面"),
    ("FAVORITE ARCHITECT", "ARQUITECTO FAVORITO", "LIEBLINGSARCHITEKT", "お気に入りの建築家"),

    # ----- Quiz -----
    ("Play · Architecture quiz", "Juega · Quiz de arquitectura", "Spielen · Architektur-Quiz", "遊ぶ · 建築クイズ"),
    ("Test your ", "Pon a prueba ", "Teste dein ", "あなたの"),
    ("smarts.", "lo que sabes.", "Wissen.", "知識を試そう。"),
    ("Every city and every campus has its own 10-question quiz built from its real landmarks: the style, the year, the architect, the number of floors. 241 quizzes in all, in 9 languages. Tap your answer or say it out loud.",
     "Cada ciudad y cada campus tiene su propio quiz de 10 preguntas basado en sus monumentos reales: el estilo, el año, el arquitecto, el número de plantas. 241 quizzes en total, en 9 idiomas. Toca tu respuesta o dila en voz alta.",
     "Jede Stadt und jeder Campus hat ein eigenes Quiz mit 10 Fragen zu seinen echten Sehenswürdigkeiten: Stil, Baujahr, Architekt, Anzahl der Stockwerke. Insgesamt 241 Quizze in 9 Sprachen. Tippe deine Antwort an oder sag sie laut.",
     "どの都市・キャンパスにも、実在の名建築から作られた10問のクイズがあります。様式、建築年、建築家、階数。全241クイズ、9言語に対応。タップでも音声でも答えられます。"),
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
    ("Trips sync with iCloud between iPhone and iPad",
     "Los viajes se sincronizan con iCloud entre iPhone y iPad",
     "Reisen werden per iCloud zwischen iPhone und iPad synchronisiert",
     "旅程はiCloudでiPhoneとiPadに同期"),
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
    ("Hotels on the map and a hotel search for your trip dates.", "Hoteles en el mapa y búsqueda de hotel para las fechas de tu viaje.", "Hotels auf der Karte und eine Hotelsuche für deine Reisedaten.", "マップ上のホテルと、旅行日程に合わせたホテル検索。"),
    ("Places to eat", "Dónde comer", "Essen gehen", "食事"),
    ("Top eats near the landmarks, plus food and coffee on the map.", "Los mejores sitios para comer cerca de los monumentos, y comida y café en el mapa.", "Die besten Lokale nahe den Sehenswürdigkeiten, dazu Essen und Kaffee auf der Karte.", "名建築の近くの人気店と、マップ上の食事・カフェ。"),
    ("Events", "Eventos", "Events", "イベント"),
    ("Upcoming concerts and games at landmark venues, with ticket links.", "Próximos conciertos y partidos en recintos emblemáticos, con enlaces a entradas.", "Kommende Konzerte und Spiele an bekannten Veranstaltungsorten, mit Ticket-Links.", "名所の会場で開かれるコンサートや試合を、チケットリンク付きで。"),
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
    ("New in 2.5 · Campus visits", "Novedad en 2.5 · Visitas a campus", "Neu in 2.5 · Campusbesuche", "2.5の新機能 · キャンパス訪問"),
    ("Plus 101 ", "Y 101 ", "Dazu 101 ", "さらに101の"),
    ("campuses.", "campus.", "Campusse.", "キャンパス。"),
    ("Every Big Ten, SEC, ACC and Big 12 school, the Ivy League, and great campuses from Oxford to Melbourne. Built for college visits, and for anyone who loves a good quad.",
     "Todas las universidades del Big Ten, la SEC, la ACC y el Big 12, la Ivy League y grandes campus de Oxford a Melbourne. Pensado para visitar universidades y para cualquiera a quien le guste un buen campus.",
     "Jede Uni aus Big Ten, SEC, ACC und Big 12, die Ivy League und großartige Campusse von Oxford bis Melbourne. Gemacht für College-Besuche und für alle, die einen schönen Campus lieben.",
     "Big Ten、SEC、ACC、Big 12の全校、アイビーリーグ、そしてオックスフォードからメルボルンまでの名門キャンパス。大学見学にも、美しいキャンパスが好きな人にも。"),
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
    ("High-contrast and reduced-motion options, plus a dark mode.", "Opciones de alto contraste y movimiento reducido, y modo oscuro.", "Optionen für hohen Kontrast und reduzierte Bewegung, dazu ein Dunkelmodus.", "高コントラスト、視差効果を減らす設定、ダークモードに対応。"),

    # ----- Closing call to action -----
    ("BON VOYAGE", "BUEN VIAJE", "GUTE REISE", "よい旅を"),
    ("DEPART", "SALIDA", "ABFLUG", "出発"),
    ("WELCOME", "BIENVENIDO", "WILLKOMMEN", "ようこそ"),
    ("ARRIVE", "LLEGADA", "ANKUNFT", "到着"),
    ("Your passport is waiting.", "Tu pasaporte te espera.", "Dein Reisepass wartet.", "パスポートが待っています。"),
    ("1,800+ landmarks. One stamp each. Free on iPhone and iPad.",
     "Más de 1.800 monumentos. Un sello por cada uno. Gratis para iPhone y iPad.",
     "1.800+ Sehenswürdigkeiten. Ein Stempel für jede. Kostenlos für iPhone und iPad.",
     "1,800以上の名建築。ひとつにつきスタンプひとつ。iPhoneとiPadで無料。"),

    # ----- Landmark photos and guided tours -----
    ('Inside the app · 1,800+ landmarks', 'Dentro de la app · Más de 1.800 monumentos', 'In der App · 1.800+ Sehenswürdigkeiten', 'アプリの中身 · 1,800以上の名建築'),
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
    ("Apple, the Apple logo, iPhone and iPad are trademarks of Apple Inc. App Store is a service mark of Apple Inc.",
     "Apple, el logotipo de Apple, iPhone y iPad son marcas comerciales de Apple Inc. App Store es una marca de servicio de Apple Inc.",
     "Apple, das Apple Logo, iPhone und iPad sind Marken der Apple Inc. App Store ist eine Dienstleistungsmarke der Apple Inc.",
     "Apple、Appleのロゴ、iPhone、iPadはApple Inc.の商標です。App StoreはApple Inc.のサービスマークです。"),
]

# Text the quiz and video script write at runtime (replaces the whole `var copy = {...};` block)
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
                more: 'La app tiene 241 quizzes y 2.410 preguntas.',
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
                more: 'Die App hat 241 Quizze mit 2.410 Fragen.',
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
                more: 'アプリには241のクイズ、2,410問があります。',
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


def pattern(english):
    if english.startswith("!"):
        return english[1:], lambda t: t
    if english.startswith("@"):
        return f'="{english[1:]}"', lambda t: f'="{t}"'
    return f">{english}<", lambda t: f">{t}<"


def build(lang, source):
    html = source
    col = LANGS.index(lang) + 1
    missing = []
    for row in T:
        find, wrap = pattern(row[0])
        if find not in html:
            missing.append(row[0])
            continue
        html = html.replace(find, wrap(row[col]))
    if missing:
        raise SystemExit("These English strings are no longer on the page; update the table:\n  " + "\n  ".join(missing))

    # The runtime text block
    start = html.index("            var copy = {")
    end = html.index("};", start) + 2
    html = html[:start] + "            var copy = " + COPY[lang] + ";" + html[end:]

    page = f"stamped-app-{lang}.html"
    swaps = [
        ('<html lang="en">', f'<html lang="{lang}">'),
        ('<link rel="canonical" href="https://georgeclinkscalesdev.com/stamped-app.html" />',
         f'<link rel="canonical" href="https://georgeclinkscalesdev.com/{page}" />'),
        ('<meta property="og:url" content="https://georgeclinkscalesdev.com/stamped-app.html" />',
         f'<meta property="og:url" content="https://georgeclinkscalesdev.com/{page}" />'),
        ('"url": "https://georgeclinkscalesdev.com/stamped-app.html"', f'"url": "https://georgeclinkscalesdev.com/{page}"'),
        ('content="en_US"', f'content="{LOCALE[lang]}"'),
        ('https://apps.apple.com/us/app/stamped-a-city-passport/id6759680336',
         f'https://apps.apple.com/{STORE[lang]}/app/stamped-a-city-passport/id6759680336'),
        ('<summary aria-label="Language: English"><i class="fas fa-globe" aria-hidden="true"></i>EN</summary>',
         f'<summary aria-label="{NAME[lang]}"><i class="fas fa-globe" aria-hidden="true"></i>{lang.upper()}</summary>'),
        ('hreflang="en" lang="en" aria-current="page">', 'hreflang="en" lang="en">'),
        (f'<li><a href="{page}" hreflang="{lang}" lang="{lang}">',
         f'<li><a href="{page}" hreflang="{lang}" lang="{lang}" aria-current="page">'),
        ('<a class="brand" href="stamped-app.html">', f'<a class="brand" href="{page}">'),
        ('"downloadUrl": "https://apps.apple.com/us/', f'"downloadUrl": "https://apps.apple.com/{STORE[lang]}/'),
    ]
    for old, new in swaps:
        if old in html:
            html = html.replace(old, new)
        elif not old.startswith('"downloadUrl"'):
            raise SystemExit(f"Expected to find: {old}")
    return html


def main():
    source = SOURCE.read_text(encoding="utf-8")
    for lang in LANGS:
        out = ROOT / f"stamped-app-{lang}.html"
        out.write_text(build(lang, source), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
