# member.py
from database import Database
from datetime import datetime

class Member:
    def __init__(self):
        self.db = Database()
        self.db.get_connection()
    
    def add_member(self, name, email, phone=None, membership_type='Regular'):
        """添加新会员"""
        query = '''
            INSERT INTO members (name, email, phone, membership_type)
            VALUES (?, ?, ?, ?)
        '''
        return self.db.execute_query(query, (name, email, phone, membership_type))
    
    def get_all_members(self):
        """获取所有会员"""
        query = '''
            SELECT member_id, name, email, phone, 
                   DATE(join_date) as join_date, status, total_books_borrowed
            FROM members
            ORDER BY name
        '''
        return self.db.fetch_all(query)
    
    def get_member_by_id(self, member_id):
        """根据ID获取会员"""
        query = '''
            SELECT member_id, name, email, phone, membership_type, 
                   DATE(join_date) as join_date, status, total_books_borrowed
            FROM members
            WHERE member_id = ?
        '''
        return self.db.fetch_one(query, (member_id,))
    
    def search_members(self, search_term, search_type='all'):
        """搜索会员"""
        if not search_term:
            return self.get_all_members()
        
        search_term = f"%{search_term}%"
        
        if search_type == 'name':
            query = '''
                SELECT member_id, name, email, phone, DATE(join_date), status
                FROM members
                WHERE name LIKE ?
                ORDER BY name
            '''
            params = (search_term,)
        elif search_type == 'email':
            query = '''
                SELECT member_id, name, email, phone, DATE(join_date), status
                FROM members
                WHERE email LIKE ?
                ORDER BY name
            '''
            params = (search_term,)
        elif search_type == 'phone':
            query = '''
                SELECT member_id, name, email, phone, DATE(join_date), status
                FROM members
                WHERE phone LIKE ?
                ORDER BY name
            '''
            params = (search_term,)
        else:  # all
            query = '''
                SELECT member_id, name, email, phone, DATE(join_date), status
                FROM members
                WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
                ORDER BY name
            '''
            params = (search_term, search_term, search_term)
        
        return self.db.fetch_all(query, params)
    
    def update_member(self, member_id, name, email, phone, status):
        """更新会员信息"""
        query = '''
            UPDATE members
            SET name = ?, email = ?, phone = ?, status = ?
            WHERE member_id = ?
        '''
        return self.db.execute_query(query, (name, email, phone, status, member_id))
    
    def delete_member(self, member_id):
        """删除会员"""
        # 检查是否有未归还的书籍
        check_query = '''
            SELECT COUNT(*) FROM transactions 
            WHERE member_id = ? AND return_date IS NULL
        '''
        result = self.db.fetch_one(check_query, (member_id,))
        
        if result and result[0] > 0:
            return False  # 有未归还的书籍，不能删除
        
        query = 'DELETE FROM members WHERE member_id = ?'
        return self.db.execute_query(query, (member_id,))
    
    def update_books_borrowed(self, member_id, change):
        """更新借书数量"""
        query = '''
            UPDATE members
            SET total_books_borrowed = total_books_borrowed + ?
            WHERE member_id = ?
        '''
        return self.db.execute_query(query, (change, member_id))
    
    def get_active_members(self):
        """获取活跃会员"""
        query = '''
            SELECT member_id, name, email, phone, DATE(join_date), status
            FROM members
            WHERE status = 'Active'
            ORDER BY name
        '''
        return self.db.fetch_all(query)