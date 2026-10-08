"""Built-in material library (units: GPa, MPa, kg/m3).

Composite values follow the ANSYS Engineering Data "Composite Materials" library
(ACP prepreg data); foam values follow typical cross-linked PVC foam datasheets
(Divinycell H series). They are reference values - check them against your own data.

Each entry gives the same keys as a ply (see OUTPUT_PARAMS in gui_ply.py).
Strengths are positive magnitudes. Foams are treated as isotropic: E1c = E2c.
"""

COMPOSITES = [
    {
        "name": "Epoxy Carbon UD (230 GPa) Prepreg",
        "description": "Sợi carbon modul tiêu chuẩn (T300/T700) / epoxy, một hướng.",
        "E1c": 121.0, "E2c": 8.6, "G12c": 4.7, "nju12_c": 0.27,
        "sLc_tens": 2231.0, "sLc_compr": 1082.0, "sTc_tens": 29.0, "sTc_compr": 100.0,
        "sLTc": 60.0, "rho_c": 1490.0,
    },
    {
        "name": "Epoxy Carbon UD (395 GPa) Prepreg",
        "description": "Sợi carbon modul cao (M40J) / epoxy, một hướng.",
        "E1c": 209.0, "E2c": 9.45, "G12c": 5.5, "nju12_c": 0.27,
        "sLc_tens": 1979.0, "sLc_compr": 893.0, "sTc_tens": 26.0, "sTc_compr": 139.0,
        "sLTc": 55.0, "rho_c": 1540.0,
    },
    {
        "name": "Epoxy Carbon Woven (230 GPa) Prepreg",
        "description": "Vải carbon dệt cân bằng / epoxy (cùng tính chất theo phương 1 và 2).",
        "E1c": 61.34, "E2c": 61.34, "G12c": 3.3, "nju12_c": 0.04,
        "sLc_tens": 805.0, "sLc_compr": 509.0, "sTc_tens": 805.0, "sTc_compr": 509.0,
        "sLTc": 125.0, "rho_c": 1420.0,
    },
    {
        "name": "Epoxy E-Glass UD",
        "description": "Sợi thủy tinh E / epoxy, một hướng.",
        "E1c": 45.0, "E2c": 10.0, "G12c": 5.0, "nju12_c": 0.3,
        "sLc_tens": 1100.0, "sLc_compr": 675.0, "sTc_tens": 35.0, "sTc_compr": 120.0,
        "sLTc": 80.0, "rho_c": 2000.0,
    },
    {
        "name": "Epoxy S-Glass UD",
        "description": "Sợi thủy tinh S (độ bền cao) / epoxy, một hướng.",
        "E1c": 50.0, "E2c": 8.0, "G12c": 5.0, "nju12_c": 0.3,
        "sLc_tens": 1700.0, "sLc_compr": 1000.0, "sTc_tens": 35.0, "sTc_compr": 120.0,
        "sLTc": 80.0, "rho_c": 2000.0,
    },
]


def _foam(name, description, E, G, nju, s_tens, s_compr, s_shear, rho):
    """Isotropic foam: same properties in directions 1 and 2."""
    return {
        "name": name, "description": description,
        "E1c": E, "E2c": E, "G12c": G, "nju12_c": nju,
        "sLc_tens": s_tens, "sLc_compr": s_compr, "sTc_tens": s_tens, "sTc_compr": s_compr,
        "sLTc": s_shear, "rho_c": rho,
    }


FOAMS = [
    _foam("PVC Foam 60 kg/m3 (H60)", "Foam PVC liên kết ngang, tỷ trọng thấp - lõi tấm sandwich.",
          E=0.070, G=0.020, nju=0.3, s_tens=1.8, s_compr=0.9, s_shear=0.76, rho=60.0),
    _foam("PVC Foam 100 kg/m3 (H100)", "Foam PVC liên kết ngang, tỷ trọng trung bình.",
          E=0.135, G=0.035, nju=0.3, s_tens=3.5, s_compr=2.0, s_shear=1.6, rho=100.0),
    _foam("PVC Foam 200 kg/m3 (H200)", "Foam PVC liên kết ngang, tỷ trọng cao - vùng chịu tải tập trung.",
          E=0.310, G=0.073, nju=0.3, s_tens=7.1, s_compr=5.4, s_shear=3.5, rho=200.0),
]

LIBRARY = [("Composite", COMPOSITES), ("Foam", FOAMS)]
