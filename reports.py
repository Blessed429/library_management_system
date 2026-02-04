import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection

st.header("Reports & Statistics")

conn = get_connection()

books = pd.read_sql("SELECT * FROM books", conn)
transactions = pd.read_sql("SELECT * FROM transactions", conn)

st.metric("Total Books", books["quantity"].sum())
st.metric("Books Available", books["available"].sum())
st.metric("Active Loans", len(transactions[transactions["return_date"].isna()]))

fig = px.bar(books, x="title", y="available", title="Available Books per Title")
st.plotly_chart(fig)
