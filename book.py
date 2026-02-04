# book.py
from database import Database
from datetime import datetime

class Book:
    def __init__(self):
        self.db = Database()
        self.db.get_connection()
    
    def add_book(self, title, author, isbn, category, total_copies, publication_year=None):
        """添加新书"""
        query = '''
            INSERT INTO books (title, author, isbn, category, total_copies, available_copies, publication_year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        try:
            success = self.db.execute_query(query, 
                (title, author, isbn, category, total_copies, total_copies, publication_year))
            return success
        except Exception as e:
            print(f"Error adding book: {e}")
            return False
    
    def get_all_books(self):
        """获取所有书籍"""
        query = '''
            SELECT book_id, title, author, isbn, category, total_copies, available_copies, publication_year
            FROM books
            ORDER BY title
        '''
        return self.db.fetch_all(query)
    
    def get_book_by_id(self, book_id):
        """根据ID获取书籍"""
        query = '''
            SELECT book_id, title, author, isbn, category, total_copies, available_copies, publication_year
            FROM books
            WHERE book_id = ?
        '''
        return self.db.fetch_one(query, (book_id,))
    
    def search_books(self, search_term, search_type='all'):
        """搜索书籍"""
        if not search_term:
            return self.get_all_books()
        
        search_term = f"%{search_term}%"
        
        if search_type == 'title':
            query = '''
                SELECT book_id, title, author, isbn, category, total_copies, available_copies
                FROM books
                WHERE title LIKE ?
                ORDER BY title
            '''
            params = (search_term,)
        elif search_type == 'author':
            query = '''
                SELECT book_id, title, author, isbn, category, total_copies, available_copies
                FROM books
                WHERE author LIKE ?
                ORDER BY author, title
            '''
            params = (search_term,)
        elif search_type == 'isbn':
            query = '''
                SELECT book_id, title, author, isbn, category, total_copies, available_copies
                FROM books
                WHERE isbn LIKE ?
                ORDER BY title
            '''
            params = (search_term,)
        elif search_type == 'category':
            query = '''
                SELECT book_id, title, author, isbn, category, total_copies, available_copies
                FROM books
                WHERE category LIKE ?
                ORDER BY category, title
            '''
            params = (search_term,)
        else:  # all
            query = '''
                SELECT book_id, title, author, isbn, category, total_copies, available_copies
                FROM books
                WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?
                ORDER BY title
            '''
            params = (search_term, search_term, search_term, search_term)
        
        return self.db.fetch_all(query, params)
    
    def update_book(self, book_id, title, author, isbn, category, total_copies, available_copies):
        """更新书籍信息"""
        query = '''
            UPDATE books
            SET title = ?, author = ?, isbn = ?, category = ?, 
                total_copies = ?, available_copies = ?
            WHERE book_id = ?
        '''
        return self.db.execute_query(query, 
            (title, author, isbn, category, total_copies, available_copies, book_id))
    
    def delete_book(self, book_id):
        """删除书籍"""
        # 首先检查是否有借阅记录
        check_query = '''
            SELECT COUNT(*) FROM transactions 
            WHERE book_id = ? AND return_date IS NULL
        '''
        result = self.db.fetch_one(check_query, (book_id,))
        
        if result and result[0] > 0:
            return False  # 有未归还的书籍，不能删除
        
        query = 'DELETE FROM books WHERE book_id = ?'
        return self.db.execute_query(query, (book_id,))
    
    def get_available_books(self):
        """获取可借阅的书籍"""
        query = '''
            SELECT book_id, title, author, isbn, category, total_copies, available_copies
            FROM books
            WHERE available_copies > 0
            ORDER BY title
        '''
        return self.db.fetch_all(query)
    
    def update_copies(self, book_id, change):
        """更新副本数量"""
        query = '''
            UPDATE books
            SET available_copies = available_copies + ?
            WHERE book_id = ?
        '''
        return self.db.execute_query(query, (change, book_id))