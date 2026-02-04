import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime, timedelta

st.header("Issue and Return Books")

conn = get_connection()

book_id = st.number_input("Book ID", min_value=1)
member_id = st.number_input("Member ID", min_value=1)

if st.button("Issue Book"):
    cur = conn.cursor()
    cur.execute("SELECT available FROM books WHERE book_id=?", (book_id,))
    result = cur.fetchone()

    if result and result[0] > 0:
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=14)

        cur.execute("""
        INSERT INTO transactions (book_id, member_id, issue_date, due_date, fine)
        VALUES (?, ?, ?, ?, 0)
        """, (book_id, member_id, issue_date, due_date))

        cur.execute("""
        UPDATE books SET available = available - 1 WHERE book_id=?
        """, (book_id,))

        conn.commit()
        st.success("Book issued successfully")
    else:
        st.error("Book not available")

st.subheader("Active Transactions")
df = pd.read_sql("SELECT * FROM transactions WHERE return_date IS NULL", conn)
st.dataframe(df)
