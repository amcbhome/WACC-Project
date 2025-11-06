import os
import pathlib
import subprocess
from jinja2 import Template

BASE = pathlib.Path(__file__).parent
TEX_TEMPLATE_FILE = BASE / "wacc_template.tex"
BIB_FILE = BASE / "references.bib"

def build_wacc_report(
    company_name,
    tax_rate,
    equity_cost,
    pref_cost,
    red_cost,
    irred_cost,
    bank_cost,
    bv_weights,
    mv_weights,
    ROWS_BV,
    ROWS_MV,
    MV_CONTRIB,
    MV_CONTRIB_TOTAL,
    equity_method,
    forensic_data=None
):


    # Read template
    with open(TEX_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())

    sources = ["Equity", "Preference", "Redeemable debt", "Irredeemable debt", "Bank loans"]

    # Rows for Step Two/Three tables
    rows_bv = [{"source": s, "weight": w, "cost": c} for s, w, c in zip(sources, weights_BV, [equity_cost, pref_cost, red_cost, irred_cost, bank_cost])]
    rows_mv = [{"source": s, "weight": w, "cost": c} for s, w, c in zip(sources, weights_MV, [equity_cost, pref_cost, red_cost, irred_cost, bank_cost])]

    # Market-basis contributions (for WACC Reconciliation table)
    contrib_mv = [w * c * 100.0 for w, c in zip(weights_MV, [equity_cost, pref_cost, red_cost, irred_cost, bank_cost])]
    total_mv_contrib = sum(contrib_mv)  # ≈ WACC_MV*100 using full precision

    # Forensic LaTeX block + reconciliation (4dp)
    if forensic_data:
        residual_pct = (forensic_data["target_wacc"] - forensic_data["known_comp"]) * 100.0
        tex_forensic = rf"""
\section*{{Forensic Analytics}}
Missing Cost: \textbf{{{forensic_data["missing_choice"]}}} \\
Basis used: \textbf{{{forensic_data["basis"]}}} weights \\
Target WACC: \textbf{{{forensic_data["target_wacc"]*100:.4f}\%}}

\[
c_x = \frac{{{forensic_data["target_wacc"]:.6f} - {forensic_data["known_comp"]:.6f}}}{{{forensic_data["missing_weight"]:.6f}}}
= {forensic_data["solved_cost"]:.6f}
\]

\subsection*{{Forensic Reconciliation}}
\begin{center}
\begin{tabular}{l r}
\toprule
\textbf{{Item}} & \textbf{{Value}} \\
\midrule
Known contribution (Σ wᵢcᵢ, i≠x) & {forensic_data["known_comp"]*100:.4f}\% \\
Residual required & {residual_pct:.4f}\% \\
Missing weight (wₓ) & {forensic_data["missing_weight"]:.4f} \\
Implied missing cost (cₓ) & {forensic_data["solved_cost"]*100:.4f}\% \\
Target WACC & {forensic_data["target_wacc"]*100:.4f}\% \\
\bottomrule
\end{tabular}
\end{center}
"""
    else:
        tex_forensic = r"""
\section*{Forensic Analytics}
No forensic analysis was performed during this run. A reverse-solve section will appear here when the Forensic tool is used.
"""

    # Render LaTeX
    tex = tmpl.render(
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
        # Equity method block
        EQUITY_METHOD=equity_method,
        RF_PCT=f"{rf*100:.2f}\\%",
        MRP_PCT=f"{mrp*100:.2f}\\%",
        BETA_VAL=f"{beta:.2f}",
        D0_VAL=("N/A" if d0 is None else f"{d0:.4f}"),
        G_PCT=("N/A" if growth is None else f"{growth*100:.2f}\\%"),
        P0_EQUITY=("N/A" if p0_equity is None else f"{p0_equity:.2f}"),
        CAPM_COMPANY=(capm_company if capm_company else "—"),
        # Reconciliation data (Market basis table)
        MV_CONTRIB=[{"source": s, "contrib": v, "weight": w, "cost": c} for s, v, w, c in zip(sources, contrib_mv, weights_MV, [equity_cost, pref_cost, red_cost, irred_cost, bank_cost])],
        MV_CONTRIB_TOTAL=total_mv_contrib,
        FORENSIC_BLOCK=tex_forensic,
    )

    # Write LaTeX file
    with open(output_tex, "w", encoding="utf-8") as f:
        f.write(tex)

    if not allow_compile:
        return output_tex

    try:
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)
        subprocess.run(["biber", os.path.splitext(output_tex)[0]], check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)
        if os.path.exists(output_pdf):
            return output_pdf
    except Exception:
        pass

    return output_tex

