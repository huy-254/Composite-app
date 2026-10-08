program ply_calc
    use ply_module
    implicit none

    ! Input variables (GPa for modulus, MPa for strength, radian for phi)
    real(8) :: E1f_gpa, E2f_gpa, G12f_gpa, Em_gpa, G12m_gpa, vf
    real(8) :: sLf_tens_mpa, sLm_tens_mpa, phi, sLm_compr_mpa, sLTm_mpa
    real(8) :: rho_f, rho_m, nju12_f, nju12_m

    ! Converted to SI (Pa)
    real(8) :: E1f, E2f, G12f, Em, G12m
    real(8) :: sLf_tens, sLm_tens, sLm_compr, sLTm

    ! Output variables
    real(8) :: E1c, E2c, G12c, nju12_c
    real(8) :: sLc_tens, sLc_compr, sTc_tens, sTc_compr, sLTc, rho_c

    ! Read input (GPa for modulus, MPa for strength, etc.)
    read(*,*) E1f_gpa, E2f_gpa, G12f_gpa, Em_gpa, G12m_gpa, vf, sLf_tens_mpa, sLm_tens_mpa, &
              phi, sLm_compr_mpa, sLTm_mpa, rho_f, rho_m, nju12_f, nju12_m

    ! Convert to SI units (Pa)
    E1f = E1f_gpa * 1.0d9
    E2f = E2f_gpa * 1.0d9
    G12f = G12f_gpa * 1.0d9
    Em = Em_gpa * 1.0d9
    G12m = G12m_gpa * 1.0d9
    sLf_tens = sLf_tens_mpa * 1.0d6
    sLm_tens = sLm_tens_mpa * 1.0d6
    sLm_compr = sLm_compr_mpa * 1.0d6
    sLTm = sLTm_mpa * 1.0d6

    ! Call ply subroutine
    call ply(E1f, E2f, G12f, Em, G12m, vf, sLf_tens, sLm_tens, phi, sLm_compr, sLTm, &
             rho_f, rho_m, nju12_f, nju12_m, &
             E1c, E2c, G12c, nju12_c, sLc_tens, sLc_compr, sTc_tens, sTc_compr, sLTc, rho_c)

    ! Write output (convert to GPa/MPa for readability)
    write(*,'(10ES15.7)') E1c/1.0d9, E2c/1.0d9, G12c/1.0d9, nju12_c, &
                          sLc_tens/1.0d6, sLc_compr/1.0d6, sTc_tens/1.0d6, sTc_compr/1.0d6, sLTc/1.0d6, rho_c

end program ply_calc
