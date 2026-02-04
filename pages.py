import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime

st.header("Member Management")

conn = get_connection()

with st.form("add_member"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")

    if st.form_submit_button("Register Member"):
        conn.execute("""
        INSERT INTO members (name, email, phone, join_date, status)
        VALUES (?, ?, ?, ?, ?)
        """, (name, email, phone, datetime.now().strftime("%Y-%m-%d"), "Active"))
        conn.commit()
        st.success("Member registered")

df = pd.read_sql("SELECT * FROM members", conn)
st.subheader("Registered Members")
st.dataframe(df)
