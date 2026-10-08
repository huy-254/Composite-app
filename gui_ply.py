import ast
import math
import operator
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from pathlib import Path

FIBER_PARAMS = [
    ("E1f - Longitudinal modulus (GPa)", "E1f"),
    ("E2f - Transverse modulus (GPa)", "E2f"),
    ("G12f - Shear modulus (GPa)", "G12f"),
    ("nju12_f - Poisson ratio", "nju12_f"),
    ("sLf_tens - Tensile strength (MPa)", "sLf_tens"),
    ("rho_f - Density (kg/m3)", "rho_f"),
    ("vf - Fiber volume fraction (0-1)", "vf"),
    ("phi - Fiber misalignment angle (rad)", "phi"),
]

MATRIX_PARAMS = [
    ("Em - Modulus (GPa)", "Em"),
    ("G12m - Shear modulus (GPa)", "G12m"),
    ("nju12_m - Poisson ratio", "nju12_m"),
    ("sLm_tens - Tensile strength (MPa)", "sLm_tens"),
    ("sLm_compr - Compressive strength (MPa)", "sLm_compr"),
    ("sLTm - Shear strength (MPa)", "sLTm"),
    ("rho_m - Density (kg/m3)", "rho_m"),
]

# Order must match the read statement in ply_calc.f90
INPUT_ORDER = ["E1f", "E2f", "G12f", "Em", "G12m", "vf", "sLf_tens", "sLm_tens",
               "phi", "sLm_compr", "sLTm", "rho_f", "rho_m", "nju12_f", "nju12_m"]

OUTPUT_PARAMS = [
    ("E1c (GPa)", "E1c"),
    ("E2c (GPa)", "E2c"),
    ("G12c (GPa)", "G12c"),
    ("nju12_c", "nju12_c"),
    ("sLc_tens (MPa)", "sLc_tens"),
    ("sLc_compr (MPa)", "sLc_compr"),
    ("sTc_tens (MPa)", "sTc_tens"),
    ("sTc_compr (MPa)", "sTc_compr"),
    ("sLTc (MPa)", "sLTc"),
    ("rho_c (kg/m3)", "rho_c"),
]


_BIN_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
            ast.Div: operator.truediv, ast.Pow: operator.pow}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_NAMES = {"pi": math.pi, "e": math.e}
_FUNCS = {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
          "exp": math.exp, "log": math.log, "deg2rad": math.radians}


def eval_expr(text):
    """Safely evaluate a numeric expression such as '2*pi/180' or '2.9e9/2/1.35'."""
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in _NAMES:
            return _NAMES[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](ev(node.operand))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in _FUNCS and len(node.args) == 1 and not node.keywords):
            return _FUNCS[node.func.id](ev(node.args[0]))
        raise ValueError("unsupported expression")

    return ev(ast.parse(text.strip().replace("^", "**"), mode="eval"))


class PlyPropertiesGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculate Ply Properties")
        self.root.resizable(False, False)

        self.exe_path = Path(__file__).parent / "ply_calc.exe"
        self.input_vars = {}
        self.output_vars = {}

        main = ttk.Frame(root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Input section: fiber (left) | matrix (right)
        inputs = ttk.Frame(main)
        inputs.pack(fill=tk.X)
        self._build_group(inputs, "Fiber", FIBER_PARAMS, 0)
        self._build_group(inputs, "Matrix", MATRIX_PARAMS, 1)

        # Output section
        results = ttk.LabelFrame(main, text="Composite ply properties", padding=8)
        results.pack(fill=tk.X, pady=(10, 0))
        half = (len(OUTPUT_PARAMS) + 1) // 2
        for i, (text, name) in enumerate(OUTPUT_PARAMS):
            r, c = i % half, (i // half) * 2
            ttk.Label(results, text=text).grid(row=r, column=c, sticky=tk.W, padx=(5, 8), pady=3)
            var = tk.StringVar(value="---")
            ttk.Entry(results, textvariable=var, width=16, state="readonly").grid(
                row=r, column=c + 1, sticky=tk.W, padx=(0, 20), pady=3)
            self.output_vars[name] = var

        self._build_buttons(main)

    def _build_buttons(self, main):
        # Buttons (bottom right): Calculate | Clear | Cancel
        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(buttons, text="Cancel", command=self.root.destroy).pack(side=tk.RIGHT, padx=4)
        ttk.Button(buttons, text="Clear", command=self.clear).pack(side=tk.RIGHT, padx=4)
        ttk.Button(buttons, text="Calculate", command=self.calculate).pack(side=tk.RIGHT, padx=4)
        return buttons

    def _build_group(self, parent, title, params, column):
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.grid(row=0, column=column, sticky=tk.N, padx=(0 if column == 0 else 10, 0))
        for r, (text, name) in enumerate(params):
            ttk.Label(frame, text=text).grid(row=r, column=0, sticky=tk.W, padx=5, pady=3)
            var = tk.StringVar()
            ttk.Entry(frame, textvariable=var, width=14).grid(row=r, column=1, padx=5, pady=3)
            self.input_vars[name] = var

    def calculate(self):
        """Run ply_calc.exe; return dict of results (GPa/MPa/kg/m3) or None on error."""
        if not self.exe_path.exists():
            messagebox.showerror("Error", f"ply_calc.exe not found at:\n{self.exe_path}",
                                 parent=self.root)
            return None

        values = []
        for name in INPUT_ORDER:
            try:
                val = eval_expr(self.input_vars[name].get())
                values.append(repr(val))
            except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
                messagebox.showerror("Error", f"Invalid or empty input: {name}", parent=self.root)
                return None

        try:
            result = subprocess.run(
                [str(self.exe_path)], input=" ".join(values) + "\n",
                capture_output=True, text=True, cwd=str(self.exe_path.parent))
        except OSError as e:
            messagebox.showerror("Error", f"Cannot run ply_calc.exe:\n{e}", parent=self.root)
            return None

        out = result.stdout.split()
        if result.returncode != 0 or len(out) != len(OUTPUT_PARAMS):
            messagebox.showerror("Calculation error", result.stderr or result.stdout or "No output",
                                 parent=self.root)
            return None

        results = {}
        for (_, name), value in zip(OUTPUT_PARAMS, out):
            val = float(value)
            results[name] = val
            self.output_vars[name].set(f"{val:.6g}")
        return results

    def clear(self):
        for var in self.input_vars.values():
            var.set("")
        for var in self.output_vars.values():
            var.set("---")


if __name__ == "__main__":
    root = tk.Tk()
    PlyPropertiesGUI(root)
    root.mainloop()
