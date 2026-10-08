program laminate_calc
    use laminate_module
    implicit none

    ! Input: first line  -> n_layers, h0 (mm)
    !        next n lines -> E1 (GPa), E2 (GPa), G12 (GPa), nju12, theta (deg), t (mm)
    !        Layer 1 is the first line.
    integer :: n, i
    real(8) :: h0_mm, h0
    real(8), allocatable :: E1_layer(:), E2_layer(:), G12_layer(:), nju_layer(:)
    real(8), allocatable :: theta_layer(:), t_layer(:)

    ! Output: A (N/m), D (N.m)
    real(8) :: A_lam(3,3), D_lam(3,3)

    read(*,*) n, h0_mm
    allocate(E1_layer(n), E2_layer(n), G12_layer(n), nju_layer(n), theta_layer(n), t_layer(n))
    do i = 1, n
        read(*,*) E1_layer(i), E2_layer(i), G12_layer(i), nju_layer(i), theta_layer(i), t_layer(i)
    end do

    ! Convert to SI units (Pa, m); theta stays in degrees
    E1_layer = E1_layer * 1.0d9
    E2_layer = E2_layer * 1.0d9
    G12_layer = G12_layer * 1.0d9
    t_layer = t_layer * 1.0d-3
    h0 = h0_mm * 1.0d-3

    call laminate(E1_layer, E2_layer, theta_layer, t_layer, G12_layer, nju_layer, h0, A_lam, D_lam)

    ! Write A then D, row by row
    do i = 1, 3
        write(*,'(3ES16.7)') A_lam(i,:)
    end do
    do i = 1, 3
        write(*,'(3ES16.7)') D_lam(i,:)
    end do

end program laminate_calc
