"""
Generates a LaTeX WACC report from template + input values.
Uses Harvard citation format with biber when allow_compile=True.
"""

import os
import subprocess
from jinja2 import Template

TEX_TEMPLATE_FILE = "wacc_template.tex"
BIB_FILE = "references.bib"


def build_wacc_report(
    company_name: str,
    tax_rate: float,
    equity_cost: float,
    pref_cost: float,
    red_cost: float,
    irred_cost: float,
    bank_cost: float,
    weights_BV,
    weights_MV,
    WACC_BV: float,
    WACC_MV: float,
    BV_values=None,
    MV_values=None,
    output_tex: str = "wacc_report.tex",
    output_pdf: str = "wacc_report.pdf",
    allow_compile: bool = False  # default: tex only
) -> str:

    if BV_values is None:
        BV_values = [0,0,0,0,0]
    if MV_values is None:
        MV_values = [0,0,0,0,0]

    # Load LaTeX Template
    with open(TEX_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())

    sources = ["Equity", "Preference", "Redeemable debt", "Irredeemable debt", "Bank loans"]
    rows_bv = [
        {"source": s, "weight": w, "cost": c}
        for s, w, c in zip(sources, weights_BV,
                           [equity_cost, pref_cost, red_cost, irred_cost, bank_cost])
    ]
    rows_mv = [
        {"source": s, "weight": w, "cost": c}
        for s, w, c in zip(sources, weights_MV,
                           [equity_cost, pref_cost, red_cost, irred_cost, bank_cost])
    ]

    tex_content = tmpl.render(
        COMPANY_NAME=company_name,
        TAX_RATE=f"{tax_rate*100:.0f}\\%",
        EQUITY_COST_PCT=f"{equity_cost*100:.2f}\\%",
        PREF_COST_PCT=f"{pref_cost*100:.2f}\\%",
        RED_COST_PCT=f"{red_cost*100:.2f}\\%",
        IRRED_COST_PCT=f"{irred_cost*100:.2f}\\%",
        BANK_COST_PCT=f"{bank_cost*100:.2f}\\%",
        WACC_BV_PCT=f"{WACC_BV*100:.2f}",
        WACC_MV_PCT=f"{WACC_MV*100:.2f}",
        ROWS_BV=rows_bv,
        ROWS_MV=rows_mv,
        BV_TOTAL_K=f"{sum(BV_values):,.0f}",
        MV_TOTAL_K=f"{sum(MV_values):,.0f}",
    )

    # Write final LaTeX file
    with open(output_tex, "w", encoding="utf-8") as f:
        f.write(tex_content)

    # If direct PDF building not requested → return .tex
    if not allow_compile:
        return output_tex

    # Try to compile PDF locally
    try:
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)
        subprocess.run(["biber", os.path.splitext(output_tex)[0]], check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)

        if os.path.exists(output_pdf):
            return output_pdf
    except Exception as e:
        print("PDF compilation failed:", e)

    return output_tex
