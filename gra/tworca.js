// Panel twórcy gry: tylko dla konta ze znacznikiem „twórca” (gracze.tworca w Supabase, zob. konto.js).
// Skoki do dowolnego miejsca modułu, „Wstecz” do poprzedniego miejsca, pomijanie odliczania, podgląd dobrych odpowiedzi.
// Moduł gry wystawia window.orion.dev: { enable(), set(opcje), places() → [{ grp, label, go }], back(), canBack() }.
(() => {
'use strict';
const MODS = [[1, 'dynamika-poziom1.html', 'I zasada dynamiki Newtona'], [2, 'dynamika-poziom2.html', 'II zasada dynamiki Newtona'], [3, 'dynamika-poziom3.html', 'III zasada dynamiki Newtona'], [4, 'dynamika-poziom4.html', 'Swobodne spadanie'], [5, 'dynamika-poziom5.html', 'Opory ruchu']];
const OPT_KEY = 'tworca-opcje'; // bez przedrostka orion-, żeby nie znikało przy logowaniu (LS.clearGame)
let built = false;

function build() {
  const D = window.orion && window.orion.dev;
  if (built || !D || !(window.Konto && window.Konto.tworca)) return;
  built = true;
  let opt = { fast: true, ans: false };
  try { opt = { ...opt, ...JSON.parse(localStorage.getItem(OPT_KEY) || '{}') }; } catch {}
  D.enable(); D.set(opt);

  const css = document.createElement('style');
  css.textContent = `
#tworcaBtn { position: fixed; left: 12px; bottom: 12px; z-index: 6; font-family: var(--f-display); font-weight: 700; font-size: 14px;
  padding: 10px 16px; border: 0; border-radius: 999px; background: var(--good); color: var(--plum); box-shadow: 0 6px 20px rgba(0,0,0,.5); }
#tworca { position: fixed; left: 12px; bottom: 64px; z-index: 6; width: min(420px, calc(100vw - 24px)); max-height: calc(100dvh - 90px);
  overflow-y: auto; overscroll-behavior: contain; display: grid; gap: 12px; padding: 16px 18px; border-radius: 20px;
  background: rgba(20,10,30,.97); box-shadow: inset 0 0 0 2px var(--good), 0 16px 50px rgba(0,0,0,.6); font-size: 15px; }
#tworca h2 { font-size: 20px; }
#tworca .src { margin: 0; }
#tworca .row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
#tworca .row .btn { padding: 8px 16px; font-size: 14px; }
#tworca label { display: flex; gap: 8px; align-items: center; font-weight: 700; cursor: pointer; }
#tworca input { width: 18px; height: 18px; accent-color: var(--good); }
#tworca details { background: rgba(255,255,255,.05); border-radius: 12px; }
#tworca summary { cursor: pointer; padding: 8px 12px; font-weight: 800; color: var(--good); }
#tworca .list { display: grid; gap: 4px; padding: 0 8px 8px; }
#tworca .list button, #tworca .list a { text-align: left; font: inherit; font-size: 14px; font-weight: 700; color: var(--white); text-decoration: none;
  padding: 7px 10px; border: 0; border-radius: 10px; background: rgba(255,255,255,.06); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#tworca .list button:hover, #tworca .list a:hover { background: var(--good); color: var(--plum); }
#tworca .list .here { box-shadow: inset 0 0 0 2px var(--good); }
body.dev-ans .opt[data-ok="1"]::after { content: " ✓"; color: var(--good); font-weight: 900; }
body.dev-ans .opt.good[data-ok="1"]::after { color: var(--plum); }`;
  document.head.append(css);

  const btn = document.createElement('button');
  btn.id = 'tworcaBtn'; btn.textContent = 'Twórca'; btn.setAttribute('aria-expanded', 'false'); btn.setAttribute('aria-controls', 'tworca');
  const box = document.createElement('section');
  box.id = 'tworca'; box.hidden = true; box.setAttribute('aria-label', 'Panel twórcy');
  document.body.append(btn, box);
  const open = on => { box.hidden = !on; btn.setAttribute('aria-expanded', on); if (on) render(); };
  btn.addEventListener('click', () => open(box.hidden));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !box.hidden) open(false); });

  const here = location.pathname.split('/').pop();
  function render() {
    box.innerHTML = `<h2>Tryb twórcy</h2>
      <p class="src">Wyniki, pojęcia i przerwana gra się nie zapisują.</p>
      <div class="row"><button class="btn" data-back>← Wstecz</button><button class="btn ghost" data-close>Zamknij</button></div>
      <div class="row"><label><input type="checkbox" data-o="fast"> Bez odliczania</label><label><input type="checkbox" data-o="ans"> Pokaż dobre odpowiedzi</label></div>`;
    const back = box.querySelector('[data-back]');
    back.disabled = !D.canBack();
    back.addEventListener('click', () => { D.back(); open(false); });
    box.querySelector('[data-close]').addEventListener('click', () => open(false));
    box.querySelectorAll('[data-o]').forEach(c => {
      c.checked = !!opt[c.dataset.o];
      c.addEventListener('change', () => { opt[c.dataset.o] = c.checked; D.set(opt); try { localStorage.setItem(OPT_KEY, JSON.stringify(opt)); } catch {} });
    });
    const group = (title, isOpen) => {
      const d = document.createElement('details'); d.open = isOpen;
      d.innerHTML = '<summary></summary><div class="list"></div>'; d.querySelector('summary').textContent = title;
      box.append(d); return d.querySelector('.list');
    };
    const mods = group('Moduły', false);
    MODS.forEach(([n, file, name]) => {
      const a = document.createElement('a'); a.href = file; a.textContent = `Moduł ${n}: ${name}`;
      if (file === here) a.className = 'here';
      mods.append(a);
    });
    const lists = {};
    D.places().forEach(p => {
      const list = lists[p.grp] || (lists[p.grp] = group(p.grp, p.grp === 'Ekrany'));
      const b = document.createElement('button'); b.textContent = p.label; b.title = p.label;
      b.addEventListener('click', () => { open(false); p.go(); });
      list.append(b);
    });
  }
}
addEventListener('orion-tworca', build);
build();
})();
