module laminate_module
    implicit none
    private
    public :: laminate

contains

    subroutine laminate(E1_layer, E2_layer, theta_layer, t_layer, G12_layer, nju_layer, h0, A_lam, D_lam)
        implicit none

        ! Input parameters
        real(8), intent(in) :: E1_layer(:)
        real(8), intent(in) :: E2_layer(:)
        real(8), intent(in) :: theta_layer(:)
        real(8), intent(in) :: t_layer(:)
        real(8), intent(in) :: G12_layer(:)
        real(8), intent(in) :: nju_layer(:)
        real(8), intent(in) :: h0

        ! Output parameters
        real(8), intent(out) :: A_lam(3,3)
        real(8), intent(out) :: D_lam(3,3)

        ! Local variables
        integer :: i, n
        real(8) :: c, s
        real(8) :: E1, E2, G12, nju12
        real(8) :: S11, S22, S12, S21, S66
        real(8) :: Smat(3,3), Q(3,3), Q0(3,3)
        real(8) :: T(3,3), T_inv(3,3)
        real(8) :: z0, zk, zk_1
        real(8) :: pi

        ! Initialize output matrices
        A_lam = 0.0d0
        D_lam = 0.0d0

        ! Get number of layers
        n = size(theta_layer)

        ! Calculate z0 (half of total thickness)
        z0 = sum(t_layer) / 2.0d0

        ! Loop through each layer
        do i = 1, n
            ! Get angle in radians
            pi = 4.0d0 * atan(1.0d0)
            c = cos(theta_layer(i) * pi / 180.0d0)
            s = sin(theta_layer(i) * pi / 180.0d0)

            ! Get material properties
            E1 = E1_layer(i)
            E2 = E2_layer(i)
            G12 = G12_layer(i)
            nju12 = nju_layer(i)

            ! Calculate S_12 matrix (compliance matrix)
            S11 = 1.0d0 / E1
            S22 = 1.0d0 / E2
            S12 = -nju12 / E1
            S21 = S12
            S66 = 1.0d0 / G12

            Smat(1,1) = S11
            Smat(1,2) = S12
            Smat(1,3) = 0.0d0
            Smat(2,1) = S21
            Smat(2,2) = S22
            Smat(2,3) = 0.0d0
            Smat(3,1) = 0.0d0
            Smat(3,2) = 0.0d0
            Smat(3,3) = S66

            ! Q_12 matrix (stiffness matrix - inverse of S)
            call matrix_inverse_3x3(Smat, Q)
            Q(:,3) = Q(:,3) * 2.0d0

            ! Transformation matrix T (Gibson eq. 2.32)
            T(1,1) = c**2
            T(1,2) = s**2
            T(1,3) = 2.0d0 * c * s
            T(2,1) = s**2
            T(2,2) = c**2
            T(2,3) = -2.0d0 * c * s
            T(3,1) = -c * s
            T(3,2) = c * s
            T(3,3) = c**2 - s**2

            ! Q_xy matrix (rotated stiffness matrix)
            call matrix_inverse_3x3(T, T_inv)
            Q0 = matmul(T_inv, matmul(Q, T))
            Q0(:,3) = Q0(:,3) / 2.0d0

            ! A_xy of composite laminate (Gibson eq. 7.38)
            A_lam = A_lam + Q0 * t_layer(i)

            ! Calculate z coordinates for bending stiffness
            zk = -sum(t_layer) + sum(t_layer(1:n-i+1)) + z0 + h0
            zk_1 = -sum(t_layer) + sum(t_layer(1:n-i)) + z0 + h0

            ! D_xy of composite laminate (Gibson eq. 7.40)
            D_lam = D_lam + Q0 * (zk**3 - zk_1**3) / 3.0d0
        end do

    end subroutine laminate


    subroutine matrix_inverse_3x3(A, A_inv)
        implicit none
        real(8), intent(in) :: A(3,3)
        real(8), intent(out) :: A_inv(3,3)
        real(8) :: det

        ! Calculate determinant
        det = A(1,1) * (A(2,2)*A(3,3) - A(2,3)*A(3,2)) &
             - A(1,2) * (A(2,1)*A(3,3) - A(2,3)*A(3,1)) &
             + A(1,3) * (A(2,1)*A(3,2) - A(2,2)*A(3,1))

        ! Relative tolerance: compliance entries in SI are ~1e-11, so det ~1e-33
        if (abs(det) <= 1.0d-12 * maxval(abs(A))**3) then
            print *, "Error: Matrix is singular!"
            return
        end if

        ! Calculate inverse using cofactor method
        A_inv(1,1) = (A(2,2)*A(3,3) - A(2,3)*A(3,2)) / det
        A_inv(1,2) = -(A(1,2)*A(3,3) - A(1,3)*A(3,2)) / det
        A_inv(1,3) = (A(1,2)*A(2,3) - A(1,3)*A(2,2)) / det

        A_inv(2,1) = -(A(2,1)*A(3,3) - A(2,3)*A(3,1)) / det
        A_inv(2,2) = (A(1,1)*A(3,3) - A(1,3)*A(3,1)) / det
        A_inv(2,3) = -(A(1,1)*A(2,3) - A(1,3)*A(2,1)) / det

        A_inv(3,1) = (A(2,1)*A(3,2) - A(2,2)*A(3,1)) / det
        A_inv(3,2) = -(A(1,1)*A(3,2) - A(1,2)*A(3,1)) / det
        A_inv(3,3) = (A(1,1)*A(2,2) - A(1,2)*A(2,1)) / det

    end subroutine matrix_inverse_3x3

end module laminate_module
