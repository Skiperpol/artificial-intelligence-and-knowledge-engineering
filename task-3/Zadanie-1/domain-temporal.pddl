(define (domain transport-system)
  (:requirements :strips :typing :negative-preconditions :conditional-effects :durative-actions :numeric-fluents)

  (:types
    physobj
    package - physobj
    vehicle - physobj
    location
    warehouse airport port station - location
    truck plane ship train - vehicle
  )

  (:predicates
    (at ?obj - physobj ?l - location)
    (in ?p - package ?v - vehicle)
    (port-location ?l - location)
    (road-connection ?l1 - location ?l2 - location)
    (flight-connection ?l1 - airport ?l2 - airport)
    (water-connection ?l1 - port ?l2 - port)
    (rail-connection ?l1 - station ?l2 - station)
  )

  (:functions
    (total-cost)
    (road-cost ?l1 - location ?l2 - location)
    (road-time ?l1 - location ?l2 - location)
    (flight-cost ?l1 - airport ?l2 - airport)
    (flight-time ?l1 - airport ?l2 - airport)
    (cruise-cost ?l1 - port ?l2 - port)
    (cruise-time ?l1 - port ?l2 - port)
    (travel-cost ?l1 - station ?l2 - station)
    (travel-time ?l1 - station ?l2 - station)
  )

  (:durative-action load-package
    :parameters (?p - package ?v - vehicle ?l - location)
    :duration (= ?duration 2)
    :condition (and
      (at start (at ?p ?l))
      (over all (at ?v ?l))
    )
    :effect (and
      (at start (not (at ?p ?l)))
      (at end (in ?p ?v))
      (at end (increase (total-cost) 5))
    )
  )

  (:durative-action unload-package
    :parameters (?p - package ?v - vehicle ?l - location)
    :duration (= ?duration 2)
    :condition (and
      (at start (in ?p ?v))
      (over all (at ?v ?l))
    )
    :effect (and
      (at start (not (in ?p ?v)))
      (at end (at ?p ?l))
      (at end (increase (total-cost) 5))
      (at end (when (port-location ?l) (increase (total-cost) 3)))
    )
  )

  (:durative-action drive-truck
    :parameters (?t - truck ?from - location ?to - location)
    :duration (= ?duration (road-time ?from ?to))
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
    :parameters (?pl - plane ?from - airport ?to - airport)
    :duration (= ?duration (flight-time ?from ?to))
    :condition (and
      (at start (at ?pl ?from))
      (at start (not (at ?pl ?to)))
      (over all (flight-connection ?from ?to))
    )
    :effect (and
      (at start (not (at ?pl ?from)))
      (at end (at ?pl ?to))
      (at end (increase (total-cost) (flight-cost ?from ?to)))
    )
  )

  (:durative-action sail-ship
    :parameters (?s - ship ?from - port ?to - port)
    :duration (= ?duration (cruise-time ?from ?to))
    :condition (and
      (at start (at ?s ?from))
      (at start (not (at ?s ?to)))
      (over all (water-connection ?from ?to))
    )
    :effect (and
      (at start (not (at ?s ?from)))
      (at end (at ?s ?to))
      (at end (increase (total-cost) (cruise-cost ?from ?to)))
    )
  )

  (:durative-action move-train
    :parameters (?tr - train ?from - station ?to - station)
    :duration (= ?duration (travel-time ?from ?to))
    :condition (and
      (at start (at ?tr ?from))
      (at start (not (at ?tr ?to)))
      (over all (rail-connection ?from ?to))
    )
    :effect (and
      (at start (not (at ?tr ?from)))
      (at end (at ?tr ?to))
      (at end (increase (total-cost) (travel-cost ?from ?to)))
    )
  )
)
