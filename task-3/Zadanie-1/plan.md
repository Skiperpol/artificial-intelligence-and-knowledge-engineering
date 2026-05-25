number of literals: 93
constructing lookup tables: [10%] [20%] [30%] [40%] [50%] [60%] [70%] [80%] [90%] [100%]
post filtering unreachable actions:  [10%] [20%] [30%] [40%] [50%] [60%] [70%] [80%] [90%] [100%]
no semaphore facts found, returning
[01;34mno analytic limits found, not considering limit effects of goal-only operators[00m
all the ground actions in this problem are compression-safe
initial heuristic = 19.000, admissible cost estimate 0.000
b (18.000 | 20.000)b (17.000 | 20.000)b (16.000 | 35.000)b (15.000 | 40.000)b (14.000 | 45.001)b (13.000 | 60.001)b (12.000 | 65.001)b (11.000 | 70.002)b (10.000 | 90.002)b (9.000 | 95.002)b (8.000 | 95.002)b (7.000 | 95.002)b (6.000 | 95.002)b (5.000 | 95.002)b (4.000 | 95.002)b (3.000 | 95.002)b (2.000 | 95.002)b (1.000 | 95.002)(g)
; no metric specified - using makespan

; plan found with metric 95.002
; states evaluated so far: 93
; states pruned based on pre-heuristic cost lower bound: 0
; time 0.14
0.000: (move-train pociag_towarowy wroclaw_stacja szczecin_stacja)  [20.000]
0.000: (load turbina_wiatrowa kontenerowiec_baltyk gdansk_port)  [5.000]
0.000: (drive-truck tir_warszawa warszawa_lotnisko wroclaw_stacja)  [15.000]
0.000: (load elektronika tir_poznan poznan_magazyn)  [5.000]
5.000: (sail-ship kontenerowiec_baltyk gdansk_port szczecin_port)  [30.000]
5.000: (drive-truck tir_poznan poznan_magazyn warszawa_lotnisko)  [15.000]
15.001: (load czesci_samochodowe tir_warszawa wroclaw_stacja)  [5.000]
20.001: (drive-truck tir_poznan warszawa_lotnisko rzeszow_magazyn)  [15.000]
20.001: (drive-truck tir_warszawa wroclaw_stacja warszawa_lotnisko)  [15.000]
35.000: (unload turbina_wiatrowa kontenerowiec_baltyk szczecin_port)  [5.000]
35.001: (unload elektronika tir_poznan rzeszow_magazyn)  [5.000]
35.002: (drive-truck tir_warszawa warszawa_lotnisko rzeszow_magazyn)  [15.000]
40.001: (load turbina_wiatrowa tir_szczecin szczecin_port)  [5.000]
40.002: (load paczka_medyczna tir_poznan rzeszow_magazyn)  [5.000]
45.001: (drive-truck tir_szczecin szczecin_port szczecin_stacja)  [15.000]
45.002: (drive-truck tir_poznan rzeszow_magazyn warszawa_lotnisko)  [15.000]
50.002: (unload czesci_samochodowe tir_warszawa rzeszow_magazyn)  [5.000]
60.001: (unload turbina_wiatrowa tir_szczecin szczecin_stacja)  [5.000]
60.003: (drive-truck tir_poznan warszawa_lotnisko poznan_magazyn)  [15.000]
65.002: (load turbina_wiatrowa pociag_towarowy szczecin_stacja)  [5.000]
70.002: (move-train pociag_towarowy szczecin_stacja krakow_stacja)  [20.000]
75.003: (unload paczka_medyczna tir_poznan poznan_magazyn)  [5.000]
90.002: (unload turbina_wiatrowa pociag_towarowy krakow_stacja)  [5.000]

 * all goal deadlines now no later than 95.002

resorting to best-first search
running wa* with w = 5.000, not restarting with goal states
b (18.000 | 20.000)b (18.000 | 5.000)b (17.000 | 20.000)b (16.000 | 35.000)b (15.000 | 40.000)b (14.000 | 45.001)b (13.000 | 60.001)b (12.000 | 65.001)b (11.000 | 70.002)b (10.000 | 70.002)b (9.000 | 70.002)b (8.000 | 70.002)b (7.000 | 70.002)b (6.000 | 70.002)b (5.000 | 70.002)b (4.000 | 70.002)b (3.000 | 75.002)b (2.000 | 80.002)