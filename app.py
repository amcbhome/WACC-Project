import streamlit as st
import pandas as pd

import wacc_module as wacc
from app_snippet_company_extract import infer_company_name
import report_generator as rg


# Page Setup
st.set_page_config(page_title="WACC Automation Tool", layout="centered")
st.title("📊 Weighted Average Cost of Capital Automation")


# ============================
# 1️⃣ Optional Company Upload
# ============================
uploaded = st.file_uploader(
    "Upload CSV/JSON containing a 'Company' field (optional):",
    type=["csv", "json"]
)

company_name = infer_company_name(uploaded)
st.write(f"Detected Company: **{company_name}**")

st.markdown("---")


# ============================
# 2️⃣ Global Input – Tax Rate
# ============================
tax_rate = st.number_input("Corporate Tax Rate (%)", value=30.0, min_value=0.0, max_value=100.0) / 100


# ============================
# 3️⃣ Input Panels by Instrument
# ============================

# ---- Equity ----
st.subheader("Equity (Ordinary Shares)")
D0 = st.number_input("Dividend Just Paid D₀ (£ per share)", value=0.23)
g = st.number_input("Annual Dividend Growth Rate g (%)", value=5.0) / 100
P0_equity = st.number_input("Market Price per Share (£)", value=4.17)

BV_equity = st.number_input("Book Value of Equity (£000)", value=13600.0)
MV_equity = st.number_input("Market Value of Equity (£000)", value=53376.0)


# ---- Preference Shares ----
st.subheader("Preference Shares")
Dp = st.number_input("Preference Dividend (£ per share)", value=0.08)
P0_pref = st.number_input("Market Price per Pref Share (£)", value=0.89)

BV_pref = st.number_input("Book Value (£000)", value=9000.0)
MV_pref = st.number_input("Market Value (£000)", value=8010.0)


# ---- Redeemable Debt ----
st.subheader("Redeemable Debt")
I_red = st.number_input("Annual Coupon (£)", value=5.0)
RV = st.number_input("Redemption Value (£)", value=100.0)
n = st.number_input("Years to Redemption", value=6, min_value=1)

P0_red = st.number_input("Market Price per £100 Nominal (£)", value=96.0)

BV_red = st.number_input("Book Value (£000)", value=4650.0)
MV_red = st.number_input("Market Value (£000)", value=4464.0)


# ---- Irredeemable Debt ----
st.subheader("Irredeemable Debt")
I_irred = st.number_input("Annual Coupon (£)", value=9.0)
P0_irred = st.number_input("Market Price per £100 Nominal (£)", value=108.0)

BV_irred = st.number_input("Book Value (£000)", value=8500.0)
MV_irred = st.number_input("Market Value (£000)", value=9180.0)


# ---- Bank Loans ----
st.subheader("Bank Loans")
interest_bank = st.number_input("Bank Loan Interest Rate (%)", value=7.0) / 100

BV_bank = st.number_input("Book Value (£000)", value=3260.0)
MV_bank = st.number_input("Market Value (£000)", value=3260.0)


# ============================
# 4️⃣ WACC Calculations
# ============================

# Component Costs
Re = wacc.cost_of_equity_dgm(D0, g, P0_equity)
Rp = wacc.cost_of_preference_shares(Dp, P0_pref)
Rd_red = wacc.cost_of_redeemable_debt(I_red, P0_red, RV, n, tax_rate)
Rd_irred = wacc.cost_of_irredeemable_debt(I_irred, P0_irred, tax_rate)
Rd_bank = wacc.cost_of_bank_loans(interest_bank, tax_rate)
costs = [Re, Rp, Rd_red, Rd_irred, Rd_bank]

# Weights
BV_values = [BV_equity, BV_pref, BV_red, BV_irred, BV_bank]
MV_values = [MV_equity, MV_pref, MV_red, MV_irred, MV_bank]

weights_BV = wacc.calculate_weights(BV_values)
weights_MV = wacc.calculate_weights(MV_values)

# WACC
WACC_BV = wacc.calculate_wacc(costs, weights_BV)
WACC_MV = wacc.calculate_wacc(costs, weights_MV)


# ============================
# 5️⃣ Display Results
# ============================

st.markdown("---")
st.subheader("✅ Summary of WACC Results")

results_df = pd.DataFrame({
    "Source": ["Equity", "Preference", "Redeemable Debt", "Irredeemable Debt", "Bank Loans"],
    "Cost (%)": [c * 100 for c in costs],
    "Weight (Book)": weights_BV,
    "Weight (Market)": weights_MV
})

st.dataframe(results_df.style.format({"Cost (%)": "{:.2f}", "Weight (Book)": "{:.4f}", "Weight (Market)": "{:.4f}"}))

st.metric("WACC based on Book Values", f"{WACC_BV*100:.2f}%")
st.metric("WACC based on Market Values", f"{WACC_MV*100:.2f}%")


# ============================
# 6️⃣ Generate WACC Report (PDF)
# ============================

st.markdown("---")
if st.button("📄 Generate LaTeX Report"):
    tex_or_pdf_path = rg.build_wacc_report(
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
        BV_values=BV_values,
        MV_values=MV_values,
        allow_compile=False  # Set True if LaTeX available
    )
    st.success(f"Report generated! File available: {tex_or_pdf_path}")
    st.info("Upload the generated .tex to Overleaf to produce a PDF.")
