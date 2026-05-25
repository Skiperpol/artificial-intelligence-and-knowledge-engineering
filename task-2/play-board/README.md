# Plansza HTML — gra z botem turniejowym

Interaktywna plansza 8×8: przeciągasz własne piony (lub klik → pole docelowe). Po Twoim ruchu odpowiada ten sam silnik co w turnieju (`choose_tournament_move` + `best_genome_selfplay.json`).

## Uruchomienie

```bash
cd /home/dawid/Pulpit/artificial-intelligence-and-knowledge-engineering/task-2/play-board
python3 server.py
```

W przeglądarce: **http://127.0.0.1:8765/**

Zatrzymanie: `Ctrl+C`.

## Sterowanie

- **B** — czarne, zaczynasz (górne 2 rzędy, cel: dół).
- **W** — białe (dolne 2 rzędy, cel: góra).
- Zielone pole = dozwolony ruch; przeciągnij pion lub kliknij pion, potem pole.
- **Nowa gra** — reset z wybranym kolorem.

Wymaga działającego `../src/` (ten sam kod co `human_main.py --tournament-mode`).
