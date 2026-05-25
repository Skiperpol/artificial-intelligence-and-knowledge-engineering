(define (domain transport_system)

  (:requirements :strips :typing :negative-preconditions :numeric-fluents :durative-actions)

  (:types
    location physobj - object
    package vehicle - physobj
    warehouse airport port station - location
    truck plane ship train - vehicle
  )

  (:predicates
    (at ?obj - physobj ?l - location)
    (in ?p - package ?v - vehicle)
    ;; Droga: ciężarówki — dowolna lokacja (magazyn, lotnisko, port, stacja)
    (road-connection ?l1 - location ?l2 - location)
    ;; Lot: wyłącznie między lotniskami
    (flight-connection ?l1 - airport ?l2 - airport)
    ;; Kolej: wyłącznie między stacjami
    (rail-connection ?l1 - station ?l2 - station)
    ;; Morze: wyłącznie między portami
    (sea-connection ?l1 - port ?l2 - port)
  )

  (:functions
    (total-cost)
    (road-cost ?l1 - location ?l2 - location)
    (flight-cost ?l1 - airport ?l2 - airport)
    (rail-cost ?l1 - station ?l2 - station)
    (sea-cost ?l1 - port ?l2 - port)
    (road-duration ?l1 - location ?l2 - location)
    (flight-duration ?l1 - airport ?l2 - airport)
    (rail-duration ?l1 - station ?l2 - station)
    (sea-duration ?l1 - port ?l2 - port)
    (package-size ?p - package)
    (space-available ?v - vehicle)
  )

  (:durative-action load
    :parameters (?p - package ?v - vehicle ?l - location)
    :duration (= ?duration (package-size ?p))
    :condition (and
      (at start (at ?p ?l))
      (at start (at ?v ?l))
      (at start (>= (space-available ?v) (package-size ?p)))
      (over all (at ?v ?l))
    )
    :effect (and
      (at start (not (at ?p ?l)))
      (at start (decrease (space-available ?v) (package-size ?p)))
      (at end (in ?p ?v))
      (at end (increase (total-cost) 10))
    )
  )

  (:durative-action unload
    :parameters (?p - package ?v - vehicle ?l - location)
    :duration (= ?duration (package-size ?p))
    :condition (and
      (at start (in ?p ?v))
      (over all (at ?v ?l))
    )
    :effect (and
      (at start (not (in ?p ?v)))
      (at end (at ?p ?l))
      (at end (increase (space-available ?v) (package-size ?p)))
      (at end (increase (total-cost) 10))
    )
  )

  (:durative-action drive-truck
    :parameters (?t - truck ?from - location ?to - location)
    :duration (= ?duration (road-duration ?from ?to))
    :condition (and
      (at start (at ?t ?from))
      (at start (not (at ?t ?to)))
      (over all (road-connection ?from ?to))
    )
    :effect (and
      (at start (not (at ?t ?from)))
      (at end (at ?t ?to))
      (at end (increase (total-cost) (road-cost ?from ?to)))
    )
  )

  (:durative-action fly-plane
    :parameters (?p - plane ?from - airport ?to - airport)
    :duration (= ?duration (flight-duration ?from ?to))
    :condition (and
      (at start (at ?p ?from))
      (at start (not (at ?p ?to)))
      (over all (flight-connection ?from ?to))
    )
    :effect (and
      (at start (not (at ?p ?from)))
      (at end (at ?p ?to))
      (at end (increase (total-cost) (flight-cost ?from ?to)))
    )
  )

  (:durative-action sail-ship
    :parameters (?s - ship ?from - port ?to - port)
    :duration (= ?duration (sea-duration ?from ?to))
    :condition (and
      (at start (at ?s ?from))
      (at start (not (at ?s ?to)))
      (over all (sea-connection ?from ?to))
    )
    :effect (and
      (at start (not (at ?s ?from)))
      (at end (at ?s ?to))
      (at end (increase (total-cost) (sea-cost ?from ?to)))
    )
  )

  (:durative-action move-train
    :parameters (?tr - train ?from - station ?to - station)
    :duration (= ?duration (rail-duration ?from ?to))
    :condition (and
      (at start (at ?tr ?from))
      (at start (not (at ?tr ?to)))
      (over all (rail-connection ?from ?to))
    )
    :effect (and
      (at start (not (at ?tr ?from)))
      (at end (at ?tr ?to))
      (at end (increase (total-cost) (rail-cost ?from ?to)))
    )
  )
)
