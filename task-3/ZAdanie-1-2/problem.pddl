(define (problem transport_intermodal_system)
    (:domain transport_system)

    (:objects
        poznan_magazyn - warehouse
        rzeszow_magazyn - warehouse
        
        gdansk_port - port
        szczecin_port - port
        
        warszawa_lotnisko - airport
        katowice_lotnisko - airport
        
        wroclaw_stacja - station
        krakow_stacja - station
        szczecin_stacja - station

        ;; --- POJAZDY ---
        ;; Zróżnicowana flota z różnymi ograniczeniami pojemności
        tir_poznan tir_warszawa tir_szczecin - truck
        pociag_towarowy - train
        kontenerowiec_baltyk - ship
        awionetka_cargo - plane

        ;; --- PACZKI ---
        ;; Ładunki o różnej specyfice gabarytowej
        paczka_medyczna - package    ;; Mała, pilna
        elektronika - package        ;; Średnia
        czesci_samochodowe - package ;; Duża
        turbina_wiatrowa - package   ;; Gigantyczna (wymaga statku lub pociągu)
    )

    (:init
        ;; 1. Globalne koszty finansowe
        (= (total-cost) 0)

        ;; 2. Specyfikacja gabarytów paczek
        (= (package-size paczka_medyczna) 1)
        (= (package-size elektronika) 5)
        (= (package-size czesci_samochodowe) 15)
        (= (package-size turbina_wiatrowa) 80)

        ;; 3. Pozycje startowe pojazdów i ich limity ładowności
        (at tir_poznan poznan_magazyn)
        (= (space-available tir_poznan) 20)

        (at tir_warszawa warszawa_lotnisko)
        (= (space-available tir_warszawa) 30)

        (at tir_szczecin szczecin_port)
        (= (space-available tir_szczecin) 100)

        (at pociag_towarowy wroclaw_stacja)
        (= (space-available pociag_towarowy) 100)

        (at kontenerowiec_baltyk gdansk_port)
        (= (space-available kontenerowiec_baltyk) 200)

        (at awionetka_cargo katowice_lotnisko)
        (= (space-available awionetka_cargo) 10) ;; Nie zmieści części samochodowych ani turbiny!

        ;; 4. Pozycje startowe paczek (gdzie czekają na odbiór)
        (at paczka_medyczna rzeszow_magazyn)
        (at elektronika poznan_magazyn)
        (at czesci_samochodowe wroclaw_stacja)
        (at turbina_wiatrowa gdansk_port)


        ;; =======================================================
        ;; 5. TOPOLOGIA SIECI (Połączenia, koszty i czasy trwania)
        ;; =======================================================

        ;; --- POŁĄCZENIA DROGOWE (Dla Ciężarówek) ---
        ;; Poznań <-> Warszawa
        (road-connection poznan_magazyn warszawa_lotnisko)
        (road-connection warszawa_lotnisko poznan_magazyn)
        (= (road-cost poznan_magazyn warszawa_lotnisko) 30)
        (= (road-cost warszawa_lotnisko poznan_magazyn) 30)
        (= (road-duration poznan_magazyn warszawa_lotnisko) 120)
        (= (road-duration warszawa_lotnisko poznan_magazyn) 120)

        ;; Poznań <-> Wrocław
        (road-connection poznan_magazyn wroclaw_stacja)
        (road-connection wroclaw_stacja poznan_magazyn)
        (= (road-cost poznan_magazyn wroclaw_stacja) 25)
        (= (road-cost wroclaw_stacja poznan_magazyn) 25)
        (= (road-duration poznan_magazyn wroclaw_stacja) 90)
        (= (road-duration wroclaw_stacja poznan_magazyn) 90)

        ;; Warszawa <-> Rzeszów
        (road-connection warszawa_lotnisko rzeszow_magazyn)
        (road-connection rzeszow_magazyn warszawa_lotnisko)
        (= (road-cost warszawa_lotnisko rzeszow_magazyn) 45)
        (= (road-cost rzeszow_magazyn warszawa_lotnisko) 45)
        (= (road-duration warszawa_lotnisko rzeszow_magazyn) 160)
        (= (road-duration rzeszow_magazyn warszawa_lotnisko) 160)

        ;; Warszawa <-> Gdańsk (lotnisko i port połączone drogą — przesiadka TIR)
        (road-connection warszawa_lotnisko gdansk_port)
        (road-connection gdansk_port warszawa_lotnisko)
        (= (road-cost warszawa_lotnisko gdansk_port) 50)
        (= (road-cost gdansk_port warszawa_lotnisko) 50)
        (= (road-duration warszawa_lotnisko gdansk_port) 180)
        (= (road-duration gdansk_port warszawa_lotnisko) 180)

        ;; Katowice <-> Warszawa (dostęp TIR do lotniska katowickiego)
        (road-connection katowice_lotnisko warszawa_lotnisko)
        (road-connection warszawa_lotnisko katowice_lotnisko)
        (= (road-cost katowice_lotnisko warszawa_lotnisko) 40)
        (= (road-cost warszawa_lotnisko katowice_lotnisko) 40)
        (= (road-duration katowice_lotnisko warszawa_lotnisko) 150)
        (= (road-duration warszawa_lotnisko katowice_lotnisko) 150)

        ;; Port Szczecin <-> stacja Szczecin (krótki odcinek TIR po dopłynięciu statku)
        (road-connection szczecin_port szczecin_stacja)
        (road-connection szczecin_stacja szczecin_port)
        (= (road-cost szczecin_port szczecin_stacja) 5)
        (= (road-cost szczecin_stacja szczecin_port) 5)
        (= (road-duration szczecin_port szczecin_stacja) 15)
        (= (road-duration szczecin_stacja szczecin_port) 15)

        ;; Lotnisko / port / stacja Warszawa — wspólny węzeł drogowy (już wyżej)

        ;; Port Gdańsk <-> stacja Wrocław (hub intermodalny)
        (road-connection gdansk_port wroclaw_stacja)
        (road-connection wroclaw_stacja gdansk_port)
        (= (road-cost gdansk_port wroclaw_stacja) 55)
        (= (road-cost wroclaw_stacja gdansk_port) 55)
        (= (road-duration gdansk_port wroclaw_stacja) 190)
        (= (road-duration wroclaw_stacja gdansk_port) 190)


        ;; --- POŁĄCZENIA KOLEJOWE (Dla Pociągów) ---
        ;; Wrocław <-> Kraków
        (rail-connection wroclaw_stacja krakow_stacja)
        (rail-connection krakow_stacja wroclaw_stacja)
        (= (rail-cost wroclaw_stacja krakow_stacja) 40)
        (= (rail-cost krakow_stacja wroclaw_stacja) 40)
        (= (rail-duration wroclaw_stacja krakow_stacja) 100)
        (= (rail-duration krakow_stacja wroclaw_stacja) 100)

        ;; Wrocław <-> Szczecin (szlak towarowy)
        (rail-connection wroclaw_stacja szczecin_stacja)
        (rail-connection szczecin_stacja wroclaw_stacja)
        (= (rail-cost wroclaw_stacja szczecin_stacja) 70)
        (= (rail-cost szczecin_stacja wroclaw_stacja) 70)
        (= (rail-duration wroclaw_stacja szczecin_stacja) 180)
        (= (rail-duration szczecin_stacja wroclaw_stacja) 180)

        ;; Szczecin <-> Kraków
        (rail-connection szczecin_stacja krakow_stacja)
        (rail-connection krakow_stacja szczecin_stacja)
        (= (rail-cost szczecin_stacja krakow_stacja) 55)
        (= (rail-cost krakow_stacja szczecin_stacja) 55)
        (= (rail-duration szczecin_stacja krakow_stacja) 140)
        (= (rail-duration krakow_stacja szczecin_stacja) 140)

        ;; --- POŁĄCZENIA MORSKIE (Dla Statków) ---
        ;; Gdańsk <-> Szczecin (Korytarz Bałtycki)
        (sea-connection gdansk_port szczecin_port)
        (sea-connection szczecin_port gdansk_port)
        (= (sea-cost gdansk_port szczecin_port) 35)
        (= (sea-cost szczecin_port gdansk_port) 35)
        (= (sea-duration gdansk_port szczecin_port) 240)
        (= (sea-duration szczecin_port gdansk_port) 240)


        ;; --- POŁĄCZENIA LOTNICZE (Dla Samolotów) ---
        ;; Katowice <-> Warszawa
        (flight-connection katowice_lotnisko warszawa_lotnisko)
        (flight-connection warszawa_lotnisko katowice_lotnisko)
        (= (flight-cost katowice_lotnisko warszawa_lotnisko) 150)
        (= (flight-cost warszawa_lotnisko katowice_lotnisko) 150)
        (= (flight-duration katowice_lotnisko warszawa_lotnisko) 35)
        (= (flight-duration warszawa_lotnisko katowice_lotnisko) 35)

        ;; Loty tylko między lotniskami (Rzeszów obsługiwany drogą przez Warszawę)
    )

    ;; =======================================================
    ;; 6. CELE LOGISTYCZNE (Miejsca docelowe dla wszystkich towarów)
    ;; =======================================================
    (:goal (and
        ;; Paczka medyczna z Rzeszowa musi pilnie trafić do Poznania
        (at paczka_medyczna poznan_magazyn)

        ;; Elektronika z Poznania ma trafić do magazynu w Rzeszowie
        (at elektronika rzeszow_magazyn)

        ;; Części samochodowe z Wrocławia muszą lecieć z Warszawy lub jechać do Rzeszowa
        (at czesci_samochodowe rzeszow_magazyn)

        ;; Wielka turbina wiatrowa z Gdańska musi drogą morską i kolejową trafić do Krakowa
        (at turbina_wiatrowa krakow_stacja)
    ))
)