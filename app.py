import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from database import Database
from book import Book
from member import Member
from transaction import Transaction
from report import Report

# Page configuration
st.set_page_config(
    page_title="Library System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BEAUTIFICATION & CSS ---
def add_bg_from_local(image_file):
    try:
        with open(image_file, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url(data:image/png;base64,{encoded_string});
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            
            /* WHITE BOX styling: Solid white background for all major containers */
            .stDataFrame, .stPlotlyChart, [data-testid="stMetric"], .stExpander, div[data-testid="stForm"], .stTab, div[class*="stMarkdown"] {{
                background-color: #FFFFFF;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 15px;
            }}
            
            /* Specific fix for floating text/headers to be in boxes or clearly visible */
            h1, h2, h3 {{
                background-color: rgba(255, 255, 255, 0.95);
                padding: 15px;
                border-radius: 10px;
                color: #111827 !important;
                font-weight: 800 !important;
                display: inline-block; /* Wrap tight around text */
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            /* Typography Enhancements */
            html, body, [class*="css"] {{
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }}

            /* General Text Visibility - Ensure contrast */
            p, li, label, .stMarkdown, .stText {{
                color: #000000 !important;
                font-size: 1.2rem !important;
                font-weight: 600 !important;
                line-height: 1.6;
            }}
            
            /* Sidebar Styling - Solid white/grey */
            section[data-testid="stSidebar"] {{
                background-color: #F9FAFB;
                border-right: 1px solid #E5E7EB;
            }}
            section[data-testid="stSidebar"] .stMarkdown h1 {{
                 background-color: transparent; /* Sidebar header doesn't need box if sidebar is solid */
                 box-shadow: none;
                 font-size: 2rem !important;
                 color: #1F2937 !important;
                 text-align: center;
                 margin-bottom: 2rem;
            }}

            /* Input Fields - Solid White */
            .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
                background-color: #FFFFFF !important;
                color: #000000 !important;
                font-size: 1.1rem !important;
                font-weight: 500;
                border: 2px solid #E5E7EB;
                border-radius: 8px;
            }}
            
            /* Buttons */
            .stButton button {{
                font-weight: 700 !important;
                font-size: 1.1rem !important;
                border-radius: 8px;
                padding-top: 0.5rem;
                padding-bottom: 0.5rem;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        pass 

# Initialize session state and managers
@st.cache_resource
def get_managers():
    try:
        db = Database()
        db.create_tables()
        return {
            'db': db,
            'book': Book(),
            'member': Member(),
            'transaction': Transaction(),
            'report': Report()
        }
    except Exception as e:
        st.error(f"Initialization error: {e}")
        return None

managers = get_managers()

# attempt to load background
add_bg_from_local("./assets/background.png")

if not managers:
    st.stop()

# Helper accessors
book_mgr = managers['book']
member_mgr = managers['member']
trans_mgr = managers['transaction']
report_mgr = managers['report']

# Sidebar Navigation
st.sidebar.markdown("# 🏛️ Athena Library")
page = st.sidebar.radio("Navigation", 
    ["🏠 Dashboard", "📚 Books", "👥 Members", "🔄 Circulation", "📊 Reports"])

# --- DASHBOARD ---
if "Dashboard" in page:
    st.title("🏠 Dashboard Overview")
    
    # Wrap dashboard stats in a container for better white-box effect if needed, 
    # but metrics have their own boxes via CSS above.
    
    stats = report_mgr.get_library_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    if stats:
        with col1:
            st.metric("Total Books", stats[0][1])
        with col2:
            st.metric("Members", stats[3][1])
        with col3:
            st.metric("Active Loans", stats[5][1])
        with col4:
            st.metric("Overdue", stats[6][1])
        
        # Use markdown containers for these to get the white box effect
        st.markdown("### ⚡ Quick Status")
        col_a, col_b = st.columns(2)
        
        with col_a:
             st.info(f"**Available Copies:** {stats[2][1]}")
        with col_b:
             st.error(f"**Total Fines Due:** {stats[7][1]}")
    else:
        st.warning("Could not load statistics.")

# --- BOOKS ---
elif "Books" in page:
    st.title("📚 Library Collection")
    
    tab1, tab2 = st.tabs(["🔍 Search & Inventory", "➕ Add New Book"])
    
    with tab1:
        st.markdown("### 📖 Browse Inventory")
        search_term = st.text_input("Find books by Title, Author, or ISBN")
        if search_term:
            books = book_mgr.search_books(search_term)
        else:
            books = book_mgr.get_all_books()
            
        if books:
            df = pd.DataFrame(books, columns=[
                'ID', 'Title', 'Author', 'ISBN', 'Category', 
                'Total Copies', 'Available', 'Year'
            ])
            st.dataframe(df, use_container_width=True)
            
            st.divider()
            with st.expander("🗑️ Delete Book"):
                book_id_to_del = st.number_input("Enter Book ID to Remove", min_value=1, step=1)
                if st.button("Delete Book", type="primary"):
                    if book_mgr.delete_book(book_id_to_del):
                        st.success(f"Book ID {book_id_to_del} deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Cannot delete book. It might be currently borrowed.")
        else:
            st.info("No books found in the inventory.")
            
    with tab2:
        st.markdown("### 📝 Register New Entry")
        with st.form("add_book_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                new_title = st.text_input("Book Title")
                new_isbn = st.text_input("ISBN")
                new_copies = st.number_input("Total Copies", min_value=1, value=1)
            with col_b:
                new_author = st.text_input("Author")
                new_category = st.selectbox("Category", 
                    ["Fiction", "Non-Fiction", "Science", "History", "Technology", "Arts", "Other"])
                new_year = st.number_input("Year", min_value=1000, max_value=2100, step=1, value=2024)
            
            submit = st.form_submit_button("✨ Add Book to Collection")
            
            if submit:
                if new_title and new_author and new_isbn:
                    if book_mgr.add_book(new_title, new_author, new_isbn, new_category, new_copies, new_year):
                        st.success(f"✅ Book '{new_title}' added successfully!")
                    else:
                        st.error("❌ Failed to add book. ISBN might already exist.")
                else:
                    st.warning("⚠️ Please fill in all required fields.")

# --- MEMBERS ---
elif "Members" in page:
    st.title("👥 Member Directory")
    
    tab1, tab2 = st.tabs(["📋 Member List", "➕ New Registration"])
    
    with tab1:
        st.markdown("### 🔍 Find Members")
        search_member = st.text_input("Search by Name, Email or Phone")
        if search_member:
            members = member_mgr.search_members(search_member)
        else:
            members = member_mgr.get_all_members()

        if members:
            try:
                df = pd.DataFrame(members, columns=[
                    'ID', 'Name', 'Email', 'Phone', 'Join Date', 'Status', 'Books Borrowed'
                ])
                st.dataframe(df, use_container_width=True)
            except ValueError:
                 st.dataframe(members)
            
            st.divider()
            with st.expander("🗑️ Remove Member"):
                mid_del = st.number_input("Member ID to Remove", min_value=1)
                if st.button("Delete Member", type="primary"):
                    if member_mgr.delete_member(mid_del):
                        st.success(f"Member ID {mid_del} removed.")
                        st.rerun()
                    else:
                        st.error("Cannot delete member. Check for unreturned books.")
        else:
            st.info("No members found.")
            
    with tab2:
        st.markdown("### 📝 New Membership")
        with st.form("add_member", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                m_name = st.text_input("Full Name")
                m_phone = st.text_input("Phone Number")
            with col_b:
                m_email = st.text_input("Email Address")
                m_type = st.selectbox("Membership Tier", ["Regular", "Premium", "Student"])
            
            sub = st.form_submit_button("✨ Register New Member")
            
            if sub:
                if m_name and m_email:
                    if member_mgr.add_member(m_name, m_email, m_phone, m_type):
                        st.success(f"✅ Member '{m_name}' registered successfully!")
                    else:
                        st.error("❌ Registration failed. Email might be already in use.")
                else:
                    st.warning("⚠️ Name and Email are required.")

# --- TRANSACTIONS ---
elif "Circulation" in page:
    st.title("🔄 Circulation Desk")
    
    mode = st.radio("Action", ["📤 Issue Book", "📥 Return Book", "📋 Active Loans"], horizontal=True)
    
    if "Issue" in mode:
        st.markdown("### 📤 Issue a Book")
        # Markdown is automatically boxed by CSS, but Layout columns might not be.
        # The form or interactive elements will be boxed.
        
        container = st.container()
        
        col1, col2 = st.columns(2)
        
        if 'selected_member_id' not in st.session_state:
            st.session_state.selected_member_id = None
        if 'selected_book_id' not in st.session_state:
            st.session_state.selected_book_id = None
        
        # We can use expanders or just improved headers to make sections distinct if 'white box' isn't applying to raw columns
        # But 'stMetric', 'stTextInput' etc have white backgrounds now.
            
        with col1:
            st.subheader("1. Identify Member")
            m_search = st.text_input("Search Member", key="m_search")
            if m_search:
                m_results = member_mgr.search_members(m_search)
                if m_results:
                    m_opts = {f"{m[1]} ({m[2]})": m[0] for m in m_results}
                    sel_m = st.selectbox("Select Member", list(m_opts.keys()), key="sel_m")
                    st.session_state.selected_member_id = m_opts[sel_m]
                else:
                    st.warning("No member found.")
            
        with col2:
            st.subheader("2. Identify Book")
            b_search = st.text_input("Search Book", key="b_search")
            if b_search:
                b_results = book_mgr.search_books(b_search)
                avail_books = [b for b in b_results if b[6] > 0]
                if avail_books:
                    b_opts = {f"{b[1]} - {b[2]}": b[0] for b in avail_books}
                    sel_b = st.selectbox("Select Book", list(b_opts.keys()), key="sel_b")
                    st.session_state.selected_book_id = b_opts[sel_b]
                else:
                    st.warning("No available books matching query.")
        
        st.divider()
        if st.button("✅ Confirm Issue", type="primary", use_container_width=True):
             if st.session_state.selected_member_id and st.session_state.selected_book_id:
                if trans_mgr.issue_book(st.session_state.selected_book_id, st.session_state.selected_member_id):
                    st.success("Book issued successfully!")
                else:
                    st.error("Failed to issue. Check transaction limit or book availability.")
             else:
                 st.error("Please select both a member and a book.")

    elif "Return" in mode:
        st.markdown("### 📥 Return a Book")
        loans = trans_mgr.get_active_transactions()
        if loans:
            loan_opts = {f"Loan #{l[0]} | {l[1]} ({l[2]}) | Due: {l[4]}": l[0] for l in loans}
            sel_loan_label = st.selectbox("Select Loan to Return", list(loan_opts.keys()))
            sel_loan_id = loan_opts[sel_loan_label]
            
            fine = trans_mgr.calculate_fine(sel_loan_id)
            if fine > 0:
                st.error(f"⚠️ Overdue Fine: ${fine:.2f}")
            else:
                st.success("✅ No fine applicable.")
                
            if st.button("✅ Confirm Return", type="primary"):
                if trans_mgr.return_book(sel_loan_id):
                    st.success("Book returned successfully!")
                    st.rerun()
                else:
                    st.error("Error processing return.")
        else:
            st.info("No active loans.")

    elif "Active Loans" in mode:
        st.markdown("### 📋 Ongoing Transactions")
        loans = trans_mgr.get_active_transactions()
        if loans:
            df = pd.DataFrame(loans, columns=['ID', 'Book Title', 'Borrower', 'Issued On', 'Due Date'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No books are currently issued.")

# --- REPORTS ---
elif "Reports" in page:
    st.title("📊 Analytics & Reports")
    
    r_type = st.selectbox("Select Report Type", 
        ["🔥 Popular Books", "⚠️ Overdue List", "📚 Category Split", "🏆 Top Readers"])
    
    if "Popular" in r_type:
        st.subheader("🔥 Most Borrowed Books")
        data = report_mgr.get_popular_books()
        if data:
            df = pd.DataFrame(data, columns=['ID', 'Title', 'Author', 'Borrows'])
            st.bar_chart(df.set_index('Title')['Borrows'])
            
    elif "Overdue" in r_type:
        st.subheader("⚠️ Overdue Items")
        data = report_mgr.get_overdue_books()
        if data:
            df = pd.DataFrame(data, columns=['TRX ID', 'Book', 'Member', 'Email', 'Issue Date', 'Due Date', 'Days Over', 'Fine'])
            st.dataframe(df)
        else:
            st.success("No overdue books! Good job.")
            
    elif "Category" in r_type:
        st.subheader("📚 Collection Distribution")
        data = report_mgr.get_category_distribution()
        if data:
            df = pd.DataFrame(data, columns=['Category', 'Count'])
            fig = px.pie(df, values='Count', names='Category', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
    elif "Top Readers" in r_type:
        st.subheader("🏆 Most Active Members")
        data = report_mgr.get_top_members()
        if data:
            df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Borrowed Count', 'Last Active'])
            st.bar_chart(df.set_index('Name')['Borrowed Count'])
