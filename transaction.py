# transaction.py
from database import Database
from datetime import datetime, timedelta

class Transaction:
    def __init__(self):
        self.db = Database()
        self.db.get_connection()
    
    def issue_book(self, book_id, member_id, loan_period_days=14):
        """借出书籍"""
        # 检查书籍是否可用
        book_query = '''
            SELECT available_copies, title FROM books WHERE book_id = ?
        '''
        book = self.db.fetch_one(book_query, (book_id,))
        
        if not book or book[0] <= 0:
            return False
        
        # 检查会员状态
        member_query = '''
            SELECT status FROM members WHERE member_id = ?
        '''
        member = self.db.fetch_one(member_query, (member_id,))
        
        if not member or member[0] != 'Active':
            return False
        
        # 检查会员借书数量限制
        setting_query = '''
            SELECT setting_value FROM settings WHERE setting_name = 'max_books_per_member'
        '''
        max_books = int(self.db.fetch_one(setting_query)[0])
        
        current_loans_query = '''
            SELECT COUNT(*) FROM transactions 
            WHERE member_id = ? AND return_date IS NULL
        '''
        current_loans = self.db.fetch_one(current_loans_query, (member_id,))[0]
        
        if current_loans >= max_books:
            return False
        
        # 计算到期日期
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=loan_period_days)
        
        # 开始事务
        try:
            # 插入交易记录
            transaction_query = '''
                INSERT INTO transactions (book_id, member_id, issue_date, due_date)
                VALUES (?, ?, ?, ?)
            '''
            self.db.execute_query(transaction_query, 
                (book_id, member_id, issue_date, due_date))
            
            # 更新书籍可用副本
            update_book_query = '''
                UPDATE books
                SET available_copies = available_copies - 1
                WHERE book_id = ?
            '''
            self.db.execute_query(update_book_query, (book_id,))
            
            # 更新会员借书数量
            update_member_query = '''
                UPDATE members
                SET total_books_borrowed = total_books_borrowed + 1
                WHERE member_id = ?
            '''
            self.db.execute_query(update_member_query, (member_id,))
            
            return True
        except Exception as e:
            print(f"Error issuing book: {e}")
            return False
    
    def return_book(self, transaction_id):
        """归还书籍"""
        # 获取交易信息
        query = '''
            SELECT book_id, member_id, due_date FROM transactions
            WHERE transaction_id = ? AND return_date IS NULL
        '''
        transaction = self.db.fetch_one(query, (transaction_id,))
        
        if not transaction:
            return False
        
        book_id, member_id, due_date = transaction
        return_date = datetime.now()
        
        # 计算罚款
        fine = self.calculate_fine(transaction_id)
        
        try:
            # 更新交易记录
            update_transaction_query = '''
                UPDATE transactions
                SET return_date = ?, fine_amount = ?
                WHERE transaction_id = ?
            '''
            self.db.execute_query(update_transaction_query, 
                (return_date, fine, transaction_id))
            
            # 更新书籍可用副本
            update_book_query = '''
                UPDATE books
                SET available_copies = available_copies + 1
                WHERE book_id = ?
            '''
            self.db.execute_query(update_book_query, (book_id,))
            
            return True
        except Exception as e:
            print(f"Error returning book: {e}")
            return False
    
    def calculate_fine(self, transaction_id):
        """计算罚款"""
        query = '''
            SELECT due_date, fine_amount FROM transactions
            WHERE transaction_id = ?
        '''
        transaction = self.db.fetch_one(query, (transaction_id,))
        
        if not transaction:
            return 0.0
        
        due_date_str, existing_fine = transaction
        
        if existing_fine > 0:
            return existing_fine
        
        # 如果已经有罚款或已归还，返回0
        check_query = '''
            SELECT return_date FROM transactions WHERE transaction_id = ?
        '''
        result = self.db.fetch_one(check_query, (transaction_id,))
        
        if result and result[0]:  # 已归还
            return 0.0
        
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d %H:%M:%S.%f')
        current_date = datetime.now()
        
        if current_date <= due_date:
            return 0.0
        
        # 计算逾期天数
        days_overdue = (current_date - due_date).days
        
        # 获取宽限期
        setting_query = '''
            SELECT setting_value FROM settings WHERE setting_name = 'grace_period_days'
        '''
        grace_period = int(self.db.fetch_one(setting_query)[0])
        
        if days_overdue <= grace_period:
            return 0.0
        
        # 计算罚款天数
        fine_days = days_overdue - grace_period
        
        # 获取每日罚款金额
        setting_query = '''
            SELECT setting_value FROM settings WHERE setting_name = 'fine_per_day'
        '''
        fine_per_day = float(self.db.fetch_one(setting_query)[0])
        
        # 获取最大罚款金额
        setting_query = '''
            SELECT setting_value FROM settings WHERE setting_name = 'max_fine_amount'
        '''
        max_fine = float(self.db.fetch_one(setting_query)[0])
        
        fine = fine_days * fine_per_day
        return min(fine, max_fine)
    
    def get_active_transactions(self):
        """获取活跃交易（未归还）"""
        query = '''
            SELECT t.transaction_id, b.title, m.name, 
                   DATE(t.issue_date) as issue_date, DATE(t.due_date) as due_date
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN members m ON t.member_id = m.member_id
            WHERE t.return_date IS NULL
            ORDER BY t.due_date
        '''
        return self.db.fetch_all(query)
    
    def get_transaction_history(self, limit=100):
        """获取交易历史"""
        query = '''
            SELECT t.transaction_id, b.title, m.name, 
                   DATE(t.issue_date) as issue_date, DATE(t.due_date) as due_date,
                   DATE(t.return_date) as return_date, t.fine_amount
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN members m ON t.member_id = m.member_id
            ORDER BY t.issue_date DESC
            LIMIT ?
        '''
        return self.db.fetch_all(query, (limit,))
    
    def get_member_transactions(self, member_id):
        """获取会员的交易记录"""
        query = '''
            SELECT t.transaction_id, b.title, 
                   DATE(t.issue_date) as issue_date, DATE(t.due_date) as due_date,
                   DATE(t.return_date) as return_date, t.fine_amount
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            WHERE t.member_id = ?
            ORDER BY t.issue_date DESC
        '''
        return self.db.fetch_all(query, (member_id,))
    
    def pay_fine(self, transaction_id, amount):
        """支付罚款"""
        query = '''
            UPDATE transactions
            SET fine_paid = CASE 
                WHEN ? >= fine_amount THEN TRUE 
                ELSE FALSE 
            END
            WHERE transaction_id = ?
        '''
        return self.db.execute_query(query, (amount, transaction_id))