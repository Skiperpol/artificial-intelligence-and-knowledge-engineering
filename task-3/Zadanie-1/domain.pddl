(define (domain transport-system)
  (:requirements :strips :typing :negative-preconditions :action-costs)

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

  (:action load-package
    :parameters (?p - package ?v - vehicle ?l - location)
    :precondition (and
      (at ?p ?l)
      (at ?v ?l)
      (not (in ?p ?v))
    )
    :effect (and
      (not (at ?p ?l))
      (in ?p ?v)
      (increase (total-cost) 5)
    )
  )

  (:action unload-package
    :parameters (?p - package ?v - vehicle ?l - location)
    :precondition (and
      (in ?p ?v)
      (at ?v ?l)
      (not (at ?p ?l))
      (not (port-location ?l))
    )
    :effect (and
      (not (in ?p ?v))
      (at ?p ?l)
      (increase (total-cost) 5)
    )
  )

  (:action unload-at-port
    :parameters (?p - package ?v - vehicle ?l - port)
    :precondition (and
      (in ?p ?v)
      (at ?v ?l)
      (not (at ?p ?l))
    )
    :effect (and
      (not (in ?p ?v))
      (at ?p ?l)
      (increase (total-cost) 8)
    )
  )

  (:action drive-truck
    :parameters (?t - truck ?from - location ?to - location)
    :precondition (and
      (at ?t ?from)
      (not (at ?t ?to))
      (road-connection ?from ?to)
    )
    :effect (and
      (not (at ?t ?from))
      (at ?t ?to)
      (increase (total-cost) (road-cost ?from ?to))
    )
  )

  (:action fly-plane
    :parameters (?pl - plane ?from - airport ?to - airport)
    :precondition (and
      (at ?pl ?from)
      (not (at ?pl ?to))
      (flight-connection ?from ?to)
    )
    :effect (and
      (not (at ?pl ?from))
      (at ?pl ?to)
      (increase (total-cost) (flight-cost ?from ?to))
    )
  )

  (:action sail-ship
    :parameters (?s - ship ?from - port ?to - port)
    :precondition (and
      (at ?s ?from)
      (not (at ?s ?to))
      (water-connection ?from ?to)
    )
    :effect (and
      (not (at ?s ?from))
      (at ?s ?to)
      (increase (total-cost) (cruise-cost ?from ?to))
    )
  )

  (:action move-train
    :parameters (?tr - train ?from - station ?to - station)
    :precondition (and
      (at ?tr ?from)
      (not (at ?tr ?to))
      (rail-connection ?from ?to)
    )
    :effect (and
      (not (at ?tr ?from))
      (at ?tr ?to)
      (increase (total-cost) (travel-cost ?from ?to))
    )
  )
)
