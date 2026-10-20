-- Misja Orion: konta graczy (nick + hasło), wyniki modułów, pojęcia do powtórki i zapis gry do wznowienia.
-- Logowanie idzie przez Supabase Auth z technicznym e-mailem zrobionym z nicku (public.nick_email).
-- Gracz go nie widzi. W panelu Supabase musi być wyłączone „Confirm email”.

-- ---------- nick → techniczny e-mail ----------
-- Nick: 3–14 znaków, litery (także polskie), cyfry, _ i -. Wielkość liter bez znaczenia: „Ola” i „ola” to ten sam gracz.
-- Część przed @ musi być ASCII, więc to zapis szesnastkowy nicku małymi literami (UTF-8).
-- Klient liczy to samo:
--   'g' + [...new TextEncoder().encode(nick.toLowerCase())].map(b => b.toString(16).padStart(2, '0')).join('') + '@misja-orion.invalid'
create function public.nick_poprawny(nick text) returns boolean
language sql immutable set search_path = ''
as $$ select coalesce(nick ~ '^[A-Za-z0-9_ąćęłńóśźżĄĆĘŁŃÓŚŹŻ-]{3,14}$', false) $$;

create function public.nick_email(nick text) returns text
language sql immutable set search_path = ''
as $$ select 'g' || encode(convert_to(lower(nick), 'UTF8'), 'hex') || '@misja-orion.invalid' $$;

-- ---------- tabele ----------
create table public.gracze (
  id uuid primary key references auth.users (id) on delete cascade,
  nick text not null check (public.nick_poprawny(nick)),
  bohater text check (bohater in ('astronautka', 'astronauta', 'robot', 'kot')),
  bohater_imie text check (char_length(bohater_imie) <= 14),
  utworzono timestamptz not null default now(),
  zmieniono timestamptz not null default now()
);
create unique index gracze_nick_unikalny on public.gracze (lower(nick));
comment on table public.gracze is 'Profil gracza: nick do logowania i wybrany bohater (dawniej localStorage orion-bohater). Wiersz zakłada trigger przy rejestracji.';

-- każde ukończenie modułu (ekran Raport); najlepszy wynik daje widok najlepsze_wyniki
create table public.wyniki (
  id bigint generated always as identity primary key,
  gracz_id uuid not null default auth.uid() references public.gracze (id) on delete cascade,
  modul smallint not null check (modul between 1 and 6),
  gwiazdki smallint not null check (gwiazdki between 0 and 3),
  xp integer not null check (xp between 0 and 100000),
  raport jsonb not null default '{}' check (jsonb_typeof(raport) = 'object' and pg_column_size(raport) <= 16384),
  ukonczono timestamptz not null default now()
);
create index wyniki_gracz_modul on public.wyniki (gracz_id, modul);
comment on table public.wyniki is 'Historia ukończonych modułów (dawniej localStorage orion-mN). Tylko dopisywanie, bez poprawiania.';

-- stan pojęć: ok = od razu, retry = po powtórce, weak = do powtórki w kolejnym module
create table public.pojecia (
  gracz_id uuid not null default auth.uid() references public.gracze (id) on delete cascade,
  pojecie text not null check (char_length(pojecie) between 1 and 40),
  status text not null check (status in ('ok', 'retry', 'weak')),
  temat smallint not null check (temat between 1 and 99),
  zmieniono timestamptz not null default now(),
  primary key (gracz_id, pojecie)
);
comment on table public.pojecia is 'Pojęcia gracza i ich stan (dawniej localStorage orion-pojecia).';

-- przerwana gra: jeden zapis na moduł; „stan” to migawka gry (XP, gwiazdki, odpowiedzi, miejsce w etapie)
create table public.zapisy (
  gracz_id uuid not null default auth.uid() references public.gracze (id) on delete cascade,
  modul smallint not null check (modul between 1 and 6),
  etap text not null check (etap in ('lab', 'cards', 's1', 's2', 's3')),
  stan jsonb not null check (jsonb_typeof(stan) = 'object' and pg_column_size(stan) <= 65536),
  zmieniono timestamptz not null default now(),
  primary key (gracz_id, modul)
);
comment on table public.zapisy is 'Zapis przerwanej gry do wznowienia. Znika sam, gdy gracz ukończy moduł (trigger na wyniki).';

-- najlepszy wynik w module: najwięcej gwiazdek, potem XP; przy remisie zostaje wcześniejszy (jak w localStorage)
create view public.najlepsze_wyniki with (security_invoker = true) as
select distinct on (w.gracz_id, w.modul)
  w.gracz_id, w.modul, w.gwiazdki, w.xp, w.ukonczono,
  count(*) over (partition by w.gracz_id, w.modul) as gry,
  max(w.ukonczono) over (partition by w.gracz_id, w.modul) as ostatnio
from public.wyniki w
order by w.gracz_id, w.modul, w.gwiazdki desc, w.xp desc, w.ukonczono;

-- ---------- triggery ----------
create function public.ustaw_zmieniono() returns trigger
language plpgsql set search_path = ''
as $$ begin new.zmieniono := now(); return new; end $$;
create trigger gracze_zmieniono before update on public.gracze for each row execute function public.ustaw_zmieniono();
create trigger pojecia_zmieniono before update on public.pojecia for each row execute function public.ustaw_zmieniono();
create trigger zapisy_zmieniono before update on public.zapisy for each row execute function public.ustaw_zmieniono();

-- ukończony moduł nie ma już czego wznawiać
create function public.wynik_konczy_zapis() returns trigger
language plpgsql set search_path = ''
as $$ begin delete from public.zapisy where gracz_id = new.gracz_id and modul = new.modul; return new; end $$;
create trigger wyniki_konczy_zapis after insert on public.wyniki for each row execute function public.wynik_konczy_zapis();

-- rejestracja: signUp({ email: nick_email(nick), password, options: { data: { nick } } }) zakłada profil gracza.
-- Konto z innym e-mailem albo bez poprawnego nicku jest odrzucane.
create function public.nowy_gracz() returns trigger
language plpgsql security definer set search_path = ''
as $$
declare n text := new.raw_user_meta_data ->> 'nick';
begin
  if not public.nick_poprawny(n) then
    raise exception 'Nick musi mieć 3–14 znaków: litery, cyfry, _ albo -.' using errcode = 'check_violation';
  end if;
  if new.email is distinct from public.nick_email(n) then
    raise exception 'Konto zakłada się nickiem i hasłem.' using errcode = 'check_violation';
  end if;
  insert into public.gracze (id, nick) values (new.id, n);
  return new;
end $$;
revoke all on function public.nowy_gracz() from public, anon, authenticated;
create trigger nowy_gracz after insert on auth.users for each row execute function public.nowy_gracz();

-- ---------- dostęp: każdy gracz widzi i zmienia tylko swoje dane ----------
alter table public.gracze enable row level security;
alter table public.wyniki enable row level security;
alter table public.pojecia enable row level security;
alter table public.zapisy enable row level security;

revoke all on public.gracze, public.wyniki, public.pojecia, public.zapisy, public.najlepsze_wyniki from anon, authenticated;

-- nicku nie da się zmienić (z niego jest e-mail do logowania), bohatera tak
grant select on public.gracze to authenticated;
grant update (bohater, bohater_imie) on public.gracze to authenticated;
create policy "gracz widzi swój profil" on public.gracze for select to authenticated
  using (id = (select auth.uid()));
create policy "gracz zmienia swojego bohatera" on public.gracze for update to authenticated
  using (id = (select auth.uid())) with check (id = (select auth.uid()));

-- wyniki: tylko odczyt i dopisanie nowego; gracz_id i data ustawiają się same
grant select on public.wyniki to authenticated;
grant insert (modul, gwiazdki, xp, raport) on public.wyniki to authenticated;
create policy "gracz widzi swoje wyniki" on public.wyniki for select to authenticated
  using (gracz_id = (select auth.uid()));
create policy "gracz dopisuje swój wynik" on public.wyniki for insert to authenticated
  with check (gracz_id = (select auth.uid()));

grant select on public.najlepsze_wyniki to authenticated;

-- pojęcia i zapisy: pełny dostęp do własnych wierszy (upsert, usuwanie)
grant select, insert, update, delete on public.pojecia, public.zapisy to authenticated;
create policy "gracz zarządza swoimi pojęciami" on public.pojecia for all to authenticated
  using (gracz_id = (select auth.uid())) with check (gracz_id = (select auth.uid()));
create policy "gracz zarządza swoimi zapisami" on public.zapisy for all to authenticated
  using (gracz_id = (select auth.uid())) with check (gracz_id = (select auth.uid()));
