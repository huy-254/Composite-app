Composite App - Tính thông số lớp và tấm composite
==================================================

Chạy chương trình chính:
   python composite_app.py

- Bên trái "Tạo lớp": tạo lớp bằng 1 trong 3 cách
    * Tạo từ sợi và keo (gọi ply_calc.exe)
    * Nhập thông số lớp trực tiếp
    * Thư viện vật liệu (composite + foam, dữ liệu trong materials_library.py)
- Bên phải "Tạo tấm": chọn lớp và góc xếp cho từng hàng, bấm Calculate để tính
  ma trận A, D của tấm (gọi laminate_calc.exe).

Tệp tin bổ sung:
- composite_app.py      - Giao diện chính (tkinter)
- materials_library.py  - Thư viện vật liệu
- laminate.f90          - Module Fortran tính ma trận A, D của tấm
- laminate_calc.f90     - Chương trình Fortran main cho laminate
- laminate_calc.exe     - File thực thi đã biên dịch

Biên dịch lại Fortran:
   gfortran -static -o ply_calc.exe ply.f90 ply_calc.f90
   gfortran -static -o laminate_calc.exe laminate.f90 laminate_calc.f90


Hướng dẫn sử dụng Composite Ply Properties Calculator (gui_ply.py)
==================================================================

Tệp tin:
--------
1. ply.f90 - Module Fortran chứa subroutine ply tính toán thông số lớp composite
2. ply_calc.f90 - Chương trình Fortran main có thể chạy độc lập
3. ply_calc.exe - File thực thi đã biên dịch
4. gui_ply.py - Giao diện Python (tkinter) để nhập dữ liệu

Cách sử dụng:
-----------
1. Chạy file gui_ply.py:
   python gui_ply.py

2. Nhập các thông số đầu vào (tự động chuyển đơn vị):
   - E1f: Độ cứng dọc trục của sợi (GPa) - nhập 230 cho 230 GPa
   - E2f: Độ cứng ngang trục của sợi (GPa)
   - G12f: Mô đun cắt của sợi (GPa)
   - Em: Mô đun của keo (GPa)
   - G12m: Mô đun cắt của keo (GPa)
   - vf: Phần trăm thể tích sợi (0-1)
   - sLf_tens: Giới hạn bền kéo dọc sợi (MPa) - nhập 4900 cho 4900 MPa
   - sLm_tens: Giới hạn bền kéo của keo (MPa)
   - phi: Tham số góc (radian) - có thể dùng biểu thức như 2*pi/180
   - sLm_compr: Giới hạn bền nén của keo (MPa)
   - sLTm: Giới hạn bền cắt của keo (MPa)
   - rho_f: Khối lượng riêng sợi (kg/m³)
   - rho_m: Khối lượng riêng keo (kg/m³)
   - nju12_f: Hệ số Poisson của sợi
   - nju12_m: Hệ số Poisson của keo

3. Bấm nút "Calculate" để tính toán
   Kết quả sẽ hiển thị ở phần "Results"

4. Bấm nút "Cancel" để xóa tất cả dữ liệu

Các thông số đầu ra (Results):
-----------------------------
- E1c: Độ cứng dọc trục của lớp composite (GPa)
- E2c: Độ cứng ngang trục của lớp composite (GPa)
- G12c: Mô đun cắt của lớp composite (GPa)
- nju12_c: Hệ số Poisson của lớp composite
- sLc_tens: Giới hạn bền kéo dọc trục của composite (MPa)
- sLc_compr: Giới hạn bền nén dọc trục của composite (MPa)
- sTc_tens: Giới hạn bền kéo ngang trục của composite (MPa)
- sTc_compr: Giới hạn bền nén ngang trục của composite (MPa)
- sLTc: Giới hạn bền cắt của composite (MPa)
- rho_c: Khối lượng riêng của lớp composite (kg/m³)

Lưu ý:
-----
- Tất cả file (ply.f90, ply_calc.exe, gui_ply.py) phải nằm cùng thư mục
- Python 3.x được yêu cầu để chạy giao diện
- Các ô nhập có thể nhận:
  * Số thập phân: 230, 2.9, 0.5751
  * Biểu thức: 2*pi/180, 2.9e9/2/1.35, sqrt(2)
  * Hằng: pi, e
  * Hàm: sqrt(), sin(), cos(), tan(), exp(), log(), deg2rad()
  * Lũy thừa: 2^3 hoặc 2**3
- Tự động chuyển đơn vị:
  * Mô đun (E, G): nhập GPa, tự động × 1e9 để đổi thành Pa
  * Bền (s): nhập MPa, tự động × 1e6 để đổi thành Pa
  * Rho, vf, phi: nhập trực tiếp (kg/m³, không có unit, radian)
- Nếu biên dịch lại Fortran, dùng lệnh:
  gfortran -o ply_calc.exe ply.f90 ply_calc.f90
