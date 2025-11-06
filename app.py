import streamlit as st
import pandas as pd

import wacc_module as wacc
import report_generator as rg

st.set_page_config(page_title="WACC Automation Tool", layout="centered")
st.title("📊 Weighted Average Cost of Capital Automation")

# Tabs
tab1, tab2 = st.tabs(["📊 WACC Calculator", "🔍 Forensic Analytics"])

# ──────────────────────────────────────────────
# Constants / Defaults
# ──────────────────────────────────────────────
DEFAULT_BOE_RATE = 0.050   # 5.00% (editable in UI)
DEFAULT_MRP      = 0.055   # 5.50% (your choice A)

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
# TAB 1 — WACC CALCULATOR
# ──────────────────────────────────────────────
with tab1:
    # Company
    company_name = st.text_input("Company Name", value="Untitled Company")
    st.markdown("---")

    # Global input
    tax_rate = st.number_input("Corporate Tax Rate (%)", value=30.0, min_value=0.0, max_value=100.0) / 100.0

    # Cost of Equity method
    st.subheader("Cost of Equity Method")
    equity_method = st.radio(
        "Choose method:",
        ["CAPM (uses Beta)", "Dividend Growth Model (DGM)"],
        index=0
    )

    if equity_method.startswith("CAPM"):
        st.caption("CAPM:  Rₑ = Rf + β × MRP")
        rf = st.number_input("Risk-free rate Rf (%) — Bank of England base rate", value=DEFAULT_BOE_RATE * 100.0) / 100.0
        mrp = st.number_input("Market Risk Premium MRP (%)", value=DEFAULT_MRP * 100.0) / 100.0
        ftse_choice = st.selectbox("Select FTSE company for Beta (β)", list(FTSE10_BETAS.keys()), index=0)
        beta = st.number_input("Beta (β) — auto-filled (editable)", value=float(FTSE10_BETAS[ftse_choice]), step=0.01)
        Re = rf + beta * mrp
        D0 = None; g = None; P0_equity = None  # placeholders for report
    else:
        st.caption("DGM:  Rₑ = D₁/P₀ + g,  with  D₁ = D₀(1+g)")
        D0 = st.number_input("Dividend Just Paid D₀ (£ per share)", value=0.23)
        g  = st.number_input("Annual Dividend Growth Rate g (%)", value=5.0) / 100.0
        P0_equity = st.number_input("Market Price per Share P₀ (£)", value=4.17)
        Re = wacc.cost_of_equity_dgm(D0, g, P0_equity)
        rf = DEFAULT_BOE_RATE; mrp = DEFAULT_MRP; ftse_choice = ""; beta = 0.0

    # Other sources
    st.subheader("Preference Shares")
    Dp = st.number_input("Preference Dividend (£ per share)", value=0.08)
    P0_pref = st.number_input("Market Price per Pref Share (£)", value=0.89)

    st.subheader("Redeemable Debt")
    I_red = st.number_input("Annual Coupon (£, per £100 nominal)", value=5.0)
    RV = st.number_input("Redemption Value (£)", value=100.0)
    n  = st.number_input("Years to Redemption", value=6, min_value=1)
    P0_red = st.number_input("Market Price per £100 Nominal (£)", value=96.0)

    st.subheader("Irredeemable Debt")
    I_irred = st.number_input("Annual Coupon (£, per £100 nominal)", value=9.0)
    P0_irred = st.number_input("Market Price per £100 Nominal (£)", value=108.0)

    st.subheader("Bank Loans")
    interest_bank = st.number_input("Bank Loan Interest Rate i (%)", value=7.0) / 100.0

    # Capital structure values (weights)
    st.markdown("### Capital Structure (Book & Market for weights)")
    BV_equity = st.number_input("Book Value of Equity (£000)", value=13600.0)
    MV_equity = st.number_input("Market Value of Equity (£000)", value=53376.0)
    BV_pref   = st.number_input("Book Value of Preference (£000)", value=9000.0)
    MV_pref   = st.number_input("Market Value of Preference (£000)", value=8010.0)
    BV_red    = st.number_input("Book Value of Redeemable Debt (£000)", value=4650.0)
    MV_red    = st.number_input("Market Value of Redeemable Debt (£000)", value=4464.0)
    BV_irred  = st.number_input("Book Value of Irredeemable Debt (£000)", value=8500.0)
    MV_irred  = st.number_input("Market Value of Irredeemable Debt (£000)", value=9180.0)
    BV_bank   = st.number_input("Book Value of Bank Loans (£000)", value=3260.0)
    MV_bank   = st.number_input("Market Value of Bank Loans (£000)", value=3260.0)

    # Component costs (after tax where applicable)
    Rp      = wacc.cost_of_preference_shares(Dp, P0_pref)
    Rd_red  = wacc.cost_of_redeemable_debt(I_red, P0_red, RV, n, tax_rate)
    Rd_irred= wacc.cost_of_irredeemable_debt(I_irred, P0_irred, tax_rate)
    Rd_bank = wacc.cost_of_bank_loans(interest_bank, tax_rate)
    costs   = [Re, Rp, Rd_red, Rd_irred, Rd_bank]

    # Weights
    BV_values   = [BV_equity, BV_pref, BV_red, BV_irred, BV_bank]
    MV_values   = [MV_equity, MV_pref, MV_red, MV_irred, MV_bank]
    weights_BV  = wacc.calculate_weights(BV_values)
    weights_MV  = wacc.calculate_weights(MV_values)

    # WACC results
    WACC_BV = wacc.calculate_wacc(costs, weights_BV)
    WACC_MV = wacc.calculate_wacc(costs, weights_MV)

    # Display results
    st.markdown("---")
    st.subheader("✅ Summary of WACC Results")
    results_df = pd.DataFrame({
        "Source": ["Equity", "Preference", "Redeemable Debt", "Irredeemable Debt", "Bank Loans"],
        "Cost (%)": [c * 100 for c in costs],
        "Weight (Book)": weights_BV,
        "Weight (Market)": weights_MV
    })
    st.dataframe(results_df.style.format({
        "Cost (%)": "{:.2f}", "Weight (Book)": "{:.4f}", "Weight (Market)": "{:.4f}"
    }))
    st.metric("WACC (Book Values)", f"{WACC_BV*100:.2f}%")
    st.metric("WACC (Market Values)", f"{WACC_MV*100:.2f}%")

    # Generate LaTeX (includes reconciliation + optional forensic)
    st.markdown("---")
    if st.button("📄 Generate LaTeX Report"):
        forensic_data = st.session_state.get("forensic", None)
        tex_path = rg.build_wacc_report(
            company_name=company_name,
            tax_rate=tax_rate,
            equity_cost=Re,
            pref_cost=Rp,
            red_cost=Rd_red,
            irred_cost=Rd_irred,
            bank_cost=Rd_bank,
            weights_BV=weights_BV,
            weights_MV=weights_MV,
            WACC_BV=WACC_BV,
            WACC_MV=WACC_MV,
            equity_method=("CAPM" if equity_method.startswith("CAPM") else "DGM"),
            rf=rf, mrp=mrp, beta=beta,
            d0=D0, growth=g, p0_equity=P0_equity,
            capm_company=ftse_choice,
            forensic_data=forensic_data,
            allow_compile=False
        )
        st.success("✅ LaTeX report generated!")
        with open(tex_path, "rb") as f:
            st.download_button("⬇️ Download LaTeX (.tex)", f, "wacc_report.tex")

    st.info("📌 Compile the downloaded .tex in Overleaf to generate the PDF.")

# ──────────────────────────────────────────────
# TAB 2 — FORENSIC ANALYTICS
# ──────────────────────────────────────────────
with tab2:
    st.subheader("🔍 Forensic Accounting Tool")

    missing_choice = st.selectbox(
        "Which cost is missing?",
        ["Cost of Equity", "Cost of Preference Shares", "Cost of Redeemable Debt", "Cost of Irredeemable Debt", "Cost of Bank Loans"]
    )
    forensic_basis = st.radio("Forensic WACC Basis:", ["Market", "Book"])
    default_target = WACC_MV * 100 if forensic_basis == "Market" else WACC_BV * 100
    target_wacc = st.number_input("Target WACC (%)", value=float(f"{default_target:.2f}")) / 100.0

    if st.button("🔎 Run Forensic Solver"):
        idx = ["Cost of Equity","Cost of Preference Shares","Cost of Redeemable Debt","Cost of Irredeemable Debt","Cost of Bank Loans"].index(missing_choice)
        weights = weights_MV if forensic_basis == "Market" else weights_BV
        known_costs = [Re, Rp, Rd_red, Rd_irred, Rd_bank]
        known_costs[idx] = 0.0  # zero out missing

        known_comp = sum(c * w for c, w in zip(known_costs, weights))
        missing_weight = weights[idx]

        if missing_weight == 0:
            st.error("Missing component has zero financing weight → cannot solve.")
        else:
            solved_cost = (target_wacc - known_comp) / missing_weight
            st.success(f"Solved {missing_choice}: **{solved_cost*100:.4f}%**")  # 4dp

            # Store for LaTeX integration
            st.session_state["forensic"] = {
                "missing_choice": missing_choice,
                "solved_cost": solved_cost,
                "target_wacc": target_wacc,
                "basis": forensic_basis,
                "known_comp": known_comp,
                "missing_weight": missing_weight,
            }

            st.caption("Using:  WACC = Σ(wᵢ × cᵢ)  ⇒  cₓ = (WACC − Σ wᵢcᵢ for i≠x) / wₓ  (shown to 4dp)")
