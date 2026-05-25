(define (domain transport_system)
  (:requirements :strips :typing :durative-actions)

(:types
    location package vehicle - object
    warehouse airport port station - location
    truck plane ship train - vehicle
  )

  (:predicates
    (package-at ?p - package ?l - location)
    (vehicle-at ?v - vehicle ?l - location)
    (loaded ?p - package ?v - vehicle)
    (vehicle-empty ?v - vehicle)
    (compatible ?p - package ?v - vehicle)
    (road-connection ?l1 - location ?l2 - location)
    (flight-connection ?l1 - airport ?l2 - airport)
    (rail-connection ?l1 - station ?l2 - station)
    (sea-connection ?l1 - port ?l2 - port)
  )

  (:durative-action load
    :parameters (?p - package ?v - vehicle ?l - location)
    :duration (= ?duration 5)
    :condition (and
      (at start (package-at ?p ?l))
      (at start (vehicle-at ?v ?l))
      (at start (compatible ?p ?v))
      (at start (vehicle-empty ?v))
      (over all (vehicle-at ?v ?l))
    )
    :effect (and
      (at start (not (package-at ?p ?l)))
      (at start (not (vehicle-empty ?v)))
      (at end (loaded ?p ?v))
    )
  )

  (:durative-action unload
    :parameters (?p - package ?v - vehicle ?l - location)
    :duration (= ?duration 5)
    :condition (and
      (at start (loaded ?p ?v))
      (over all (vehicle-at ?v ?l))
    )
    :effect (and
      (at start (not (loaded ?p ?v)))
      (at end (package-at ?p ?l))
      (at end (vehicle-empty ?v))
    )
  )

  (:durative-action drive-truck
    :parameters (?t - truck ?from - location ?to - location)
    :duration (= ?duration 15)
    :condition (and
      (at start (vehicle-at ?t ?from))
      (over all (road-connection ?from ?to))
    )
    :effect (and
      (at start (not (vehicle-at ?t ?from)))
      (at end (vehicle-at ?t ?to))
    )
  )

  (:durative-action fly-plane
    :parameters (?a - plane ?from - airport ?to - airport)
    :duration (= ?duration 8)
    :condition (and
      (at start (vehicle-at ?a ?from))
      (over all (flight-connection ?from ?to))
    )
    :effect (and
      (at start (not (vehicle-at ?a ?from)))
      (at end (vehicle-at ?a ?to))
    )
  )

  (:durative-action sail-ship
    :parameters (?s - ship ?from - port ?to - port)
    :duration (= ?duration 30)
    :condition (and
      (at start (vehicle-at ?s ?from))
      (over all (sea-connection ?from ?to))
    )
    :effect (and
      (at start (not (vehicle-at ?s ?from)))
      (at end (vehicle-at ?s ?to))
    )
  )

  (:durative-action move-train
    :parameters (?tr - train ?from - station ?to - station)
    :duration (= ?duration 20)
    :condition (and
      (at start (vehicle-at ?tr ?from))
      (over all (rail-connection ?from ?to))
    )
    :effect (and
      (at start (not (vehicle-at ?tr ?from)))
      (at end (vehicle-at ?tr ?to))
    )
  )
)
