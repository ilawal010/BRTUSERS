
# ==========================================================
# GUSAU BRT – TICKETING & WALLET SYSTEM
# ==========================================================

import streamlit as st
import pandas as pd
import os, qrcode
from datetime import datetime, timedelta

# -----------------------------
# DIRECTORIES & FILES
# -----------------------------
DATA_DIR = "brt_data"
QR_DIR = "qr_codes"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

USERS_FILE   = f"{DATA_DIR}/users.csv"
WALLETS_FILE = f"{DATA_DIR}/wallets.csv"
TICKETS_FILE = f"{DATA_DIR}/tickets.csv"

# -----------------------------
# CSV INITIALIZATION
# -----------------------------
def init_csv(path, columns):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_csv(path, index=False)

init_csv(USERS_FILE,   ["user_id","first_name","role","phone","bus_stop"])
init_csv(WALLETS_FILE, ["user_id","balance"])
init_csv(TICKETS_FILE, ["ticket_id","buyer_id","ticket_type","amount",
                         "issue_time","expiry_time","terminal","qr_path"])

# -----------------------------
# LOAD DATA
# -----------------------------
users   = pd.read_csv(USERS_FILE)
wallets = pd.read_csv(WALLETS_FILE)

def save(df, path):
    df.to_csv(path, index=False)

def wallet_balance(uid):
    row = wallets[wallets.user_id == uid]
    return float(row.balance.iloc[0]) if not row.empty else 0.0

# ==========================================================
# STREAMLIT UI
# ==========================================================
st.title("🚌 Gusau BRT – Ticketing & Wallet System")

menu = st.sidebar.selectbox(
    "Menu",
    ["Register User","Load Wallet","Buy Ticket","Check Wallet Balance"]
)

# ==========================================================
# USER REGISTRATION
# ==========================================================
if menu == "Register User":
    st.subheader("User Registration")

    first_name = st.text_input("First Name")
    phone = st.text_input("Phone Number")
    role = st.selectbox(
        "User Category",
        ["Private Ticket Agent","Client / Passenger","Bus Conductor"]
    )
    bus_stop = st.text_input("Designated Bus Stop (optional)")

    if st.button("Register"):
        count = len(users) + 1
        user_id = f"{first_name.lower()}{str(count).zfill(4)}"

        users.loc[len(users)] = [user_id, first_name, role, phone, bus_stop]
        wallets.loc[len(wallets)] = [user_id, 0.0]

        save(users, USERS_FILE)
        save(wallets, WALLETS_FILE)

        st.success(f"Registered successfully. USER ID: {user_id}")

# ==========================================================
# WALLET FUNDING
# ==========================================================
elif menu == "Load Wallet":
    st.subheader("Wallet Funding")

    if wallets.empty:
        st.warning("No registered users yet.")
    else:
        uid = st.selectbox("Select User ID", wallets.user_id.tolist())
        method = st.selectbox(
            "Funding Method",
            ["USSD","Bank Transfer","Credit Unit"]
        )
        amount = st.number_input("Amount (₦)", min_value=100, step=100)

        if st.button("Load Wallet"):
            wallets.loc[wallets.user_id == uid, "balance"] += amount
            save(wallets, WALLETS_FILE)
            st.success(f"₦{amount} loaded successfully via {method}")

# ==========================================================
# BUY TICKET
# ==========================================================
elif menu == "Buy Ticket":
    st.subheader("Purchase Ticket")

    if wallets.empty:
        st.warning("No users available.")
    else:
        uid = st.selectbox("Buyer User ID", wallets.user_id.tolist())

        ticket_type = st.selectbox(
            "Ticket Type",
            ["Single Ride – ₦200","Daily Pass – ₦700","Monthly Pass – ₦15,000"]
        )

        terminal = st.text_input("Bus Terminal (optional)")

        PRICE = {
            "Single Ride – ₦200": 200,
            "Daily Pass – ₦700": 700,
            "Monthly Pass – ₦15,000": 15000
        }

        if st.button("Purchase Ticket"):
            price = PRICE[ticket_type]

            if wallet_balance(uid) < price:
                st.error("Insufficient wallet balance")
            else:
                now = datetime.now()

                if "Single" in ticket_type:
                    expiry = now + timedelta(minutes=30)
                elif "Daily" in ticket_type:
                    expiry = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                else:
                    expiry = now + timedelta(days=30)

                ticket_id = f"TKT-{int(now.timestamp())}"

                qr_data = (
                    f"TicketID:{ticket_id}\n"
                    f"User:{uid}\n"
                    f"Type:{ticket_type}\n"
                    f"Expiry:{expiry}"
                )

                qr_path = f"{QR_DIR}/{ticket_id}.png"
                qrcode.make(qr_data).save(qr_path)

                tickets = pd.read_csv(TICKETS_FILE)

                ticket_row = {
                    "ticket_id": ticket_id,
                    "buyer_id": uid,
                    "ticket_type": ticket_type,
                    "amount": price,
                    "issue_time": now,
                    "expiry_time": expiry,
                    "terminal": terminal,
                    "qr_path": qr_path
                }

                tickets = pd.concat([tickets, pd.DataFrame([ticket_row])], ignore_index=True)

                wallets.loc[wallets.user_id == uid, "balance"] -= price

                save(wallets, WALLETS_FILE)
                save(tickets, TICKETS_FILE)

                st.success("Ticket issued successfully")
                st.image(qr_path)
                st.download_button(
                    "Download QR / Receipt",
                    open(qr_path, "rb"),
                    file_name=f"{ticket_id}.png"
                )

# ==========================================================
# CHECK WALLET BALANCE
# ==========================================================
elif menu == "Check Wallet Balance":
    st.subheader("Wallet Balance")

    if wallets.empty:
        st.warning("No users available.")
    else:
        uid = st.selectbox("Select User ID", wallets.user_id.tolist())
        if st.button("Check Balance"):
            balance = wallet_balance(uid)
            st.info(f"User ID: {uid} | Wallet Balance: ₦{balance}")

