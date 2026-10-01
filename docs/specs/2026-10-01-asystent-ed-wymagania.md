# Asystent ED — specyfikacja wymagań

**Wersja:** 1.0 (szkic do akceptacji)
**Data:** 2026-10-01
**Autor:** Marta Trybus
**Status:** do przeglądu

---

## 1. Cel i kontekst

Dziecko w edukacji domowej (7 klasa SP) uczy się z podręczników i listy zagadnień. Problem: część tematów wymaga wytłumaczenia, a rodzic nie zawsze potrafi to zrobić.

**Asystent ED** to aplikacja webowa, która:
- na podstawie zagadnień i materiałów (podręcznik, podstawa programowa) generuje testy i sprawdza, czy temat jest opanowany,
- przy błędnej odpowiedzi pokazuje prawidłową odpowiedź i wyjaśnia, dlaczego,
- pilnuje harmonogramu do egzaminów klasyfikacyjnych i wskazuje, co trzeba nadrobić,
- oferuje czat z asystentem („Nie rozumiem, wyjaśnij”), który prowadzi dialog z przykładami i zadaniami, aż upewni się, że dziecko zrozumiało,
- tam, gdzie pomaga to zrozumieć temat, pokazuje proste animacje,
- opiera wszystkie treści na potwierdzonych źródłach (ochrona przed halucynacjami modelu).

### 1.1 Kryteria sukcesu
- Dziecko samodzielnie (bez rodzica) rozumie trudny temat i potrafi rozwiązać zadania sprawdzające.
- Rodzic w jednym miejscu widzi: co opanowane, co zaległe, ile zostało do egzaminu.
- Żadna treść merytoryczna nie pojawia się bez wskazania źródła.
- Miesięczny koszt AI nie przekracza 150 zł.

### 1.2 Użytkownicy
| Rola | Opis |
|---|---|
| **Rodzic** | Konfiguruje przedmioty, zagadnienia, materiały i harmonogram; ma pełny wgląd w postępy i rozmowy. |
| **Dziecko** | Uczy się: plan dnia, testy, czat z asystentem, animacje, powtórki. |

---

## 2. Zakres

### 2.1 MVP (etap 1)
- Jedna rodzina (1 rodzic, 1+ dzieci), uruchamiane **lokalnie** na komputerze domowym.
- Obsługa przez przeglądarkę na **komputerze** (układ responsywny, ale testowany tylko na desktopie).
- Przedmioty na start: **geografia, fizyka, matematyka, język polski, język angielski, język niemiecki**.
- Wszystkie funkcje opisane w rozdziale 3, chyba że oznaczono je jako „później”.

### 2.2 Rozwój (kolejne etapy — architektura musi je umożliwić, ale nie są w MVP)
- Wiele rodzin, rejestracja, hosting w chmurze, RODO dla danych dzieci, ewentualnie płatności.
- Wersja mobilna / tablet (dotyk, pisanie rysikiem).
- Mówienie do asystenta (rozpoznawanie mowy) i ocena wymowy w językach obcych.
- Wtyczka do przeglądarki robiąca zrzut strony flipbooka jednym kliknięciem.
- Animacje interaktywne (suwaki, parametry) poza mapą.
- Kolejne przedmioty 7 klasy i kolejne klasy.

### 2.3 Poza zakresem
- Rozwiązywanie zadań domowych „za dziecko”.
- Rozmowy niezwiązane z nauką.
- Automatyczne pobieranie treści z flipbooków wydawców (logowanie, prawa autorskie).

---

## 3. Wymagania funkcjonalne

Oznaczenia: **[M]** — MVP, **[P]** — później.

### 3.1 Przedmioty i zagadnienia
- **F-01 [M]** Rodzic definiuje przedmioty; system ma wbudowane 6 przedmiotów startowych i pozwala dodawać kolejne.
- **F-02 [M]** Rodzic tworzy listę zagadnień dla przedmiotu (np. „Matematyka kl. 7 — potęgi”), ręcznie lub przez import z podstawy programowej.
- **F-03 [M]** Każde zagadnienie jest powiązane z wymaganiami podstawy programowej MEN (kod/punkt wymagania).
- **F-04 [M]** Zagadnienie może mieć przypisane materiały (rozdział 3.2); bez materiałów system korzysta z podstawy programowej i źródeł zewnętrznych z listy dopuszczonych.

### 3.2 Materiały i źródła
- **F-10 [M]** Rodzic dodaje materiały z podręcznika jako:
  - zrzuty ekranu / zdjęcia stron (wklejenie ze schowka, przeciągnięcie pliku),
  - wklejony tekst skopiowany z flipbooka.
- **F-11 [M]** System rozpoznaje z obrazów tekst, wzory matematyczne i opisy rysunków; rodzic może poprawić rozpoznany tekst.
- **F-12 [M]** Każdy materiał ma metadane: przedmiot, podręcznik, strona/rozdział, zagadnienie.
- **F-13 [M]** Trzy poziomy potwierdzonych źródeł:
  1. **Podstawa programowa MEN** — określa zakres wymagań (wgrywana raz).
  2. **Podręczniki rodziny** — materiały dodane przez rodzica.
  3. **Zewnętrzne źródła z listy dopuszczonych** — m.in. epodreczniki.pl / Zintegrowana Platforma Edukacyjna, słowniki (PWN, Cambridge/Oxford, Duden). Rodzic może edytować listę.
- **F-14 [M]** Materiały są przechowywane wyłącznie lokalnie i służą tylko rodzinie.
- **F-15 [P]** Wtyczka do przeglądarki do zrzutów stron flipbooka.

### 3.3 Harmonogram i zaległości
- **F-20 [M]** Rodzic wpisuje daty egzaminów klasyfikacyjnych dla każdego przedmiotu.
- **F-21 [M]** System rozkłada zagadnienia na tygodnie do daty egzaminu (z buforem na powtórki przed egzaminem).
- **F-22 [M]** Status zagadnienia: *nie rozpoczęte → w trakcie → zaliczone wstępnie → opanowane*; dodatkowo flaga *do powtórki*.
- **F-23 [M]** System wykrywa opóźnienia i pokazuje komunikaty, np. „Do egzaminu z fizyki 6 tygodni, zostało 9 nieopanowanych tematów — tempo zbyt wolne”.
- **F-24 [M]** Plan dnia dla dziecka: nowe tematy + zaległe + powtórki na dziś.
- **F-25 [M]** Rodzic może ręcznie zmienić status zagadnienia (np. oznaczyć jako opanowane).

### 3.4 Testy i ocena
- **F-30 [M]** System generuje testy z danego zagadnienia wyłącznie na podstawie potwierdzonych źródeł (F-13).
- **F-31 [M]** Test sprawdza trzy poziomy:
  - *pamiętam* — fakty, definicje,
  - *rozumiem* — „wyjaśnij, dlaczego…”,
  - *stosuję* — zadanie w nowej sytuacji.
- **F-32 [M]** Typy zadań dopasowane do przedmiotu:
  - matematyka / fizyka: zadania obliczeniowe (wynik + opcjonalnie tok rozumowania), jednokrotny/wielokrotny wybór, prawda/fałsz,
  - geografia: wybór, uzupełnianie, „wskaż na mapie”,
  - język polski: odpowiedzi opisowe, części mowy / zdania, interpretacja krótkiego tekstu,
  - języki obce: słownictwo, gramatyka (uzupełnianie luk, transformacje), rozumienie tekstu.
- **F-33 [M]** Pytania są zatwierdzane **automatycznie** po weryfikacji (rozdział 4); rodzic może oznaczyć pytanie jako błędne — zostaje wtedy wycofane.
- **F-34 [M]** Po błędnej odpowiedzi system pokazuje: prawidłową odpowiedź, wyjaśnienie „dlaczego”, wskazanie typowego błędu oraz przypis do źródła.
- **F-35 [M]** Odpowiedzi opisowe są oceniane przez AI według kryteriów wynikających ze źródła; ocena zawiera uzasadnienie.
- **F-36 [M]** Wyniki obliczeń (matematyka, fizyka) są sprawdzane programowo (silnik obliczeń symbolicznych), a nie przez model językowy.

### 3.5 Kryterium opanowania tematu
- **F-40 [M]** Temat jest *zaliczony wstępnie*, gdy wynik testu wynosi **≥ 80%** i zaliczony jest **każdy** z trzech poziomów (F-31).
- **F-41 [M]** Temat staje się *opanowany* po ponownym zaliczeniu testu w sesji odległej o **co najmniej 2 dni**.
- **F-42 [M]** Przy wyniku **< 50%** system zamiast kolejnego testu proponuje tryb „Wyjaśnij mi”.
- **F-43 [M]** Progi (80% / 2 dni / 50%) są domyślne; rodzic może je zmienić dla każdego przedmiotu.

### 3.6 Powtórki
- **F-50 [M]** System planuje powtórki opanowanych tematów w rosnących odstępach (np. 2 dni → 1 tydzień → 3 tygodnie → przed egzaminem).
- **F-51 [M]** Słaby wynik powtórki przywraca temat do statusu *w trakcie* i skraca odstęp.
- **F-52 [M]** Powtórki są widoczne w planie dnia (F-24) i w harmonogramie przed egzaminem.

### 3.7 Asystent — czat „Nie rozumiem, wyjaśnij”
- **F-60 [M]** Przycisk „Nie rozumiem, wyjaśnij” dostępny przy zagadnieniu, przy każdym pytaniu testowym i przy wyjaśnieniu błędu; otwiera czat z kontekstem (temat, pytanie, odpowiedź dziecka).
- **F-61 [M]** Asystent prowadzi **dialog**: pyta, co jest niejasne, tłumaczy krok po kroku językiem dostosowanym do 13-latka, podaje przykłady z życia, zadaje pytania kontrolne.
- **F-62 [M]** Asystent **naprowadza**, a nie podaje gotowych rozwiązań; pełne rozwiązanie pokazuje dopiero po kilku nieudanych próbach dziecka (liczba prób ustawiana w konfiguracji, domyślnie 3).
- **F-63 [M]** Asystent daje zadania sprawdzające o rosnącym poziomie trudności.
- **F-64 [M]** Asystent kończy wyjaśnianie, gdy dziecko **samodzielnie rozwiąże 2–3 zadania sprawdzające z rzędu** i **wyjaśni temat własnymi słowami**; wtedy proponuje test.
- **F-65 [M]** Asystent zajmuje się wyłącznie nauką: grzecznie odmawia rozmów nie na temat i wraca do tematu.
- **F-66 [M]** Każda informacja merytoryczna w czacie ma przypis do źródła; gdy źródła brak, asystent mówi „nie mam tego w materiałach” i nie zgaduje (rozdział 4).
- **F-67 [M]** Asystent może w trakcie rozmowy wstawić animację lub mapę (rozdział 3.8).
- **F-68 [M]** Wzory matematyczne i chemiczne są poprawnie renderowane.
- **F-69 [M]** Odczyt na głos odpowiedzi asystenta (polski, angielski, niemiecki) — z wykorzystaniem syntezy mowy przeglądarki.
- **F-6A [P]** Mówienie do asystenta i ocena wymowy.

### 3.8 Wizualizacje i animacje
- **F-70 [M]** Animacje są **odtwarzane** (play / pauza / krok wstecz-naprzód), bez interaktywnych parametrów.
- **F-71 [M]** Model hybrydowy:
  1. system najpierw szuka pasującego **szablonu** z biblioteki (AI ustawia tylko parametry i podpisy),
  2. gdy brak szablonu, AI **generuje nową animację** (SVG/canvas),
  3. rodzic może zapisać udaną wygenerowaną animację do biblioteki.
- **F-72 [M]** Animacje są zgodne z tematem zagadnienia, podręcznikiem i podstawą programową; dane liczbowe na animacji pochodzą ze źródła lub z silnika obliczeń.
- **F-73 [M]** Startowa biblioteka szablonów (przykłady):
  - matematyka: wykres funkcji liniowej, figury i twierdzenie Pitagorasa, oś liczbowa, potęgi/pierwiastki wizualnie,
  - fizyka: ruch jednostajny i przyspieszony, siły i ich wypadkowa, prosty obwód elektryczny, fala,
  - geografia: ruch obiegowy Ziemi i pory roku, krążenie wody, strefy klimatyczne,
  - języki / polski: oś czasu (czasy gramatyczne), schemat budowy zdania.
- **F-74 [M]** **Geografia — interaktywna mapa**: przybliżanie/oddalanie, warstwy (polityczna, fizyczna, klimatyczna), klikanie w obiekty z opisem, quizy „wskaż na mapie”. (Wyjątek od F-70 — mapa jest interaktywna.)
- **F-75 [M]** Wygenerowana animacja przed pokazaniem przechodzi kontrolę techniczną (czy się renderuje) i merytoryczną (zgodność opisu ze źródłem); w razie błędu system pokazuje szablon zastępczy lub statyczny schemat.
- **F-76 [P]** Animacje interaktywne (suwaki, parametry).

### 3.9 Panel rodzica
- **F-80 [M]** Przegląd postępów: statusy zagadnień per przedmiot, wyniki testów, tempo vs harmonogram.
- **F-81 [M]** Pełny wgląd w rozmowy dziecka z asystentem oraz w odpowiedzi testowe.
- **F-82 [M]** Automatyczne podsumowania asystenta (np. „miał problem z ułamkami przy potęgach”), dzienne/tygodniowe.
- **F-83 [M]** Zarządzanie przedmiotami, zagadnieniami, materiałami, harmonogramem, progami (F-43), listą dopuszczonych źródeł (F-13).
- **F-84 [M]** Licznik kosztów AI z miesięcznym limitem (rozdział 5.3).
- **F-85 [M]** Zgłaszanie błędnych pytań/wyjaśnień (wycofanie z puli, F-33).

### 3.10 Panel dziecka
- **F-90 [M]** Plan dnia (F-24) z jasnym wskazaniem, co robić teraz.
- **F-91 [M]** Mapa postępów przedmiotów (co opanowane, co przed nami) w przyjaznej formie.
- **F-92 [M]** Dostęp do testów, czatu, animacji, mapy, historii własnych rozmów.

### 3.11 Konta i dostęp
- **F-95 [M]** Osobne logowanie rodzica i dziecka (proste hasło/PIN lokalnie).
- **F-96 [M]** Model danych: *rodzina → rodzice, dzieci*; dane każdej rodziny odseparowane (przygotowanie pod wiele rodzin).
- **F-97 [P]** Rejestracja, wiele rodzin, odzyskiwanie hasła.

---

## 4. Wymagania — ochrona przed halucynacjami

- **H-01 [M]** Wszystkie treści merytoryczne (pytania, poprawne odpowiedzi, wyjaśnienia, opisy animacji) są generowane **wyłącznie na podstawie fragmentów potwierdzonych źródeł** (F-13) wyszukanych dla danego zagadnienia (RAG).
- **H-02 [M]** Każda treść merytoryczna ma **przypis do źródła** (np. „Fizyka 7, s. 54”, „Podstawa programowa, fizyka, pkt II.3”, „epodreczniki.pl — tytuł lekcji”).
- **H-03 [M]** Brak źródła ⇒ brak odpowiedzi merytorycznej: asystent informuje, że temat nie jest pokryty materiałami, i sugeruje rodzicowi dodanie materiału.
- **H-04 [M]** Obliczenia (matematyka, fizyka) i poprawne wyniki zadań liczbowych są wyznaczane i sprawdzane **programowo** (silnik obliczeń symbolicznych), nie przez model językowy.
- **H-05 [M]** Każde wygenerowane pytanie testowe przechodzi **automatyczną weryfikację drugim przebiegiem modelu**: zgodność ze źródłem, jednoznaczność, poprawność klucza odpowiedzi, poziom trudności adekwatny do 7 klasy. Pytania, które nie przejdą weryfikacji, są odrzucane.
- **H-06 [M]** Słownictwo i gramatyka w językach obcych są weryfikowane względem dopuszczonych słowników.
- **H-07 [M]** System zapisuje, z jakich fragmentów źródeł powstała dana treść (ścieżka audytu dla rodzica).
- **H-08 [M]** Rodzic może zgłosić błąd treści; zgłoszenie wycofuje treść i jest uwzględniane przy kolejnych generowaniach.

---

## 5. Wymagania niefunkcjonalne

### 5.1 Technologia i uruchomienie
- **N-01 [M]** Backend: **Python** (proponowane: FastAPI). Frontend: **HTML + JavaScript** z lekkimi bibliotekami (proponowane: Alpine.js, KaTeX do wzorów, Leaflet + OpenStreetMap do map, SVG/GSAP do animacji).
- **N-02 [M]** Baza danych: SQLite (jeden plik) z wyszukiwaniem wektorowym dla źródeł; architektura pozwala na późniejszą migrację do PostgreSQL.
- **N-03 [M]** Uruchomienie **lokalne** jednym poleceniem; dostęp przez przeglądarkę na `localhost`.
- **N-04 [M]** Klucz API przechowywany wyłącznie po stronie serwera (nigdy w przeglądarce).
- **N-05 [M]** Architektura modułowa (treści/źródła, program i plan, testy, tutor, wizualizacje, powtórki, weryfikacja, koszty) — każdy moduł z jasnym interfejsem, testowalny niezależnie.

### 5.2 Modele AI
- **N-10 [M]** **Claude Opus 5.5** (`claude-opus-5-5`), effort **medium** — czat „Wyjaśnij mi”, wyjaśnienia błędnych odpowiedzi, generowanie nowych animacji.
- **N-11 [M]** **Claude Haiku 4.5** (`claude-haiku-4-5`) z **extended thinking** (budżet tokenów konfigurowalny, domyślnie ok. 6 000) — generowanie i weryfikacja pytań, ocena odpowiedzi, rozpoznawanie zrzutów stron, podsumowania dla rodzica.
  *Uwaga: Haiku 4.5 nie obsługuje parametru `effort`; odpowiednikiem „wysokiego wysiłku” jest extended thinking z budżetem tokenów.*
- **N-12 [M]** Przypisanie modeli do zadań jest konfigurowalne (bez zmian w kodzie).
- **N-13 [M]** Odpowiedzi czatu są strumieniowane (dziecko widzi tekst na bieżąco).
- **N-14 [M]** Cache'owanie stałych części promptów i źródeł w celu obniżenia kosztów.

### 5.3 Koszty
- **N-20 [M]** Budżet AI: **150 zł / miesiąc** (szacowane zużycie przy ~1 h nauki dziennie: 75–115 zł).
- **N-21 [M]** Licznik zużycia tokenów i kosztu w panelu rodzica (dziennie / miesięcznie / per funkcja).
- **N-22 [M]** Ostrzeżenie przy 80% budżetu; po przekroczeniu limitu — tryb oszczędny (np. czat na Haiku, tylko szablonowe animacje), konfigurowalny przez rodzica.

### 5.4 Użyteczność
- **N-30 [M]** Interfejs po polsku; język i ton dostosowane do 13-latka (krótko, konkretnie, życzliwie).
- **N-31 [M]** Desktop jako platforma MVP; układ responsywny przygotowany pod tablet/telefon.
- **N-32 [M]** Dostępność: czytelne kontrasty, możliwość powiększenia tekstu, odczyt na głos (F-69).
- **N-33 [M]** Odpowiedź czatu zaczyna się wyświetlać w ciągu kilku sekund.

### 5.5 Bezpieczeństwo i prywatność
- **N-40 [M]** Dane dziecka (rozmowy, wyniki) przechowywane lokalnie; do API wysyłane są tylko treści niezbędne do odpowiedzi, bez danych identyfikujących dziecko.
- **N-41 [M]** Asystent ma zabezpieczenia przed wyjściem poza tematykę nauki i przed nieodpowiednimi treściami.
- **N-42 [M]** Kopia zapasowa bazy (eksport/import pliku) dostępna z panelu rodzica.
- **N-43 [P]** Przy wersji publicznej: RODO dla danych małoletnich, zgody rodzica, polityka praw autorskich do wgrywanych materiałów.

---

## 6. Kluczowe scenariusze (do testów akceptacyjnych)

1. **Dodanie materiału:** rodzic wkleja zrzut strony z podręcznika fizyki → system rozpoznaje tekst i wzory → rodzic przypisuje go do zagadnienia „Ruch jednostajny”.
2. **Test:** dziecko otwiera plan dnia → rozwiązuje test z „Ruchu jednostajnego” → uzyskuje 70% → system pokazuje błędy z wyjaśnieniem i przypisem do źródła → temat pozostaje *w trakcie*.
3. **Wyjaśnienie:** przy błędnym pytaniu dziecko klika „Nie rozumiem, wyjaśnij” → asystent pyta, co niejasne, pokazuje animację ruchu, daje zadanie → dziecko rozwiązuje 3 zadania z rzędu i wyjaśnia własnymi słowami → asystent proponuje test.
4. **Opanowanie:** dziecko zalicza test (≥ 80%, wszystkie poziomy) → *zaliczone wstępnie* → po 2+ dniach zalicza ponownie → *opanowane* → system planuje powtórki.
5. **Zaległości:** rodzic widzi ostrzeżenie „fizyka — tempo zbyt wolne do egzaminu 2027-06-10” i listę zaległych tematów.
6. **Brak źródła:** dziecko pyta o temat bez materiałów i bez pokrycia w źródłach dopuszczonych → asystent odpowiada „nie mam tego w materiałach” i nie zgaduje.
7. **Poza tematem:** dziecko prosi o pomoc w grze → asystent grzecznie odmawia i wraca do nauki.
8. **Mapa:** w geografii dziecko rozwiązuje quiz „wskaż na mapie stolice państw Europy”.
9. **Budżet:** po osiągnięciu 80% budżetu rodzic dostaje ostrzeżenie w panelu.

---

## 7. Ryzyka i założenia

| Ryzyko / założenie | Wpływ | Mitygacja |
|---|---|---|
| Jakość rozpoznawania tekstu ze zrzutów flipbooka (wzory, rysunki) | Błędne źródła → błędne pytania | Rodzic może poprawić rozpoznany tekst (F-11) |
| Haiku 4.5 bez `effort` — mniejsza głębia rozumowania przy weryfikacji | Słabsza weryfikacja pytań | Extended thinking z budżetem; konfigurowalne przypisanie modeli (N-12) |
| Generowane animacje bywają błędne | Mylące wizualizacje | Szablony w pierwszej kolejności, kontrola przed pokazaniem (F-75) |
| Ocena odpowiedzi opisowych (polski) jest subiektywna | Niesprawiedliwa ocena | Kryteria ze źródła, uzasadnienie oceny, wgląd rodzica |
| Dostępność podstawy programowej i epodreczniki.pl w formie do importu | Mniej źródeł | Import ręczny/półautomatyczny; podręczniki rodziny jako główne źródło |
| Prawa autorskie do materiałów podręcznikowych | Blokada rozwoju w produkt | MVP tylko lokalnie i na użytek rodziny; przy produkcie — analiza prawna (N-43) |
| Koszty przy intensywnym użyciu | Przekroczenie 150 zł | Limit i tryb oszczędny (N-22), cache (N-14) |

---

## 8. Otwarte kwestie (do decyzji przed projektem technicznym)

1. Które konkretnie podręczniki (wydawnictwo, tytuł) są używane w każdym z 6 przedmiotów — wpływa na metadane źródeł.
2. Daty egzaminów klasyfikacyjnych w bieżącym roku szkolnym.
3. Czy dziecko ma mieć limit czasu nauki / przerwy (np. przypomnienie o przerwie co 45 min).
4. Czy rodzic chce powiadomień poza aplikacją (e-mail) o zaległościach — w MVP lokalnym raczej nie.
