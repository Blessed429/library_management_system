# report.py
from database import Database
from datetime import datetime, timedelta

class Report:
    def __init__(self):
        self.db = Database()
        self.db.get_connection()
    
    def get_library_statistics(self):
        """获取图书馆统计"""
        stats = []
        
        # 总书籍数量
        query = "SELECT COUNT(*) FROM books"
        total_books = self.db.fetch_one(query)[0]
        stats.append(("Total Books", total_books))
        
        # 总副本数量
        query = "SELECT SUM(total_copies) FROM books"
        total_copies = self.db.fetch_one(query)[0] or 0
        stats.append(("Total Copies", total_copies))
        
        # 可用副本数量
        query = "SELECT SUM(available_copies) FROM books"
        available_copies = self.db.fetch_one(query)[0] or 0
        stats.append(("Available Copies", available_copies))
        
        # 总会员数量
        query = "SELECT COUNT(*) FROM members"
        total_members = self.db.fetch_one(query)[0]
        stats.append(("Total Members", total_members))
        
        # 活跃会员数量
        query = "SELECT COUNT(*) FROM members WHERE status = 'Active'"
        active_members = self.db.fetch_one(query)[0]
        stats.append(("Active Members", active_members))
        
        # 活跃借阅数量
        query = "SELECT COUNT(*) FROM transactions WHERE return_date IS NULL"
        active_loans = self.db.fetch_one(query)[0]
        stats.append(("Active Loans", active_loans))
        
        # 逾期书籍数量
        query = '''
            SELECT COUNT(*) FROM transactions 
            WHERE return_date IS NULL AND due_date < datetime('now')
        '''
        overdue_books = self.db.fetch_one(query)[0]
        stats.append(("Overdue Books", overdue_books))
        
        # 总罚款
        query = "SELECT SUM(fine_amount) FROM transactions WHERE fine_paid = FALSE"
        total_fines = self.db.fetch_one(query)[0] or 0.0
        stats.append(("Total Fines Due", f"${total_fines:.2f}"))
        
        return stats
    
    def get_available_books(self):
        """获取可用书籍"""
        query = '''
            SELECT book_id, title, author, category, available_copies
            FROM books
            WHERE available_copies > 0
            ORDER BY title
        '''
        return self.db.fetch_all(query)
    
    def get_popular_books(self, limit=10):
        """获取热门书籍"""
        query = '''
            SELECT b.book_id, b.title, b.author, 
                   COUNT(t.transaction_id) as borrow_count
            FROM books b
            LEFT JOIN transactions t ON b.book_id = t.book_id
            GROUP BY b.book_id
            ORDER BY borrow_count DESC
            LIMIT ?
        '''
        return self.db.fetch_all(query, (limit,))
    
    def get_books_by_category(self):
        """按分类统计书籍"""
        query = '''
            SELECT category, COUNT(*) as count, 
                   SUM(total_copies) as total_copies,
                   SUM(available_copies) as available_copies
            FROM books
            GROUP BY category
            ORDER BY count DESC
        '''
        return self.db.fetch_all(query)
    
    def get_member_statistics(self):
        """获取会员统计"""
        query = '''
            SELECT m.member_id, m.name, m.email,
                   COUNT(t.transaction_id) as total_borrowed,
                   SUM(CASE WHEN t.return_date IS NULL THEN 1 ELSE 0 END) as current_loans,
                   SUM(t.fine_amount) as total_fines,
                   SUM(CASE WHEN t.fine_paid = FALSE THEN t.fine_amount ELSE 0 END) as unpaid_fines
            FROM members m
            LEFT JOIN transactions t ON m.member_id = t.member_id
            GROUP BY m.member_id
            ORDER BY total_borrowed DESC
        '''
        return self.db.fetch_all(query)
    
    def get_overdue_books(self):
        """获取逾期书籍"""
        query = '''
            SELECT t.transaction_id, b.title, m.name, m.email,
                   DATE(t.issue_date) as issue_date,
                   DATE(t.due_date) as due_date,
                   julianday('now') - julianday(t.due_date) as days_overdue,
                   t.fine_amount
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN members m ON t.member_id = m.member_id
            WHERE t.return_date IS NULL 
            AND t.due_date < datetime('now')
            ORDER BY days_overdue DESC
        '''
        return self.db.fetch_all(query)
    
    def get_monthly_activity(self, months=6):
        """获取月度活动"""
        query = '''
            SELECT 
                strftime('%Y-%m', issue_date) as month,
                COUNT(*) as total_issues,
                SUM(CASE WHEN return_date IS NULL THEN 1 ELSE 0 END) as active_loans,
                SUM(fine_amount) as total_fines,
                SUM(CASE WHEN fine_paid = TRUE THEN fine_amount ELSE 0 END) as paid_fines
            FROM transactions
            WHERE issue_date >= date('now', ?)
            GROUP BY strftime('%Y-%m', issue_date)
            ORDER BY month DESC
        '''
        return self.db.fetch_all(query, (f'-{months} months',))
    
    def get_category_distribution(self):
        """获取分类分布"""
        query = '''
            SELECT category, COUNT(*) as count
            FROM books
            GROUP BY category
            ORDER BY count DESC
        '''
        return self.db.fetch_all(query)
    
    def get_top_members(self, limit=10):
        """获取顶级会员"""
        query = '''
            SELECT m.member_id, m.name, m.email,
                   COUNT(t.transaction_id) as books_borrowed,
                   MAX(t.issue_date) as last_borrowed
            FROM members m
            LEFT JOIN transactions t ON m.member_id = t.member_id
            WHERE m.status = 'Active'
            GROUP BY m.member_id
            ORDER BY books_borrowed DESC
            LIMIT ?
        '''
        return self.db.fetch_all(query, (limit,))