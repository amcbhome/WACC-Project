import os
import pathlib
import subprocess
from jinja2 import Template

BASE = pathlib.Path(__file__).parent
TEX_TEMPLATE_FILE = BASE / "wacc_template.tex"

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
    equity_method: str,
    rf: float,
    mrp: float,
    beta: float,
    d0,
    growth,
    p0_equity,
    capm_company: str,
    forensic_data: dict | None = None,
    output_tex: str = "wacc_report.tex",
    output_pdf: str = "wacc_report.pdf",
    allow_compile: bool = False,
) -> str:
    """Render LaTeX report and optionally compile to PDF."""

    # Load LaTeX template
    with open(TEX_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())

    sources = ["Equity", "Preference", "Redeemable debt", "Irredeemable debt", "Bank loans"]
    costs = [equity_cost, pref_cost, red_cost, irred_cost, bank_cost]

    rows_bv = [{"source": s, "weight": w, "cost": c} for s, w, c in zip(sources, weights_BV, costs)]
    rows_mv = [{"source": s, "weight": w, "cost": c} for s, w, c in zip(sources, weights_MV, costs)]

    mv_contrib = [w * c * 100.0 for w, c in zip(weights_MV, costs)]
    mv_contrib_total = sum(mv_contrib)

    if forensic_data:
        residual_pct = (forensic_data["target_wacc"] - forensic_data["known_comp"]) * 100.0
        forensic_block = rf"""
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
        forensic_block = r"""
\section*{Forensic Analytics}
No forensic analysis was performed during this run. A reverse-solve section will appear here when the Forensic tool is used.
"""

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
        EQUITY_METHOD=equity_method,
        RF_PCT=f"{rf*100:.2f}\\%",
        MRP_PCT=f"{mrp*100:.2f}\\%",
        BETA_VAL=f"{beta:.2f}",
        D0_VAL=("N/A" if d0 is None else f"{d0:.4f}"),
        G_PCT=("N/A" if growth is None else f"{growth*100:.2f}\\%"),
        P0_EQUITY=("N/A" if p0_equity is None else f"{p0_equity:.2f}"),
        CAPM_COMPANY=(capm_company if capm_company else "—"),
        MV_CONTRIB=[{"source": s, "contrib": v, "weight": w, "cost": c}
                    for s, v, w, c in zip(sources, mv_contrib, weights_MV, costs)],
        MV_CONTRIB_TOTAL=mv_contrib_total,
        FORENSIC_BLOCK=forensic_block,
    )

    with open(output_tex, "w", encoding="utf-8") as f:
        f.write(tex)

    if not allow_compile:
        return output_tex

    try:
        basename = os.path.splitext(output_tex)[0]
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)
        subprocess.run(["biber", basename], check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", output_tex], check=True)
        pdf_path = f"{basename}.pdf"
        if os.path.exists(pdf_path):
            return pdf_path
    except Exception:
        pass

    return output_tex
