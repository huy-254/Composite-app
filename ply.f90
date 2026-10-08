module ply_module
    implicit none
    private
    public :: ply
    real(8), parameter :: PI = atan(1.0d0)*4.0d0

contains

subroutine ply(E1f, E2f, G12f, Em, G12m, vf, sLf_tens, sLm_tens, phi, sLm_compr, sLTm, &
               rho_f, rho_m, nju12_f, nju12_m, &
               E1c, E2c, G12c, nju12_c, sLc_tens, sLc_compr, sTc_tens, sTc_compr, sLTc, rho_c)
    !! Calculates composite layer properties from fiber and matrix properties
    !! Based on Gibson equations

    implicit none

    ! Input parameters (fiber, matrix, and composite properties)
    real(8), intent(in) :: E1f                ! Fiber longitudinal modulus
    real(8), intent(in) :: E2f                ! Fiber transverse modulus
    real(8), intent(in) :: G12f               ! Fiber shear modulus
    real(8), intent(in) :: Em                 ! Matrix modulus
    real(8), intent(in) :: G12m               ! Matrix shear modulus
    real(8), intent(in) :: vf                 ! Fiber volume fraction
    real(8), intent(in) :: sLf_tens           ! Fiber longitudinal tensile strength
    real(8), intent(in) :: sLm_tens           ! Matrix longitudinal tensile strength
    real(8), intent(in) :: phi                ! Fiber angle parameter
    real(8), intent(in) :: sLm_compr          ! Matrix longitudinal compressive strength
    real(8), intent(in) :: sLTm               ! Matrix shear strength
    real(8), intent(in) :: rho_f              ! Fiber density
    real(8), intent(in) :: rho_m              ! Matrix density
    real(8), intent(in) :: nju12_f            ! Fiber Poisson's ratio
    real(8), intent(in) :: nju12_m            ! Matrix Poisson's ratio

    ! Output parameters (composite layer properties)
    real(8), intent(out) :: E1c               ! Composite longitudinal modulus
    real(8), intent(out) :: E2c               ! Composite transverse modulus
    real(8), intent(out) :: G12c              ! Composite shear modulus
    real(8), intent(out) :: nju12_c           ! Composite Poisson's ratio
    real(8), intent(out) :: sLc_tens          ! Composite longitudinal tensile strength
    real(8), intent(out) :: sLc_compr         ! Composite longitudinal compressive strength
    real(8), intent(out) :: sTc_tens          ! Composite transverse tensile strength
    real(8), intent(out) :: sTc_compr         ! Composite transverse compressive strength
    real(8), intent(out) :: sLTc              ! Composite shear strength
    real(8), intent(out) :: rho_c             ! Composite density

    ! Local variables
    real(8) :: eLf_tens, eLm_tens, d_s_ratio, F, eT_tens
    real(8) :: sLc_compr_ext, sLc_compr_shear, sLc_compr_rupture
    real(8) :: sqrt_vf

    ! Modulus calculations
    E1c = E1f*vf + Em*(1.0d0-vf)  ! Gibson eq. 3.23

    sqrt_vf = sqrt(vf)
    E2c = Em*((1.0d0-sqrt_vf) + sqrt_vf/(1.0d0-sqrt_vf*(1.0d0-Em/E2f)))  ! Gibson eq. 3.50

    G12c = G12m*((1.0d0-sqrt_vf) + sqrt_vf/(1.0d0-sqrt_vf*(1.0d0-G12m/G12f)))  ! Gibson eq. 3.50

    nju12_c = nju12_f*vf + nju12_m*(1.0d0-vf)  ! Gibson eq. 3.41

    ! Strength calculations
    ! Longitudinal tensile strength
    eLf_tens = sLf_tens/E1f
    eLm_tens = sLm_tens/Em

    if (eLf_tens < eLm_tens) then  ! Gibson Fig. 4.9
        sLc_tens = eLf_tens*E1c
        if (vf < (sLm_tens-eLf_tens*Em)/(sLf_tens-eLf_tens*Em)) then  ! Gibson Eq. 4.22
            sLc_tens = sLm_tens*(1.0d0-vf)  ! Gibson Eq. 4.23
        end if
    else
        sLc_tens = eLm_tens*E1c
    end if

    ! Transverse strength
    d_s_ratio = sqrt(vf*4.0d0/PI)
    F = (d_s_ratio*(Em/E2f-1.0d0)+1.0d0)**(-1.0d0)  ! Gibson Eq. 4.38
    sTc_tens = E2c*sLm_tens/Em/F  ! Gibson Eq. 4.35
    sTc_compr = E2c*sLm_compr/Em/F  ! Gibson Eq. 4.35

    ! Longitudinal compressive strength
    sLc_compr_ext = 2.0d0*vf*sqrt(vf*Em*E1f/3.0d0/(1.0d0-vf))  ! Gibson Eq. 4.29
    sLc_compr_shear = sLTm/(sLTm/(G12m/(1.0d0-vf))+phi)  ! Gibson Eq. 4.30; Daniel Eq. 5.28
    eT_tens = eLm_tens/F  ! Gibson Eq. 4.34
    sLc_compr_rupture = E1c*eT_tens/nju12_c  ! Gibson Eq. 4.32
    sLc_compr = min(sLc_compr_ext, sLc_compr_shear, sLc_compr_rupture)

    ! Shear strength
    F = (d_s_ratio*(G12m/G12f-1.0d0)+1.0d0)**(-1.0d0)  ! Gibson Eq. 4.41
    sLTc = G12c*sLTm/G12m/F  ! Gibson Eq. 4.35

    ! Density
    rho_c = rho_f*vf+rho_m*(1.0d0-vf)

end subroutine ply

end module ply_module
