(define (problem transport-chicago-ny)
  (:domain transport-system)
  (:objects
    warszawa-hub - airport
    warszawa-station - station
    gdansk-port - port
    gdansk-station - station
    ny-airport - airport
    ny-port - port
    truck1 truck2 - truck
    ship1 - ship
    plane1 - plane
    train1 - train
    p1 p2 - package
  )

  (:init
    (port-location gdansk-port)
    (port-location ny-port)

    (road-connection warszawa-hub gdansk-port)
    (road-connection gdansk-port warszawa-hub)
    (road-connection ny-airport ny-port)
    (road-connection ny-port ny-airport)
    (road-connection warszawa-hub warszawa-station)
    (road-connection warszawa-station warszawa-hub)
    (road-connection gdansk-port gdansk-station)
    (road-connection gdansk-station gdansk-port)

    (water-connection gdansk-port ny-port)
    (water-connection ny-port gdansk-port)

    (flight-connection warszawa-hub ny-airport)
    (flight-connection ny-airport warszawa-hub)

    (rail-connection warszawa-station gdansk-station)
    (rail-connection gdansk-station warszawa-station)

    (at truck1 warszawa-hub)
    (at truck2 ny-airport)
    (at ship1 gdansk-port)
    (at plane1 warszawa-hub)
    (at train1 warszawa-station)

    (at p1 warszawa-hub)
    (at p2 warszawa-hub)

    (= (total-cost) 0)

    (= (road-cost warszawa-hub gdansk-port) 15)
    (= (road-time warszawa-hub gdansk-port) 10)
    (= (road-cost gdansk-port warszawa-hub) 15)
    (= (road-time gdansk-port warszawa-hub) 10)
    (= (road-cost ny-airport ny-port) 5)
    (= (road-time ny-airport ny-port) 3)
    (= (road-cost ny-port ny-airport) 5)
    (= (road-time ny-port ny-airport) 3)
    (= (road-cost warszawa-hub warszawa-station) 2)
    (= (road-time warszawa-hub warszawa-station) 1)
    (= (road-cost warszawa-station warszawa-hub) 2)
    (= (road-time warszawa-station warszawa-hub) 1)
    (= (road-cost gdansk-port gdansk-station) 2)
    (= (road-time gdansk-port gdansk-station) 1)
    (= (road-cost gdansk-station gdansk-port) 2)
    (= (road-time gdansk-station gdansk-port) 1)

    (= (flight-cost warszawa-hub ny-airport) 100)
    (= (flight-time warszawa-hub ny-airport) 4)
    (= (flight-cost ny-airport warszawa-hub) 100)
    (= (flight-time ny-airport warszawa-hub) 4)

    (= (cruise-cost gdansk-port ny-port) 40)
    (= (cruise-time gdansk-port ny-port) 25)
    (= (cruise-cost ny-port gdansk-port) 40)
    (= (cruise-time ny-port gdansk-port) 25)

    (= (travel-cost warszawa-station gdansk-station) 12)
    (= (travel-time warszawa-station gdansk-station) 8)
    (= (travel-cost gdansk-station warszawa-station) 12)
    (= (travel-time gdansk-station warszawa-station) 8)
  )

  (:goal (and
    (at p1 ny-port)
    (at p2 ny-airport)
  ))

  (:metric minimize (total-cost))
)
