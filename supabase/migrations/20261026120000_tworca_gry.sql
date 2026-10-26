-- konto twórcy gry: panel do skakania po ekranach, wyniki testowe nie są zapisywane (logika w gra/tworca.js i gra/konto.js)
-- Gracz nie może sam ustawić znacznika: na gracze ma update tylko (bohater, bohater_imie).
alter table public.gracze add column tworca boolean not null default false;
comment on column public.gracze.tworca is 'Twórca gry: widzi panel testowy. Gracz nie może tego zmienić (update tylko bohater, bohater_imie); ustawiane migracją.';
update public.gracze set tworca = true where lower(nick) = 'merlin';
