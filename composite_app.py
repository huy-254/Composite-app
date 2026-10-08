"""Composite laminate program.

Left half  : "Tạo lớp"  - create plies (from fiber + matrix, or by entering ply properties).
Right half : "Tạo tấm"  - stack the created plies with angles, compute A and D (laminate_calc.exe).
"""
import subprocess
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import ttk, messagebox

from gui_ply import PlyPropertiesGUI, OUTPUT_PARAMS, eval_expr
from materials_library import LIBRARY

THICKNESS_MISSING_MSG = "missing"
THICKNESS_INVALID_MSG = "Chiều dày không hợp lệ (mm, phải > 0)"


@dataclass
class Ply:
    """Properties of one composite ply (GPa, MPa, kg/m3, mm)."""
    name: str
    thickness: float          # mm
    E1c: float
    E2c: float
    G12c: float
    nju12_c: float
    sLc_tens: float
    sLc_compr: float
    sTc_tens: float
    sTc_compr: float
    sLTc: float
    rho_c: float
    source: str = ""          # "Sợi + keo" or "Nhập trực tiếp"
    inputs: dict = field(default_factory=dict)  # fiber/matrix inputs, if any


def parse_thickness(text):
    """Return (thickness_mm, error_message). error_message is '' when valid."""
    if not text.strip():
        return None, THICKNESS_MISSING_MSG
    try:
        t = eval_expr(text)
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
        return None, THICKNESS_INVALID_MSG
    if t <= 0:
        return None, THICKNESS_INVALID_MSG
    return t, ""


class ThicknessMixin:
    """Thickness entry + 'Create ply' button that only works with a valid thickness."""

    def _build_ply_frame(self, main, default_name):
        frame = ttk.LabelFrame(main, text="Ply", padding=8)
        frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(frame, text="Tên lớp").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.name_var = tk.StringVar(value=default_name)
        ttk.Entry(frame, textvariable=self.name_var, width=16).grid(row=0, column=1, padx=5, pady=3)
        ttk.Label(frame, text="t - Ply thickness (mm)").grid(
            row=0, column=2, sticky=tk.W, padx=(20, 5), pady=3)
        self.thickness_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.thickness_var, width=14).grid(
            row=0, column=3, padx=5, pady=3)

    def _build_warning(self, main):
        self.warning_label = tk.Label(main, text="", fg="red", anchor=tk.E)
        self.warning_label.pack(fill=tk.X, pady=(4, 0))
        self.thickness_var.trace_add("write", lambda *_: self._update_create_state())
        self._update_create_state()

    def _update_create_state(self):
        _, err = parse_thickness(self.thickness_var.get())
        # Empty thickness: the disabled button is enough, no message
        self.warning_label.config(text="" if err == THICKNESS_MISSING_MSG else err)
        self.create_button.state(["disabled"] if err else ["!disabled"])

    def _ply_name(self):
        return self.name_var.get().strip() or self.default_name


class PlyFromFiberMatrixDialog(ThicknessMixin, PlyPropertiesGUI):
    """Same window as gui_ply.py, plus ply thickness and a 'Create ply' button."""

    def __init__(self, parent, default_name, on_create):
        self.default_name = default_name
        self.on_create = on_create
        top = tk.Toplevel(parent)
        super().__init__(top)
        top.title("Tạo lớp từ sợi và keo")
        top.transient(parent)
        top.grab_set()

    def _build_buttons(self, main):
        self._build_ply_frame(main, self.default_name)
        buttons = super()._build_buttons(main)
        self.create_button = ttk.Button(buttons, text="Create ply", command=self.create_ply)
        self.create_button.pack(side=tk.RIGHT, padx=4)
        self._build_warning(main)
        return buttons

    def clear(self):
        super().clear()
        self.thickness_var.set("")

    def create_ply(self):
        t, err = parse_thickness(self.thickness_var.get())
        if err:
            self._update_create_state()
            return
        results = self.calculate()  # always recalculate so the ply matches current inputs
        if results is None:
            return
        inputs = {name: var.get() for name, var in self.input_vars.items()}
        ply = Ply(name=self._ply_name(), thickness=t, source="Sợi + keo", inputs=inputs, **results)
        self.on_create(ply)
        self.root.destroy()


class PlyManualDialog(ThicknessMixin):
    """Enter ply properties directly."""

    def __init__(self, parent, default_name, on_create):
        self.default_name = default_name
        self.on_create = on_create
        self.root = tk.Toplevel(parent)
        self.root.title("Nhập thông số lớp")
        self.root.resizable(False, False)
        self.root.transient(parent)
        self.root.grab_set()

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        props = ttk.LabelFrame(main, text="Composite ply properties", padding=8)
        props.pack(fill=tk.X)
        self.prop_vars = {}
        half = (len(OUTPUT_PARAMS) + 1) // 2
        for i, (text, name) in enumerate(OUTPUT_PARAMS):
            r, c = i % half, (i // half) * 2
            ttk.Label(props, text=text).grid(row=r, column=c, sticky=tk.W, padx=(5, 8), pady=3)
            var = tk.StringVar()
            ttk.Entry(props, textvariable=var, width=16).grid(
                row=r, column=c + 1, sticky=tk.W, padx=(0, 20), pady=3)
            self.prop_vars[name] = var

        self._build_ply_frame(main, default_name)

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(buttons, text="Cancel", command=self.root.destroy).pack(side=tk.RIGHT, padx=4)
        ttk.Button(buttons, text="Clear", command=self.clear).pack(side=tk.RIGHT, padx=4)
        self.create_button = ttk.Button(buttons, text="Create ply", command=self.create_ply)
        self.create_button.pack(side=tk.RIGHT, padx=4)
        self._build_warning(main)

    def clear(self):
        for var in self.prop_vars.values():
            var.set("")
        self.thickness_var.set("")

    def create_ply(self):
        t, err = parse_thickness(self.thickness_var.get())
        if err:
            self._update_create_state()
            return
        values = {}
        for text, name in OUTPUT_PARAMS:
            try:
                values[name] = eval_expr(self.prop_vars[name].get())
            except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
                messagebox.showerror("Error", f"Invalid or empty input: {text}", parent=self.root)
                return
        ply = Ply(name=self._ply_name(), thickness=t, source="Nhập trực tiếp", **values)
        self.on_create(ply)
        self.root.destroy()


class MaterialLibraryDialog(ThicknessMixin):
    """Material list on the left, properties of the selected material on the right."""

    def __init__(self, parent, default_name, on_create):
        self.default_name = default_name
        self.on_create = on_create
        self.material = None
        self.root = tk.Toplevel(parent)
        self.root.withdraw()  # stay hidden while measuring, see _fix_window_size
        self.root.title("Thư viện vật liệu")
        self.root.resizable(False, False)
        self.root.transient(parent)

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        panes = ttk.Frame(main)
        panes.pack(fill=tk.BOTH, expand=True)

        # Left: material list grouped by type
        left = ttk.LabelFrame(panes, text="Danh sách vật liệu", padding=8)
        left.grid(row=0, column=0, sticky=tk.NS)
        panes.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse", height=14)
        self.tree.column("#0", width=330)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.materials = {}  # tree iid -> material dict
        for group, materials in LIBRARY:
            gid = self.tree.insert("", tk.END, text=group, open=True)
            for mat in materials:
                self.materials[self.tree.insert(gid, tk.END, text=mat["name"])] = mat
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._on_select())

        # Right: properties of the selected material
        right = ttk.LabelFrame(panes, text="Thông số vật liệu", padding=8)
        right.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 0))
        self.title_var = tk.StringVar(value="Chọn một vật liệu ở danh sách bên trái")
        self.desc_var = tk.StringVar()
        ttk.Label(right, textvariable=self.title_var, font=("TkDefaultFont", 10, "bold"),
                  wraplength=330).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 2))
        ttk.Label(right, textvariable=self.desc_var, wraplength=330, foreground="gray25").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))
        self.prop_vars = {}
        for r, (text, name) in enumerate(OUTPUT_PARAMS, start=2):
            ttk.Label(right, text=text).grid(row=r, column=0, sticky=tk.W, padx=(5, 8), pady=3)
            var = tk.StringVar(value="---")
            ttk.Entry(right, textvariable=var, width=16, state="readonly", justify=tk.RIGHT).grid(
                row=r, column=1, sticky=tk.W, pady=3)
            self.prop_vars[name] = var

        self._build_ply_frame(main, default_name)

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(buttons, text="Cancel", command=self.root.destroy).pack(side=tk.RIGHT, padx=4)
        self.create_button = ttk.Button(buttons, text="Create ply", command=self.create_ply)
        self.create_button.pack(side=tk.RIGHT, padx=4)
        self._build_warning(main)
        self._fix_window_size()
        self.root.deiconify()
        self.root.grab_set()  # needs a visible window

    def _fix_window_size(self):
        """Size the window for the largest material entry, so it does not jump when selecting.

        Runs while the window is withdrawn, so the trial layouts are never drawn on screen.
        """
        width = height = 0
        for mat in [None, *self.materials.values()]:
            self._show_material(mat)
            self.root.update_idletasks()
            width = max(width, self.root.winfo_reqwidth())
            height = max(height, self.root.winfo_reqheight())
        self._show_material(None)
        self.root.geometry(f"{width}x{height}")

    def _show_material(self, mat):
        mat = mat or {}
        self.title_var.set(mat.get("name", "Chọn một vật liệu ở danh sách bên trái"))
        self.desc_var.set(mat.get("description", ""))
        for name, var in self.prop_vars.items():
            var.set(f"{mat[name]:.6g}" if mat else "---")

    def _on_select(self):
        sel = self.tree.selection()
        self.material = self.materials.get(sel[0]) if sel else None
        self._show_material(self.material)
        self._update_create_state()

    def _update_create_state(self):
        super()._update_create_state()
        if self.material is None:  # a group heading, or nothing selected
            self.create_button.state(["disabled"])

    def create_ply(self):
        t, err = parse_thickness(self.thickness_var.get())
        if err or self.material is None:
            self._update_create_state()
            return
        values = {name: self.material[name] for _, name in OUTPUT_PARAMS}
        ply = Ply(name=self._ply_name(), thickness=t, source=f"Thư viện: {self.material['name']}",
                  **values)
        self.on_create(ply)
        self.root.destroy()


PLY_COLUMNS = [
    ("name", "Tên lớp", 90),
    ("t", "t (mm)", 60),
    ("E1c", "E1 (GPa)", 70),
    ("E2c", "E2 (GPa)", 70),
    ("G12c", "G12 (GPa)", 70),
    ("nju12_c", "ν12", 55),
    ("rho_c", "ρ (kg/m3)", 70),
    ("source", "Nguồn", 95),
]


class CompositeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Composite - Lớp và Tấm")
        self.root.geometry("1100x520")
        self.plies = {}   # treeview iid -> Ply
        self._ply_counter = 0

        main = ttk.Frame(root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1, uniform="half")
        main.columnconfigure(1, weight=1, uniform="half")
        main.rowconfigure(0, weight=1)

        self._build_ply_panel(main)
        self._build_laminate_panel(main)

    # ---------- Left: Tạo lớp ----------
    def _build_ply_panel(self, main):
        panel = ttk.LabelFrame(main, text="Tạo lớp", padding=10)
        panel.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 5))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)

        actions = ttk.Frame(panel)
        actions.grid(row=0, column=0, sticky=tk.W)
        ttk.Button(actions, text="Tạo từ sợi và keo",
                   command=self.open_fiber_matrix_dialog).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(actions, text="Nhập thông số lớp",
                   command=self.open_manual_dialog).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(actions, text="Thư viện vật liệu",
                   command=self.open_library_dialog).pack(side=tk.LEFT)

        ttk.Label(panel, text="Danh sách lớp đã tạo:").grid(row=1, column=0, sticky=tk.W, pady=(12, 4))

        table = ttk.Frame(panel)
        table.grid(row=2, column=0, sticky=tk.NSEW)
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.ply_tree = ttk.Treeview(table, columns=[c[0] for c in PLY_COLUMNS],
                                     show="headings", selectmode="extended")
        for col, heading, width in PLY_COLUMNS:
            self.ply_tree.heading(col, text=heading)
            self.ply_tree.column(col, width=width, minwidth=40, anchor=tk.CENTER, stretch=True)
        self.ply_tree.grid(row=0, column=0, sticky=tk.NSEW)
        scroll = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self.ply_tree.yview)
        scroll.grid(row=0, column=1, sticky=tk.NS)
        self.ply_tree.configure(yscrollcommand=scroll.set)

        ttk.Button(panel, text="Xóa lớp đã chọn", command=self.delete_selected_plies).grid(
            row=3, column=0, sticky=tk.E, pady=(8, 0))

    def _next_ply_name(self):
        return f"Lớp {self._ply_counter + 1}"

    def open_fiber_matrix_dialog(self):
        PlyFromFiberMatrixDialog(self.root, self._next_ply_name(), self.add_ply)

    def open_manual_dialog(self):
        PlyManualDialog(self.root, self._next_ply_name(), self.add_ply)

    def open_library_dialog(self):
        MaterialLibraryDialog(self.root, self._next_ply_name(), self.add_ply)

    def add_ply(self, ply):
        self._ply_counter += 1
        iid = self.ply_tree.insert("", tk.END, values=(
            ply.name, f"{ply.thickness:.4g}", f"{ply.E1c:.4g}", f"{ply.E2c:.4g}",
            f"{ply.G12c:.4g}", f"{ply.nju12_c:.3g}", f"{ply.rho_c:.5g}", ply.source))
        self.plies[iid] = ply

    def delete_selected_plies(self):
        for iid in self.ply_tree.selection():
            self.ply_tree.delete(iid)
            self.plies.pop(iid, None)
            self.layup.remove_ply(iid)

    def ordered_plies(self):
        """Plies in the order shown in the left list: [(iid, Ply), ...]."""
        return [(iid, self.plies[iid]) for iid in self.ply_tree.get_children()]

    # ---------- Right: Tạo tấm ----------
    def _build_laminate_panel(self, main):
        panel = ttk.LabelFrame(main, text="Tạo tấm", padding=10)
        panel.grid(row=0, column=1, sticky=tk.NSEW, padx=(5, 0))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(0, weight=1)

        self.total_var = tk.StringVar()
        self.layup = LayupTable(panel, self.ordered_plies, self._update_total_thickness)
        self.layup.grid(row=0, column=0, sticky=tk.NSEW)

        info = ttk.Frame(panel)
        info.grid(row=1, column=0, sticky=tk.EW, pady=(8, 0))
        ttk.Label(info, textvariable=self.total_var, font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)
        self.h0_var = tk.StringVar(value="0")
        ttk.Entry(info, textvariable=self.h0_var, width=8).pack(side=tk.RIGHT)
        ttk.Label(info, text="h0 (mm)").pack(side=tk.RIGHT, padx=(0, 5))
        self._update_total_thickness()

        buttons = ttk.Frame(panel)
        buttons.grid(row=2, column=0, sticky=tk.EW, pady=(12, 0))
        ttk.Button(buttons, text="Cancel", command=self.cancel_laminate).pack(side=tk.RIGHT, padx=4)
        ttk.Button(buttons, text="Calculate", command=self.calculate_laminate).pack(side=tk.RIGHT, padx=4)
        self.result_window = None

    def _update_total_thickness(self):
        self.total_var.set(f"Tổng chiều dày: {self.layup.total_thickness():.4g} mm")

    def cancel_laminate(self):
        if len(self.layup.rows) > 1 and not messagebox.askyesno(
                "Cancel", "Xóa toàn bộ các lớp trong tấm?", parent=self.root):
            return
        self.layup.clear()
        if self.result_window is not None and self.result_window.winfo_exists():
            self.result_window.destroy()

    def calculate_laminate(self):
        exe = Path(__file__).parent / "laminate_calc.exe"
        if not exe.exists():
            messagebox.showerror("Error", f"laminate_calc.exe not found at:\n{exe}", parent=self.root)
            return
        try:
            layup = self.layup.get_layup()
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self.root)
            return
        if not layup:
            messagebox.showerror("Error", "Tấm chưa có lớp nào.", parent=self.root)
            return
        try:
            h0 = eval_expr(self.h0_var.get())
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
            messagebox.showerror("Error", "h0 không hợp lệ.", parent=self.root)
            return

        # Input format of laminate_calc.f90: "n h0" then one line per layer
        lines = [f"{len(layup)} {h0!r}"]
        for ply, angle in layup:
            lines.append(" ".join(repr(float(v)) for v in (
                ply.E1c, ply.E2c, ply.G12c, ply.nju12_c, angle, ply.thickness)))
        try:
            result = subprocess.run([str(exe)], input="\n".join(lines) + "\n",
                                    capture_output=True, text=True, cwd=str(exe.parent))
        except OSError as e:
            messagebox.showerror("Error", f"Cannot run laminate_calc.exe:\n{e}", parent=self.root)
            return
        try:
            values = [float(v) for v in result.stdout.split()]
        except ValueError:
            values = []
        if result.returncode != 0 or len(values) != 18:
            messagebox.showerror("Calculation error", result.stderr or result.stdout or "No output",
                                 parent=self.root)
            return
        A = [values[0:3], values[3:6], values[6:9]]
        D = [values[9:12], values[12:15], values[15:18]]
        self._show_laminate_results(layup, h0, A, D)

    def _show_laminate_results(self, layup, h0, A, D):
        if self.result_window is not None and self.result_window.winfo_exists():
            self.result_window.destroy()
        win = tk.Toplevel(self.root)
        win.title("Thông số tấm")
        win.resizable(False, False)
        win.transient(self.root)
        self.result_window = win
        win.vars = []

        main = ttk.Frame(win, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        total = sum(ply.thickness for ply, _ in layup)
        angles = "/".join(f"{a:g}" for _, a in layup)
        ttk.Label(main, text=f"Số lớp: {len(layup)}    Tổng chiều dày: {total:.4g} mm    "
                             f"h0 = {h0:g} mm").pack(anchor=tk.W)
        ttk.Label(main, text=f"Góc xếp (lớp 1 → {len(layup)}): [{angles}]").pack(anchor=tk.W, pady=(2, 0))

        mats = ttk.Frame(main)
        mats.pack(fill=tk.X, pady=(10, 0))
        for col, (title, M) in enumerate((("A - Độ cứng màng (N/m)", A),
                                          ("D - Độ cứng uốn (N·m)", D))):
            frame = ttk.LabelFrame(mats, text=title, padding=8)
            frame.grid(row=0, column=col, sticky=tk.N, padx=(0 if col == 0 else 10, 0))
            scale = max(abs(v) for r in M for v in r)
            for i, r in enumerate(M):
                for j, v in enumerate(r):
                    if abs(v) < 1e-9 * scale:  # round-off from the 0/90 transformation
                        v = 0.0
                    var = tk.StringVar(value=f"{v:.5g}")
                    win.vars.append(var)  # keep a reference, otherwise the cell shows empty
                    ttk.Entry(frame, textvariable=var, width=13, state="readonly",
                              justify=tk.RIGHT).grid(row=i, column=j, padx=2, pady=2)

        ttk.Button(main, text="Close", command=win.destroy).pack(anchor=tk.E, pady=(12, 0))


class LayupTable(ttk.Frame):
    """Scrollable table TT | Lớp | Góc xếp. A new empty row appears once the last row gets a ply.

    Delete a row with its ✕ button (or right-click). Up/Down in an angle cell moves between rows.
    """
    COLUMNS = [("TT", 45, 0), ("Lớp", 120, 1), ("Góc xếp (°)", 110, 0), ("", 34, 0)]  # text, minsize, weight
    ROW_WIDGETS = ("tt", "combo", "angle", "delete")

    def __init__(self, parent, get_plies, on_change):
        super().__init__(parent, relief=tk.SOLID, borderwidth=1)
        self.get_plies = get_plies
        self.on_change = on_change
        self.rows = []

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky=tk.EW)
        self._configure_columns(header)
        for c, (text, _, _) in enumerate(self.COLUMNS):
            ttk.Label(header, text=text, font=("TkDefaultFont", 9, "bold"), anchor=tk.CENTER).grid(
                row=0, column=c, sticky=tk.EW, padx=2, pady=4)
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(row=0, column=0, columnspan=2, sticky=tk.EW + tk.S)

        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.canvas.grid(row=1, column=0, sticky=tk.NSEW)
        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        scroll.grid(row=0, column=1, rowspan=2, sticky=tk.NS)
        self.canvas.configure(yscrollcommand=scroll.set)

        self.body = ttk.Frame(self.canvas)
        self._configure_columns(self.body)
        body_id = self.canvas.create_window((0, 0), window=self.body, anchor=tk.NW)
        self.body.bind("<Configure>",
                       lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(body_id, width=e.width))
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.menu = tk.Menu(self, tearoff=0)
        self._menu_row = None
        self.menu.add_command(label="Xóa hàng", command=lambda: self.delete_row(self._menu_row))

        self._add_row()

    def _configure_columns(self, frame):
        for c, (_, minsize, weight) in enumerate(self.COLUMNS):
            frame.columnconfigure(c, minsize=minsize, weight=weight)

    def _on_wheel(self, event):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(int(-event.delta / 120), "units")
        return "break"

    def _add_row(self):
        row = {"ply_iid": None}
        row["tt"] = ttk.Label(self.body, anchor=tk.CENTER)
        row["combo"] = ttk.Combobox(self.body, state="readonly",
                                    postcommand=lambda: self._fill_combo(row))
        row["combo"].bind("<<ComboboxSelected>>", lambda e: self._on_ply_selected(row))
        row["combo"].bind("<MouseWheel>", self._on_wheel)  # scroll the table, not the combobox
        row["angle_var"] = tk.StringVar()
        row["angle"] = tk.Entry(self.body,textvariable=row["angle_var"],
                                justify=tk.CENTER, width=10)
        row["angle_var"].trace_add("write", lambda *_: self._check_angle(row))
        row["angle"].bind("<Up>", lambda e: self._move_focus(row, -1))
        row["angle"].bind("<Down>", lambda e: self._move_focus(row, +1))
        row["delete"] = ttk.Button(self.body, text="✕", width=3, command=lambda: self.delete_row(row))
        for key in self.ROW_WIDGETS:
            row[key].bind("<Button-3>", lambda e, r=row: self._show_menu(e, r))
        self.rows.append(row)
        self._regrid()
        self.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _regrid(self):
        for i, row in enumerate(self.rows):
            row["tt"].config(text=str(i + 1))
            row["tt"].grid(row=i, column=0, sticky=tk.EW, padx=2, pady=2)
            row["combo"].grid(row=i, column=1, sticky=tk.EW, padx=2, pady=2)
            row["angle"].grid(row=i, column=2, sticky=tk.EW, padx=2, pady=2)
            row["delete"].grid(row=i, column=3, padx=2, pady=2)
            # The trailing empty row has nothing to delete
            if row is self.rows[-1] and row["ply_iid"] is None:
                row["delete"].grid_remove()

    def _move_focus(self, row, step):
        """Up/Down arrow in an angle cell: jump to the angle cell of the row above/below."""
        i = self.rows.index(row) + step
        if 0 <= i < len(self.rows):
            target = self.rows[i]["angle"]
            target.focus_set()
            target.select_range(0, tk.END)
            target.icursor(tk.END)
            self._scroll_into_view(target)
        return "break"

    def _scroll_into_view(self, widget):
        self.update_idletasks()
        total = self.body.winfo_height()
        if total <= 0:
            return
        y, h = widget.winfo_y(), widget.winfo_height()
        top, view = self.canvas.canvasy(0), self.canvas.winfo_height()
        if y < top:
            self.canvas.yview_moveto(y / total)
        elif y + h > top + view:
            self.canvas.yview_moveto((y + h - view) / total)

    def _fill_combo(self, row):
        row["combo"]["values"] = [ply.name for _, ply in self.get_plies()]

    def _on_ply_selected(self, row):
        idx = row["combo"].current()
        plies = self.get_plies()
        if idx < 0 or idx >= len(plies):
            return
        row["ply_iid"] = plies[idx][0]
        if row is self.rows[-1]:
            self._add_row()
        else:
            self._regrid()
        self.on_change()

    def _check_angle(self, row):
        text = row["angle_var"].get()
        try:
            ok = not text.strip() or isinstance(eval_expr(text), float)
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
            ok = False
        row["angle"].config(fg="black" if ok else "red")

    def _show_menu(self, event, row):
        self._menu_row = row
        self.menu.tk_popup(event.x_root, event.y_root)

    def delete_row(self, row):
        if row not in self.rows:
            return
        if row is self.rows[-1] and row["ply_iid"] is None:
            return  # keep the trailing empty row
        for key in self.ROW_WIDGETS:
            row[key].destroy()
        self.rows.remove(row)
        if not self.rows or self.rows[-1]["ply_iid"] is not None:
            self._add_row()
        self._regrid()
        self.on_change()

    def clear(self):
        """Remove all rows, leaving a single empty row."""
        for row in self.rows:
            for key in self.ROW_WIDGETS:
                row[key].destroy()
        self.rows = []
        self._add_row()
        self.on_change()

    def remove_ply(self, iid):
        """Drop rows that use a ply deleted from the left list."""
        for row in [r for r in self.rows if r["ply_iid"] == iid]:
            self.delete_row(row)

    def _ply_of(self, row):
        return dict(self.get_plies()).get(row["ply_iid"])

    def total_thickness(self):
        return sum(p.thickness for p in map(self._ply_of, self.rows) if p is not None)

    def get_layup(self):
        """Return [(Ply, angle_deg), ...] bottom to top; raise ValueError on a bad angle."""
        layup = []
        for i, row in enumerate(self.rows, start=1):
            ply = self._ply_of(row)
            if ply is None:
                continue
            try:
                angle = eval_expr(row["angle_var"].get())
            except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
                raise ValueError(f"Góc xếp không hợp lệ ở hàng {i}")
            layup.append((ply, angle))
        return layup


if __name__ == "__main__":
    root = tk.Tk()
    CompositeApp(root)
    root.mainloop()
