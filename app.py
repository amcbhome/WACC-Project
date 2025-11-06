import streamlit as st
import pandas as pd
import math

import wacc_module as wacc

st.set_page_config(page_title="WACC Calculator", layout="wide")
st.title("WACC Calculator")
st.caption("Automated Cost of Capital & Forensic Solver — inputs in the sidebar, results below.")

# ──────────────────────────────────────────────
# Defaults
# ──────────────────────────────────────────────
DEFAULT_BOE_RATE = 0.050   # 5.00%
DEFAULT_MRP      = 0.055   # 5.50%

FTSE10_BETAS = {
    "Tesco plc": 0.67,
    "BP plc": 1.15,
    "Vodafone Group plc": 0.72,
    "Lloyds Banking Group plc": 1.25,
    "Rio Tinto plc": 1.10,
    "easyJet plc": 1.75,
    "Diageo plc": 0.66,
    "Barclays plc": 1.38,
    "Shell plc": 1.05,
    "Aviva plc": 0.90,
}

# ──────────────────────────────────────────────
# Sidebar with expanders (inputs)
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("Inputs")
    
    with st.expander("📌 Company & Global", expanded=True):
        company_name = st.text_input("Company Name", value="Untitled Company")
        tax_rate = st.number_input("Corporate Tax Rate (%)", value=30.0, min_value=0.0, max_value=100.0) / 100.0

    with st.expander("📌 Cost of Equity", expanded=True):
        equity_method = st.radio("Method", ["CAPM (uses Beta)", "Dividend Growth Model (DGM)"], index=0)
        
        if equity_method.startswith("CAPM"):
            rf = st.number_input("Risk-free rate Rf (%) — Bank of England base rate",
                                 value=DEFAULT_BOE_RATE*100.0) / 100.0
            mrp = st.number_input("Market Risk Premium MRP (%)", value=DEFAULT_MRP*100.0) / 100.0
            
            ftse_choice = st.selectbox("Select FTSE company for Beta (β)", list(FTSE10_BETES.keys()), index=0)
            beta = st.number_input("Beta (β) — auto-filled (editable)",
                                   value=float(FTSE10_BETAS[ftse_choice]), step=0.01)

            Re = rf + beta * mrp
            D0 = None; g = None; P0_equity = None
        
        else:
            D0 = st.number_input("Dividend Just Paid (D₀) £", value=0.23, min_value=0.0)
            g  = st.number_input("Growth Rate g (%)", value=5.0) / 100.0
            P0_equity = st.number_input("Price per Share (P₀) £", value=4.17, min_value=0.0001)

            Re = wacc.cost_of_equity_dgm(D0, g, P0_equity)
            rf = DEFAULT_BOE_RATE; mrp = DEFAULT_MRP; beta = 0.0; ftse_choice = ""

    with st.expander("📌 Preference Shares", expanded=False):
        Dp = st.number_input("Preference Dividend (£ per share)", value=0.08, min_value=0.0)
        P0_pref = st.number_input("Market Price per Pref Share (£)", value=0.89, min_value=0.0001)

    with st.expander("📌 Redeemable Debt", expanded=False):
        I_red = st.number_input("Annual Coupon (per £100 nominal)", value=5.0, min_value=0.0)
        RV = st.number_input("Redemption Value (£)", value=100.0, min_value=0.0)
        n  = st.number_input("Years to Redemption", value=6, min_value=1, step=1)
        P0_red = st.number_input("Market Price (£ per £100 nominal)", value=96.0, min_value=0.0001)

    with st.expander("📌 Irredeemable Debt", expanded=False):
        I_irred = st.number_input("Annual Coupon (£, per £100 nominal)", value=9.0, min_value=0.0)
        P0_irred = st.number_input("Market Price (£ per £100 nominal)", value=108.0, min_value=0.0001)

    with st.expander("📌 Bank Loans", expanded=False):
        interest_bank = st.number_input("Bank Loan Interest Rate (%)", value=7.0, min_value=0.0) / 100.0

    with st.expander("📌 Capital Structure Values (£000)", expanded=True):
        BV_equity = st.number_input("Book Value: Equity", value=13600.0, min_value=0.0)
        MV_equity = st.number_input("Market Value: Equity", value=53376.0, min_value=0.0)

        BV_pref   = st.number_input("Book Value: Preference Shares", value=9000.0, min_value=0.0)
        MV_pref   = st.number_input("Market Value: Preference Shares", value=8010.0, min_value=0.0)

        BV_red    = st.number_input("Book Value: Redeemable Debt", value=4650.0, min_value=0.0)
        MV_red    = st.number_input("Market Value: Redeemable Debt", value=4464.0, min_value=0.0)

        BV_irred  = st.number_input("Book Value: Irredeemable Debt", value=8500.0, min_value=0.0)
        MV_irred  = st.number_input("Market Value: Irredeemable Debt", value=9180.0, min_value=0.0)

        BV_bank   = st.number_input("Book Value: Bank Loans", value=3260.0, min_value=0.0)
        MV_bank   = st.number_input("Market Value: Bank Loans", value=3260.0, min_value=0.0)

    with st.expander("📌 Forensic Solver", expanded=False):
        forensic_enable = st.checkbox("Enable Forensic Solver", value=False)
        missing_choice = st.selectbox(
            "Missing component (solve for its cost):",
            ["Cost of Equity", "Cost of Preference Shares", "Cost of Redeemable Debt", "Cost of Irredeemable Debt", "Cost of Bank Loans"]
        )
        forensic_basis = st.radio("Use which weights?", ["Market", "Book"], horizontal=True)
        target_wacc_pct = st.number_input("Target WACC (%)", value=9.40,
                                         help="Enter your expected WACC to reverse-engineer the missing cost.")
        run_forensic = st.button("Run Forensic Solver")

# Calculations
Rp      = wacc.cost_of_preference_shares(Dp, P0_pref)
Rd_red  = wacc.cost_of_redeemable_debt(I_red, P0_red, RV, n, tax_rate)
Rd_irred= wacc.cost_of_irredeemable_debt(I_irred, P0_irred, tax_rate)
Rd_bank = wacc.cost_of_bank_loans(interest_bank, tax_rate)

costs   = [Re, Rp, Rd_red, Rd_irred, Rd_bank]
sources = ["Equity", "Preference", "Redeemable Debt", "Irredeemable Debt", "Bank Loans"]

BV_values = [BV_equity, BV_pref, BV_red, BV_irred, BV_bank]
MV_values = [MV_equity, MV_pref, MV_red, MV_irred, MV_bank]

weights_BV = wacc.calculate_weights(BV_values)
weights_MV = wacc.calculate_weights(MV_values)

WACC_BV = wacc.calculate_wacc(costs, weights_BV)
WACC_MV = wacc.calculate_wacc(costs, weights_MV)

# Main output
st.subheader("Results")
results_df = pd.DataFrame({
    "Source": sources,
    "Cost (%)": [c * 100 for c in costs],
    "Weight (Book)": weights_BV,
    "Weight (Market)": weights_MV
})
st.dataframe(results_df.style.format({
    "Cost (%)": "{:.2f}",
    "Weight (Book)": "{:.4f}",
    "Weight (Market)": "{:.4f}"
}), use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.metric("WACC (Book)", f"{WACC_BV*100:.2f}%")
with c2:
    st.metric("WACC (Market)", f"{WACC_MV*100:.2f}%")

st.markdown("---")

# Forensic solver
if forensic_enable and run_forensic:
    weights = weights_MV if forensic_basis == "Market" else weights_BV
    idx = ["Cost of Equity", "Cost of Preference Shares", "Cost of Redeemable Debt", "Cost of Irredeemable Debt", "Cost of Bank Loans"].index(missing_choice)
    
    known_costs = costs.copy()
    known_costs[idx] = 0.0
    
    known_comp = sum(c * w for c, w in zip(known_costs, weights))
    target_wacc = target_wacc_pct / 100.0
    missing_weight = weights[idx]

    st.subheader("🔍 Forensic Solver Result")
    if missing_weight == 0:
        st.error("Cannot solve because the missing component has zero weight in the selected basis.")
    else:
        solved_cost = (target_wacc - known_comp) / missing_weight
        st.success(f"Implied {missing_choice}: **{solved_cost*100:.4f}%**")

        contrib_rows = []
        for s, cst, wgt in zip(sources, known_costs, weights):
            contrib_rows.append({
                "Source": s,
                "Weight": f"{wgt:.4f}",
                "Cost (%)": f"{cst*100:.2f}",
                "Contribution (%)": f"{(cst*wgt)*100:.4f}"
            })

        known_total = sum((cst*wgt)*100 for cst, wgt in zip(known_costs, weights))
        residual = (target_wacc - known_comp) * 100

        recon_df = pd.DataFrame(contrib_rows)
        st.write("**Forensic Reconciliation (selected basis)**")
        st.dataframe(recon_df, use_container_width=True)
        st.write(f"**Known total contribution:** {known_total:.4f}%")
        st.write(f"**Residual required:** {residual:.4f}%")
        st.write(f"**Missing weight (wₓ):** {missing_weight:.4f}")
        st.write(f"**Implied missing cost (cₓ):** {solved_cost*100:.4f}%")
        st.write(f"**Target WACC:** {target_wacc*100:.4f}%")

st.markdown("---")
st.info("ℹ️ LaTeX report generation is temporarily disabled to keep deployment stable.\nEnable anytime on request.")
