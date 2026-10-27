// Konto gracza w Supabase: logowanie nickiem i hasłem, zapis wyników, pojęć, bohatera i przerwanej gry.
// Gra dalej czyta i zapisuje localStorage (klucze orion-*), więc bez konta i bez internetu działa jak dotąd (gość).
// Ten plik:
//  - po zalogowaniu pobiera dane konta do localStorage (konto jest źródłem prawdy),
//  - każdą zmianę wysyła do bazy przez kolejkę; bez sieci kolejka czeka i wysyła później,
//  - dokłada przycisk konta w HUD i panel logowania (style z gry: .panel, .btn, .name-row),
//  - rozpoznaje konto twórcy gry (Konto.tworca): wtedy nic nie zapisuje (zob. tworca.js).
// Baza: supabase/migrations/20261019080154_konta_wyniki_zapisy.sql
(() => {
'use strict';
const URL = 'https://wmcjrmbomzwuyoftuxvx.supabase.co';
const KEY = 'sb_publishable_a8nGtCvtwzIV25rvp641wQ_R6L8q39I'; // klucz publiczny; dane chroni RLS w bazie
const LIB = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.2/dist/umd/supabase.js';
const LIB_SRI = 'sha384-Rj26LVGvoeRVR6+mwQmFfcR3QOBEwT+ZmuCWpuiqeTzJpCs0ER4ITAWGb4Hiy3Ok';
const MODULY = 6;
const NICK_RE = /^[A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ-]{3,14}$/;
// to samo co public.nick_email w bazie: zapis szesnastkowy nicku małymi literami (UTF-8)
const nickEmail = nick => 'g' + [...new TextEncoder().encode(nick.toLowerCase())].map(b => b.toString(16).padStart(2, '0')).join('') + '@misja-orion.invalid';

// ---------- localStorage ----------
const LS = {
  get(k) { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch { return null; } },
  set(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v)); } catch {} },
  // dane gry (orion-*); kolejka ma własny prefiks orionq-, żeby nie znikała razem z nimi
  gameKeys() { try { return Object.keys(localStorage).filter(k => k.startsWith('orion-')); } catch { return []; } },
  dump() { const o = {}; this.gameKeys().sort().forEach(k => { o[k] = localStorage.getItem(k); }); return JSON.stringify(o); },
  clearGame() { this.gameKeys().forEach(k => this.set(k, null)); },
};

// gracz zapamiętany lokalnie: zmiany trafiają do kolejki od razu, zanim biblioteka Supabase się wczyta
let user = LS.get('orion-konto');   // { id, nick } albo null
let sb = null, libOk = null, sessionOk = false;

// ---------- kolejka zmian do wysłania ----------
const qKey = () => 'orionq-' + user.id;
const queue = () => (user && LS.get(qKey())) || [];
let seq = 0;
function enqueue(op) {
  if (!user) return;
  op.n = Date.now() + '-' + (seq++);
  // nowszy zapis gry danego modułu i nowszy bohater zastępują starsze, jeszcze niewysłane
  const q = queue().filter(o => !((op.t === 'zapis' || op.t === 'bohater') && o.t === op.t && o.modul === op.modul));
  q.push(op); LS.set(qKey(), q);
  schedule(); renderUI();
}
let timer = 0, flushing = null;
function schedule(ms = 700) { clearTimeout(timer); timer = setTimeout(flush, ms); }
function send(op) {
  switch (op.t) {
    case 'wynik': return sb.from('wyniki').insert({ modul: op.modul, gwiazdki: op.gwiazdki, xp: op.xp, raport: op.raport || {} });
    case 'pojecia': return sb.from('pojecia').upsert(Object.entries(op.rows).map(([pojecie, r]) =>
      ({ gracz_id: user.id, pojecie, status: r.status, temat: r.temat })), { onConflict: 'gracz_id,pojecie' });
    case 'bohater': return sb.from('gracze').update({ bohater: op.id || null, bohater_imie: op.name || null }).eq('id', user.id);
    case 'zapis': return op.stan
      ? sb.from('zapisy').upsert({ gracz_id: user.id, modul: op.modul, etap: op.stan.etap, stan: op.stan }, { onConflict: 'gracz_id,modul' })
      : sb.from('zapisy').delete().eq('modul', op.modul);
  }
  return Promise.resolve({ error: null });
}
// brak sieci, wygasła sesja albo awaria serwera: zostawiamy w kolejce. Inne błędy (np. zła wartość) pomijamy, żeby kolejka nie stanęła.
const retryLater = r => !r || r.status === 0 || r.status === 401 || r.status === 408 || r.status === 429 || r.status >= 500;
function flush() {
  if (!sb || !user || !sessionOk) return Promise.resolve();
  if (flushing) return flushing;
  flushing = (async () => {
    for (let q = queue(); q.length; q = queue()) {
      const op = q[0];
      let r; try { r = await send(op); } catch { r = null; }
      if (r && r.error && retryLater(r)) { schedule(15000); break; }
      if (!r) { schedule(15000); break; }
      if (r.error) console.warn('Konto: pominięto zmianę', op.t, r.error.message);
      LS.set(qKey(), queue().filter(o => o.n !== op.n));
    }
  })().finally(() => { flushing = null; renderUI(); });
  return flushing;
}
addEventListener('online', () => schedule(0));

// ---------- dane konta → localStorage ----------
async function pull() {
  const [g, w, p, z] = await Promise.all([
    sb.from('gracze').select('nick, bohater, bohater_imie').maybeSingle(),
    sb.from('najlepsze_wyniki').select('modul, gwiazdki, xp, ukonczono'),
    sb.from('pojecia').select('pojecie, status, temat, zmieniono'),
    sb.from('zapisy').select('modul, stan'),
  ]);
  for (const r of [g, w, p, z]) if (r.error) throw r.error;
  if (queue().length) return false; // w międzyczasie coś zagrano: lokalne dane są nowsze
  const before = LS.dump();
  if (g.data && g.data.bohater) LS.set('orion-bohater', { id: g.data.bohater, name: g.data.bohater_imie || '' });
  for (let m = 1; m <= MODULY; m++) {
    const b = w.data.find(r => r.modul === m), s = z.data.find(r => r.modul === m);
    LS.set('orion-m' + m, b ? { stars: b.gwiazdki, xp: b.xp, date: b.ukonczono.slice(0, 10) } : null);
    LS.set('orion-zapis-m' + m, s ? s.stan : null);
  }
  LS.set('orion-pojecia', p.data.length ? Object.fromEntries(p.data.map(r => [r.pojecie, { status: r.status, date: r.zmieniono.slice(0, 10), temat: r.temat }])) : null);
  return LS.dump() !== before;
}
const onStartScreen = () => { const s = document.getElementById('scr-start'); return !!s && !s.hidden; };

// ---------- start: biblioteka, sesja, wysłanie kolejki, pobranie danych ----------
const ready = new Promise(ok => {
  const s = document.createElement('script');
  s.src = LIB; s.integrity = LIB_SRI; s.crossOrigin = 'anonymous';
  s.onload = () => ok(true); s.onerror = () => ok(false);
  document.head.append(s);
}).then(async loaded => {
  libOk = loaded && !!(window.supabase && window.supabase.createClient);
  if (!libOk) return;
  sb = window.supabase.createClient(URL, KEY);
  const { data } = await sb.auth.getSession();
  const u = data.session && data.session.user;
  if (!u) return; // sesja wygasła: dane zostają lokalnie, kolejka czeka na ponowne logowanie
  sessionOk = true;
  setUser({ id: u.id, nick: (u.user_metadata && u.user_metadata.nick) || (user && user.nick) || '', tworca: !!(user && user.tworca) });
  await checkTworca();
  await flush();
  // dane z innego komputera: odśwież ekran startowy, jeśli gracz jeszcze nie zaczął grać
  if (!queue().length && await pull() && onStartScreen()) location.reload();
}).catch(e => console.warn('Konto:', e && e.message || e)).finally(() => renderUI());

function setUser(u) { user = u; LS.set('orion-konto', u); }
// twórca gry (gracze.tworca, ustawiane tylko migracją): panel testowy z tworca.js, wyniki i postęp się nie zapisują.
// Znacznik jest też w orion-konto, żeby panel był od razu po wczytaniu strony; serwer go potwierdza albo zdejmuje.
async function checkTworca() {
  const r = await sb.from('gracze').select('tworca').maybeSingle();
  if (r.error) return;
  const t = !!(r.data && r.data.tworca);
  if (t !== !!user.tworca) setUser({ ...user, tworca: t });
  dispatchEvent(new CustomEvent('orion-tworca'));
}

// ---------- logowanie, rejestracja, wylogowanie ----------
const MSG = {
  invalid_credentials: 'Zły nick albo hasło.',
  user_already_exists: 'Ten nick jest już zajęty. Wybierz inny albo się zaloguj.',
  email_exists: 'Ten nick jest już zajęty. Wybierz inny albo się zaloguj.',
  weak_password: 'To hasło jest za słabe. Wymyśl dłuższe.',
  over_request_rate_limit: 'Za dużo prób. Odczekaj chwilę.',
  signup_disabled: 'Zakładanie kont jest wyłączone.',
};
function errText(e) {
  if (!e) return 'Coś poszło nie tak. Spróbuj jeszcze raz.';
  if (MSG[e.code]) return MSG[e.code];
  if (!navigator.onLine || e.status === 0 || /fetch|network/i.test(e.message || '')) return 'Brak połączenia z internetem. Spróbuj za chwilę.';
  return 'Coś poszło nie tak. Spróbuj jeszcze raz.';
}
function check(nick, pass) {
  if (!NICK_RE.test(nick)) return 'Nick: 3–14 znaków. Litery, cyfry, _ albo -.';
  if (pass.length < 6) return 'Hasło musi mieć co najmniej 6 znaków.';
  return '';
}
async function login(nick, pass) {
  const { data, error } = await sb.auth.signInWithPassword({ email: nickEmail(nick), password: pass });
  if (error) return errText(error);
  // zalogowany widzi dane konta, a nie gościa
  LS.clearGame(); sessionOk = true;
  setUser({ id: data.user.id, nick: (data.user.user_metadata && data.user.user_metadata.nick) || nick });
  try { await checkTworca(); await flush(); await pull(); } catch {}
  location.reload();
}
async function register(nick, pass) {
  const { data, error } = await sb.auth.signUp({ email: nickEmail(nick), password: pass, options: { data: { nick } } });
  if (error) return errText(error);
  if (!data.session) return 'Konto czeka na potwierdzenie e-mailem. W Supabase trzeba wyłączyć „Confirm email”.';
  // na nowe konto przechodzi tylko gra gościa; dane innego konta (sesja wygasła) zostają przy nim
  if (user) LS.clearGame();
  sessionOk = true; setUser({ id: data.user.id, nick });
  const h = LS.get('orion-bohater');
  if (h && h.id) enqueue({ t: 'bohater', id: h.id, name: h.name });
  for (let m = 1; m <= MODULY; m++) {
    const b = LS.get('orion-m' + m), s = LS.get('orion-zapis-m' + m);
    if (b) enqueue({ t: 'wynik', modul: m, gwiazdki: b.stars, xp: b.xp, raport: { gosc: true, data: b.date } });
    if (s) enqueue({ t: 'zapis', modul: m, stan: s });
  }
  const p = LS.get('orion-pojecia');
  if (p && Object.keys(p).length) enqueue({ t: 'pojecia', rows: p });
  await flush();
  location.reload();
}
async function logout() {
  try { await flush(); } catch {}
  if (sb) await sb.auth.signOut().catch(() => {});
  if (user) LS.set(qKey(), null);
  LS.clearGame(); user = null;
  location.reload();
}

// ---------- panel konta ----------
const css = document.createElement('style');
css.textContent = `
#konto { display: grid; }
#konto .panel { max-width: 640px; }
#konto form { display: grid; gap: 12px; }
#konto .fields { display: flex; flex-wrap: wrap; gap: 12px; }
#konto .name-row { flex: 1 1 200px; max-width: none; text-shadow: none; }
#konto .err { color: var(--wrong); font-weight: 700; min-height: 1.5em; margin: 0; }
#konto .err:empty { display: none; }
#kontoBtn.on { box-shadow: inset 0 0 0 2px var(--good); }
#discordBtn { display: inline-flex; align-items: center; gap: 8px; text-decoration: none; color: inherit; background: #5865f2; box-shadow: none; }
#discordBtn svg { width: 20px; height: 15px; fill: currentColor; }`;
document.head.append(css);

const btn = document.createElement('button');
btn.className = 'glos-btn'; btn.id = 'kontoBtn'; btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-controls', 'konto');
const glosBtn = document.getElementById('glosBtn');
if (glosBtn) glosBtn.before(btn);

// ---------- serwer Discord z botem Orion ----------
// stałe zaproszenie (nigdy nie wygasa); puste = przycisku nie ma
const DISCORD = 'https://discord.gg/BZKFxs8ZN';
if (DISCORD && glosBtn) {
  const dc = document.createElement('a');
  dc.className = 'glos-btn'; dc.id = 'discordBtn'; dc.href = DISCORD; dc.target = '_blank'; dc.rel = 'noopener';
  dc.title = 'Zapytaj Oriona o fizykę na Discordzie';
  dc.innerHTML = '<svg viewBox="0 0 127.14 96.36" aria-hidden="true"><path d="M107.7 8.07A105.15 105.15 0 0 0 81.47 0a72.06 72.06 0 0 0-3.36 6.83 97.68 97.68 0 0 0-29.11 0A72.37 72.37 0 0 0 45.64 0a105.89 105.89 0 0 0-26.25 8.09C2.79 32.65-1.71 56.6.54 80.21a105.73 105.73 0 0 0 32.17 16.15 77.7 77.7 0 0 0 6.89-11.11 68.42 68.42 0 0 1-10.85-5.18c.91-.66 1.8-1.34 2.66-2a75.57 75.57 0 0 0 64.32 0c.87.71 1.76 1.39 2.66 2a68.68 68.68 0 0 1-10.87 5.19 77 77 0 0 0 6.89 11.1 105.25 105.25 0 0 0 32.19-16.14c2.64-27.38-4.51-51.11-18.9-72.15ZM42.45 65.69C36.18 65.69 31 60 31 53s5-12.74 11.44-12.74S54 46 53.89 53s-5.05 12.69-11.44 12.69Zm42.24 0C78.41 65.69 73.25 60 73.25 53s5-12.74 11.44-12.74S96.23 46 96.12 53s-5.04 12.69-11.43 12.69Z"/></svg>Discord';
  glosBtn.before(dc);
}
const box = document.createElement('section');
box.id = 'konto'; box.hidden = true;
// panel konta stoi nad ekranami gry (Słowniczek jest osobnym oknem, więc nie on wyznacza miejsce)
const main = document.querySelector('main');
if (main) main.before(box);
const toggle = open => { box.hidden = !open; btn.setAttribute('aria-expanded', open); if (open) { renderUI(true); box.scrollIntoView({ behavior: 'smooth', block: 'start' }); } };
btn.addEventListener('click', () => toggle(box.hidden));

let drawn = ''; // stan, dla którego panel jest narysowany; formularz rysujemy od nowa tylko po zmianie stanu
function renderUI(force) {
  const inside = !!(sessionOk && user);
  btn.textContent = inside ? 'Konto: ' + user.nick : user ? 'Zaloguj się ponownie' : 'Zaloguj się';
  btn.classList.toggle('on', inside);
  if (box.hidden) return;
  const pending = queue().length;
  const syncText = pending ? 'Czekam na internet. Zmiany zapiszą się później.' : 'Wszystko zapisane.';
  const state = inside ? 'in:' + user.nick : 'out:' + libOk + ':' + (user ? user.nick : '');
  if (!force && state === drawn) { const s = box.querySelector('[data-sync]'); if (s) s.textContent = syncText; return; }
  drawn = state;
  if (inside) {
    box.innerHTML = `<div class="panel"><h2></h2>
      <p>${user.tworca ? 'Konto twórcy: panel „Twórca” w lewym dolnym rogu. Wyniki, pojęcia i przerwana gra się nie zapisują.' : 'Wyniki, pojęcia i przerwana gra zapisują się na koncie. Zagrasz dalej na każdym komputerze.'}</p>
      <p class="src" data-sync></p>
      <div class="actions"><button class="btn ghost" data-out>Wyloguj</button><button class="btn ghost" data-close>Zamknij</button></div></div>`;
    box.querySelector('h2').textContent = 'Grasz jako ' + user.nick;
    box.querySelector('[data-sync]').textContent = syncText;
    box.querySelector('[data-out]').addEventListener('click', logout);
  } else {
    const off = libOk === false;
    box.innerHTML = `<div class="panel"><h2>Konto gracza</h2>
      <p>${off ? 'Brak połączenia z serwerem. Grasz jako gość. Wyniki zapisują się na tym komputerze.' : 'Zaloguj się, a wyniki i postęp zapiszą się na koncie. Wtedy zagrasz dalej na każdym komputerze.'}</p>
      <form novalidate>
        <div class="fields">
          <label class="name-row">Nick <input name="nick" maxlength="14" autocomplete="username" spellcheck="false" autocapitalize="off"></label>
          <label class="name-row">Hasło <input name="haslo" type="password" autocomplete="current-password"></label>
        </div>
        <p class="err" role="alert"></p>
        <div class="actions">
          <button class="btn" type="submit" value="login">Zaloguj</button>
          <button class="btn ghost" type="submit" value="nowe">Załóż konto</button>
          <button class="btn ghost" type="button" data-close>Zamknij</button>
        </div>
        <p class="src">Zakładasz konto? Obecne wyniki przejdą na nie. Nick: 3–14 znaków. Hasło: co najmniej 6 znaków. Nie wpisuj nazwiska.</p>
      </form></div>`;
    const f = box.querySelector('form'), err = f.querySelector('.err');
    if (user) f.nick.value = user.nick;
    f.querySelectorAll('input, button[type=submit]').forEach(el => { el.disabled = off; });
    if (libOk === null) err.textContent = 'Łączę z serwerem…';
    f.addEventListener('submit', async e => {
      e.preventDefault();
      if (!sb) { err.textContent = 'Łączę z serwerem… Spróbuj za chwilę.'; return; }
      const nick = f.nick.value.trim(), pass = f.haslo.value;
      const bad = check(nick, pass); if (bad) { err.textContent = bad; return; }
      const nowe = e.submitter && e.submitter.value === 'nowe';
      f.querySelectorAll('button').forEach(b => { b.disabled = true; });
      err.textContent = nowe ? 'Zakładam konto…' : 'Loguję…';
      const msg = await (nowe ? register(nick, pass) : login(nick, pass));
      if (msg) { err.textContent = msg; f.querySelectorAll('button').forEach(b => { b.disabled = false; }); }
    });
  }
  box.querySelector('[data-close]').addEventListener('click', () => toggle(false));
}
renderUI();

// ---------- dla gry ----------
window.Konto = {
  ready,
  get nick() { return sessionOk && user ? user.nick : null; },
  // gracz zapamiętany na tym komputerze (od razu po wczytaniu strony, zanim serwer potwierdzi sesję)
  get gracz() { return user ? user.nick : null; },
  get tworca() { return !!(user && user.tworca); },
  bohater(h) { enqueue({ t: 'bohater', id: h.id, name: h.name }); },
  // cała lokalna mapa pojęć (orion-pojecia), już zapisana przez grę
  pojecia() { if (this.tworca) return; const p = LS.get('orion-pojecia'); if (p && Object.keys(p).length) enqueue({ t: 'pojecia', rows: p }); },
  // ukończony moduł: wynik do historii; przerwana gra tego modułu znika (w bazie robi to trigger)
  wynik(modul, gwiazdki, xp, raport) { if (this.tworca) return; LS.set('orion-zapis-m' + modul, null); enqueue({ t: 'wynik', modul, gwiazdki, xp, raport }); },
  // przerwana gra: migawka { etap, S, … } do wznowienia
  zapisz(modul, stan) { if (this.tworca) return; LS.set('orion-zapis-m' + modul, stan); enqueue({ t: 'zapis', modul, stan }); },
  wczytaj(modul) { return LS.get('orion-zapis-m' + modul); },
  nickEmail,
};
})();
