# database.py
import sqlite3
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_name='library.db'):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        
    def get_connection(self):
        """Get database connection"""
        if not self.connection:
            self.connection = sqlite3.connect(self.db_name, check_same_thread=False)
            self.cursor = self.connection.cursor()
        return self.connection
    
    def create_tables(self):
        """Create database tables"""
        conn = self.get_connection()
        cursor = self.cursor
        
        # Books table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                total_copies INTEGER NOT NULL,
                available_copies INTEGER NOT NULL,
                publication_year INTEGER,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                membership_type TEXT DEFAULT 'Regular',
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Active',
                total_books_borrowed INTEGER DEFAULT 0
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                return_date TIMESTAMP,
                fine_amount REAL DEFAULT 0.0,
                fine_paid BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (book_id) REFERENCES books (book_id),
                FOREIGN KEY (member_id) REFERENCES members (member_id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_name TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL
            )
        ''')
        
        # Insert default settings
        default_settings = [
            ('loan_period_days', '14'),
            ('max_books_per_member', '5'),
            ('fine_per_day', '1.0'),
            ('grace_period_days', '2'),
            ('max_fine_amount', '20.0'),
            ('allow_renewal', 'true'),
            ('renewal_days', '7')
        ]
        
        for setting in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (setting_name, setting_value)
                VALUES (?, ?)
            ''', setting)
        
        conn.commit()
        return True
    
    def execute_query(self, query, params=()):
        """Execute SQL query"""
        try:
            conn = self.get_connection()
            cursor = self.cursor
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False
    
    def fetch_all(self, query, params=()):
        """Fetch all results"""
        try:
            conn = self.get_connection()
            cursor = self.cursor
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"Database fetch error: {e}")
            return []
    
    def fetch_one(self, query, params=()):
        """Fetch one result"""
        try:
            conn = self.get_connection()
            cursor = self.cursor
            cursor.execute(query, params)
            return cursor.fetchone()
        except Exception as e:
            print(f"Database fetch error: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
