(define (problem transport_intermodal_system)
  (:domain transport_system)

  (:objects
    poznan_magazyn rzeszow_magazyn - warehouse
    gdansk_port szczecin_port - port
    warszawa_lotnisko katowice_lotnisko - airport
    wroclaw_stacja krakow_stacja szczecin_stacja - station

    tir_poznan tir_warszawa tir_szczecin - truck
    pociag_towarowy - train
    kontenerowiec_baltyk - ship
    maly_samolot - plane

    paczka_medyczna elektronika czesci_samochodowe turbina_wiatrowa - package
  )

  (:init
    (vehicle-empty tir_poznan)
    (vehicle-empty tir_warszawa)
    (vehicle-empty tir_szczecin)
    (vehicle-empty pociag_towarowy)
    (vehicle-empty kontenerowiec_baltyk)
    (vehicle-empty maly_samolot)

    (compatible paczka_medyczna tir_poznan)
    (compatible paczka_medyczna tir_warszawa)
    (compatible paczka_medyczna tir_szczecin)
    (compatible paczka_medyczna pociag_towarowy)
    (compatible paczka_medyczna kontenerowiec_baltyk)
    (compatible paczka_medyczna maly_samolot)

    (compatible elektronika tir_poznan)
    (compatible elektronika tir_warszawa)
    (compatible elektronika tir_szczecin)
    (compatible elektronika pociag_towarowy)
    (compatible elektronika kontenerowiec_baltyk)
    (compatible elektronika maly_samolot)

    (compatible czesci_samochodowe tir_poznan)
    (compatible czesci_samochodowe tir_warszawa)
    (compatible czesci_samochodowe tir_szczecin)
    (compatible czesci_samochodowe pociag_towarowy)
    (compatible czesci_samochodowe kontenerowiec_baltyk)

    (compatible turbina_wiatrowa tir_szczecin)
    (compatible turbina_wiatrowa pociag_towarowy)
    (compatible turbina_wiatrowa kontenerowiec_baltyk)

    (vehicle-at tir_poznan poznan_magazyn)
    (vehicle-at tir_warszawa warszawa_lotnisko)
    (vehicle-at tir_szczecin szczecin_port)
    (vehicle-at pociag_towarowy wroclaw_stacja)
    (vehicle-at kontenerowiec_baltyk gdansk_port)
    (vehicle-at maly_samolot katowice_lotnisko)

    (package-at paczka_medyczna rzeszow_magazyn)
    (package-at elektronika poznan_magazyn)
    (package-at czesci_samochodowe wroclaw_stacja)
    (package-at turbina_wiatrowa gdansk_port)

    (road-connection poznan_magazyn warszawa_lotnisko)
    (road-connection warszawa_lotnisko poznan_magazyn)
    (road-connection poznan_magazyn wroclaw_stacja)
    (road-connection wroclaw_stacja poznan_magazyn)
    (road-connection warszawa_lotnisko wroclaw_stacja)
    (road-connection wroclaw_stacja warszawa_lotnisko)
    (road-connection warszawa_lotnisko rzeszow_magazyn)
    (road-connection rzeszow_magazyn warszawa_lotnisko)
    (road-connection warszawa_lotnisko gdansk_port)
    (road-connection gdansk_port warszawa_lotnisko)
    (road-connection katowice_lotnisko warszawa_lotnisko)
    (road-connection warszawa_lotnisko katowice_lotnisko)
    (road-connection szczecin_port szczecin_stacja)
    (road-connection szczecin_stacja szczecin_port)
    (road-connection gdansk_port wroclaw_stacja)
    (road-connection wroclaw_stacja gdansk_port)

    (rail-connection wroclaw_stacja krakow_stacja)
    (rail-connection krakow_stacja wroclaw_stacja)
    (rail-connection wroclaw_stacja szczecin_stacja)
    (rail-connection szczecin_stacja wroclaw_stacja)
    (rail-connection szczecin_stacja krakow_stacja)
    (rail-connection krakow_stacja szczecin_stacja)

    (sea-connection gdansk_port szczecin_port)
    (sea-connection szczecin_port gdansk_port)

    (flight-connection katowice_lotnisko warszawa_lotnisko)
    (flight-connection warszawa_lotnisko katowice_lotnisko)
  )

  (:goal (and
    (package-at paczka_medyczna poznan_magazyn)
    (package-at elektronika rzeszow_magazyn)
    (package-at czesci_samochodowe rzeszow_magazyn)
    (package-at turbina_wiatrowa krakow_stacja)
  ))
)
