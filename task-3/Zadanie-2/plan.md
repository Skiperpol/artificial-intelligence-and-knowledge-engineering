(:action clean
    :parameters (robot pokoj1)
    :precondition
      (and
        (at robot pokoj1)
        (dirty pokoj1)
      )
    :effect
      (and
        (not
          (dirty pokoj1)
        )
        (clean pokoj1)
      )
  )


  (:action move
    :parameters (robot pokoj1 pokoj2)
    :precondition
      (at robot pokoj1)
    :effect
      (and
        (not
          (at robot pokoj1)
        )
        (at robot pokoj2)
      )
  )

  (:action clean
    :parameters (robot pokoj2)
    :precondition
      (and
        (at robot pokoj2)
        (dirty pokoj2)
      )
    :effect
      (and
        (not
          (dirty pokoj2)
        )
        (clean pokoj2)
      )
  )


  (:action move
    :parameters (robot pokoj2 pokoj3)
    :precondition
      (at robot pokoj2)
    :effect
      (and
        (not
          (at robot pokoj2)
        )
        (at robot pokoj3)
      )
  )


   (:action clean
    :parameters (robot pokoj3)
    :precondition
      (and
        (at robot pokoj3)
        (dirty pokoj3)
      )
    :effect
      (and
        (not
          (dirty pokoj3)
        )
        (clean pokoj3)
      )
  )