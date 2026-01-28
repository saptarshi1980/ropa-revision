import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt

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
# DA HISTORY
# ==================================================

DA_HISTORY = [
    (date(2020, 1, 1), 0.10),
    (date(2021, 1, 1), 0.13),
    (date(2023, 3, 1), 0.16),
    (date(2024, 1, 1), 0.20),
    (date(2024, 4, 1), 0.24),
    (date(2025, 4, 1), 0.28),
]

def generate_pay_matrix_image(gp):
    matrix = PAY_MATRIX[gp]

    df = pd.DataFrame(matrix, columns=[
        "Pre-Revised Basic",
        "Revised Basic"
    ])

    df.index = range(1, len(df) + 1)
    df.insert(0, "Level", df.index)

    fig, ax = plt.subplots(figsize=(6, 0.5 * len(df) + 1))
    ax.axis('off')

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc='center',
        loc='center'
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#E8E8E8')

    plt.title(f"Revised Pay Matrix – GP {gp}", fontsize=14, weight='bold', pad=12)

    filename = f"pay_matrix_gp_{gp}.png"
    plt.savefig(filename, dpi=200, bbox_inches="tight")
    plt.close()

    return filename

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

def get_old_basics(gp):
    return [old for (old, _) in PAY_MATRIX[gp]]

# ==================================================
# INCREMENT RULE
# ==================================================

def increment_due(current, increment_month):
    if increment_month == 1:
        return current.month == 1 and current.year > 2020
    return current.month == increment_month and current.year >= 2020

# ==================================================
# STREAMLIT UI
# ==================================================

st.set_page_config(page_title="Salary Arrear Calculator", layout="wide")

st.markdown(
    "<h2 style='text-align:center;'>📊 Salary Arrear Calculator (ROPA-2020 – GP 6600 & 7600)</h2>",
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    initial_gp = st.selectbox("Initial Grade Pay as on Jan-2020", [6600, 7600])

    initial_basic = st.selectbox(
        "Basic Pay as on Jan-2020 (OLD BASIC)",
        get_old_basics(initial_gp),
        format_func=lambda x: f"₹ {x:,.0f}"
    )

with col2:
    increment_month = st.selectbox(
        "Increment Month",
        list(range(1, 13)),
        format_func=lambda x: date(2000, x, 1).strftime("%B")
    )

    arrear_upto = st.text_input("Calculate arrear upto (YYYYMM)", value="202602")

promotion_input = st.text_input(
    "Promotion Month (YYYYMM) – Optional",
    help="On promotion: GP → 7600, Basic resets to 102600",
    max_chars=6
)

# ==================================================
# CALCULATION
# ==================================================

if st.button("Generate Arrear Report"):

    try:
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

            promotion_this_month = False

            # ===== Promotion =====
            if promotion_date and current == promotion_date and not promoted:
                current_gp = 7600
                step = 0      # fixation only
                promoted = True
                promotion_this_month = True

            # ===== Increment =====
            if not promotion_this_month and increment_due(current, increment_month):
                step = min(step + 1, len(PAY_MATRIX[current_gp]) - 1)

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

            current += relativedelta(months=1)

        df = pd.DataFrame(rows, columns=[
            "Month", "Grade Pay", "Old Basic", "New Basic",
            "DA %", "Old Basic + DA", "New Basic + DA", "Monthly Arrear"
        ])

        st.success(f"✅ Total Arrear: ₹ {total_arrear:,.2f}")
        st.dataframe(df, width="stretch")

        df.to_excel("arrear_report.xlsx", index=False)
        with open("arrear_report.xlsx", "rb") as f:
            st.download_button("⬇️ Download Excel Report", f, "arrear_report.xlsx")

    except Exception as e:
        st.error(f"❌ {str(e)}")



st.markdown("### 📷 Download Revised Pay Matrix")

colA, colB = st.columns(2)

with colA:
    if st.button("Download GP 6600 Pay Matrix"):
        img_6600 = generate_pay_matrix_image(6600)
        with open(img_6600, "rb") as f:
            st.download_button(
                "⬇️ Download GP 6600 Image",
                f,
                file_name=img_6600,
                mime="image/png"
            )

with colB:
    if st.button("Download GP 7600 Pay Matrix"):
        img_7600 = generate_pay_matrix_image(7600)
        with open(img_7600, "rb") as f:
            st.download_button(
                "⬇️ Download GP 7600 Image",
                f,
                file_name=img_7600,
                mime="image/png"
            )


