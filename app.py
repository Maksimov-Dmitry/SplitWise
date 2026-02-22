from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import streamlit as st

PEOPLE = ["Dmitrii", "Nikita", "Alex", "Katja"]


@dataclass
class Expense:
    id: str = field(default_factory=lambda: uuid4().hex[:8])
    paid_by: str = ""
    amount: float = 0.0
    description: str = ""
    split_among: list[str] = field(default_factory=list)


@st.cache_resource
def get_expenses() -> list[Expense]:
    return []


def compute_minimal_transfers(expenses: list[Expense]) -> list[tuple[str, str, float]]:
    """Compute minimal number of transfers to settle all debts.

    Uses a greedy algorithm: repeatedly settle the largest creditor with the largest debtor.
    This produces the minimum number of transfers when there are no cycles, which is optimal
    for small groups.
    """
    balances: dict[str, float] = {p: 0.0 for p in PEOPLE}

    for exp in expenses:
        balances[exp.paid_by] += exp.amount
        share = exp.amount / len(exp.split_among)
        for person in exp.split_among:
            balances[person] -= share

    creditors: list[list[str | float]] = []
    debtors: list[list[str | float]] = []

    for person, balance in balances.items():
        if balance > 0.01:
            creditors.append([person, balance])
        elif balance < -0.01:
            debtors.append([person, -balance])

    transfers: list[tuple[str, str, float]] = []

    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    while creditors and debtors:
        creditor = creditors[0]
        debtor = debtors[0]
        settled = min(creditor[1], debtor[1])

        transfers.append((debtor[0], creditor[0], round(settled, 2)))

        creditor[1] -= settled
        debtor[1] -= settled

        if creditor[1] < 0.01:
            creditors.pop(0)
        if debtor[1] < 0.01:
            debtors.pop(0)

    return transfers


def main() -> None:
    st.set_page_config(page_title="SplitWise — Ski Trip", page_icon="⛷️", layout="centered")
    st.title("⛷️ Ski Trip — Expense Splitter")

    expenses = get_expenses()

    # --- Add expense form ---
    st.header("Add Expense")
    with st.form("add_expense", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            paid_by = st.selectbox("Who paid?", PEOPLE)
        with col2:
            amount = st.number_input("Amount (EUR)", min_value=0.01, step=0.01, format="%.2f")

        description = st.text_input("Description (optional)")
        split_among = st.multiselect("Split among", PEOPLE, default=PEOPLE)

        submitted = st.form_submit_button("Add Expense")

        if submitted:
            if not split_among:
                st.error("Select at least one person to split among.")
            else:
                expense = Expense(
                    paid_by=paid_by,
                    amount=amount,
                    description=description,
                    split_among=split_among,
                )
                expenses.append(expense)
                st.success(f"Added: {paid_by} paid €{amount:.2f}")

    # --- Expenses list ---
    st.header("Expenses")

    if not expenses:
        st.info("No expenses yet. Add one above.")
    else:
        for i, exp in enumerate(expenses):
            split_label = (
                "everyone" if set(exp.split_among) == set(PEOPLE) else ", ".join(exp.split_among)
            )
            desc = f" — {exp.description}" if exp.description else ""
            col_text, col_btn = st.columns([5, 1])
            with col_text:
                st.markdown(
                    f"**{exp.paid_by}** paid **€{exp.amount:.2f}** "
                    f"split among {split_label}{desc}"
                )
            with col_btn:
                if st.button("🗑️", key=f"del_{exp.id}_{i}"):
                    expenses.pop(i)
                    st.rerun()

    # --- Settle ---
    st.header("Settle Up")
    if st.button("💶 Calculate Transfers", type="primary"):
        if not expenses:
            st.warning("No expenses to settle.")
        else:
            transfers = compute_minimal_transfers(expenses)
            if not transfers:
                st.success("Everyone is already settled! No transfers needed.")
            else:
                st.subheader("Transfers needed:")
                for sender, receiver, amt in transfers:
                    st.markdown(f"**{sender}** → **{receiver}**: **€{amt:.2f}**")


if __name__ == "__main__":
    main()
