import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# ==================================================
# PAY MATRICES (Old, New)
# ==================================================

PAY_MATRIX = {
    6600: [
        (73700, 76500), (76000, 78800), (78300, 81200), (80700, 83700),
        (83200, 86300), (85700, 88900), (88300, 91600), (91000, 94400),
        (93800, 97300), (96700, 100300), (99700, 103400), (102700, 106600),
        (105800, 109800), (109000, 113100), (112300, 116500),
        (115700, 120000), (119200, 123600), (122800, 127400),
        (126500, 131300), (130300, 135300), (134300, 139400),
        (138400, 143600), (142600, 148000), (146900, 152500),
        (151400, 157100), (156000, 161900), (160700, 166800),
        (165600, 171900)
    ],
    7600: [
        (96800, 102600), (99800, 105700), (102800, 108900),
        (105900, 112200), (109100, 115600), (112400, 119100),
        (115800, 122700), (119300, 126400), (122900, 130200),
        (126600, 134200), (130400, 138300), (134400, 142500),
        (138500, 146800), (142700, 151300), (147000, 155900),
        (151500, 160600), (156100, 165500), (160800, 170500),
        (165700, 175700), (170700, 181000), (175900, 186500),
        (181200, 192100)
    ]
}

# ==================================================
# DA HISTORY (CORRECT – DATE BASED)
# ==================================================

DA_HISTORY = [
    (date(2020, 1, 1), 0.10),
    (date(2021, 1, 1), 0.13),
    (date(2023, 3, 1), 0.16),
    (date(2024, 1, 1), 0.20),
    (date(2024, 4, 1), 0.24),
    (date(2025, 4, 1), 0.28),
]

def get_da(d):
    da = DA_HISTORY[0][1]
    for eff, val in DA_HISTORY:
        if eff <= d:
            da = val
        else:
            break
    return da

def find_step(gp, basic):
    for i, (old_b, _) in enumerate(PAY_MATRIX[gp]):
        if old_b == basic:
            return i
    raise ValueError(f"Basic {basic} not found in GP {gp}")

# ==================================================
# STREAMLIT UI
# ==================================================

st.title("📊 Salary Arrear Calculator (ROPA 2020 Revision for Grade 9 and 10)")

col1, col2 = st.columns(2)

with col1:
    initial_gp = st.selectbox("Initial Grade Pay", [6600, 7600])
    initial_basic = st.number_input(
        "Basic Pay as on Jan-2020 (OLD BASIC)",
        step=100
    )

with col2:
    increment_month = st.selectbox("Increment Month", list(range(1, 13)))
    arrear_upto = st.text_input(
        "Calculate arrear upto (YYYYMM)",
        value="202602"
    )

promotion_input = st.text_input(
    "Promotion Month (YYYYMM) – Optional",
    help="On promotion GP becomes 7600 and basic resets to 102600"
)

# ==================================================
# CALCULATION
# ==================================================

if st.button("Generate Arrear Report"):

    start_date = date(2020, 1, 1)
    end_date = date(int(arrear_upto[:4]), int(arrear_upto[4:]), 1)

    promotion_date = None
    if promotion_input.strip():
        promotion_date = date(int(promotion_input[:4]), int(promotion_input[4:]), 1)

    current = start_date
    current_gp = initial_gp
    step = find_step(current_gp, initial_basic)
    promoted = False

    rows = []
    total_arrear = 0

    while current <= end_date:

        # Promotion
        if promotion_date and current == promotion_date and not promoted:
            current_gp = 7600
            step = 0   # 102600 is NEW BASIC at step 0
            promoted = True

        old_basic, new_basic = PAY_MATRIX[current_gp][step]
        da = get_da(current)

        old_salary = round(old_basic * (1 + da), 2)
        new_salary = round(new_basic * (1 + da), 2)
        arrear = round(new_salary - old_salary, 2)

        total_arrear += arrear

        rows.append([
            current.strftime("%b-%Y"),
            current_gp,
            old_basic,
            new_basic,
            int(da * 100),
            old_salary,
            new_salary,
            arrear
        ])

        # Increment
        if current.month == increment_month and current.year > 2020:
            step = min(step + 1, len(PAY_MATRIX[current_gp]) - 1)

        current += relativedelta(months=1)

    df = pd.DataFrame(rows, columns=[
        "Month", "Grade Pay", "Old Basic", "New Basic",
        "DA %", "Old Basic + DA", "New Basic + DA", "Monthly Arrear"
    ])

    st.success(f"✅ Total Arrear: ₹ {total_arrear:,.2f}")
    st.dataframe(df, use_container_width=True)

    # Excel download
    file_name = "arrear_report.xlsx"
    df.to_excel(file_name, index=False)

    with open(file_name, "rb") as f:
        st.download_button(
            "⬇️ Download Excel Report",
            f,
            file_name
        )
