import sqlite3
import pandas as pd
from datetime import datetime
from contextlib import contextmanager

class Database:
    def __init__(self, db_name='finance.db'):
        self.db_name = db_name
        self._ensure_tables_exist()
        self.income_categories = []
        self.expense_categories = []
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()
    
    def _ensure_tables_exist(self):
        with self._get_connection() as conn:
            # Bảng giao dịch
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ngay TEXT,
                    loai TEXT,
                    danh_muc TEXT,
                    so_tien REAL,
                    mo_ta TEXT
                )
            ''')
            
            # Bảng số dư ban đầu
            conn.execute('''
                CREATE TABLE IF NOT EXISTS balance (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    amount REAL DEFAULT 0
                )
            ''')
            
            # Bảng ngân sách
            conn.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    amount REAL
                )
            ''')
            
            # Bảng nhắc nhở
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    due_date TEXT,
                    amount REAL,
                    category TEXT
                )
            ''')
            
            # Bảng mục tiêu tiết kiệm
            conn.execute('''
                CREATE TABLE IF NOT EXISTS saving_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    amount REAL,
                    target_date TEXT
                )
            ''')
            
            # Bảng danh mục
            conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT,
                    name TEXT,
                    UNIQUE(type, name)
                )
            ''')
            
            conn.commit()
    
    def load_categories(self):
        with self._get_connection() as conn:
            # Load existing categories
            self.income_categories = [row[0] for row in 
                conn.execute("SELECT name FROM categories WHERE type = 'income'")]
            self.expense_categories = [row[0] for row in 
                conn.execute("SELECT name FROM categories WHERE type = 'expense'")]
            
            print("[DEBUG] Danh mục thu từ database:", self.income_categories)  # <-- Thêm dòng này
            print("[DEBUG] Danh mục chi từ database:", self.expense_categories)  # <-- Thêm dòng này


            # Thêm danh mục thu mặc định nếu chưa tồn tại
            default_income = ['Lương', 'Thưởng', 'Đầu tư', 'Kinh doanh', 'Quà tặng', 'Khác']
            for cat in default_income:
                if cat not in self.income_categories:
                    self.add_category('income', cat)  # Chỉ thêm nếu chưa có

            # Thêm danh mục chi mặc định nếu chưa tồn tại
            default_expense = ['Ăn uống', 'Nhà ở', 'Đi lại', 'Giải trí', 'Y tế', 'Giáo dục', 'Tiết kiệm', 'Khác']
            for cat in default_expense:
                if cat not in self.expense_categories:
                    self.add_category('expense', cat)  # Chỉ thêm nếu chưa có

            print("[DEBUG] Income categories after load:", self.income_categories)
            print("[DEBUG] Expense categories after load:", self.expense_categories)
            print("[DEBUG] Danh mục chi trong database:", self.expense_categories)
            
            # Thêm danh mục mặc định
            for cat in default_income:
                if cat not in self.income_categories:
                    print(f"[DEBUG] Adding income category: {cat}")
                    self.add_category('income', cat)
            
            for cat in default_expense:
                if cat not in self.expense_categories:
                    print(f"[DEBUG] Adding expense category: {cat}")
                    self.add_category('expense', cat)  # <-- Đảm bảo đúng chính tả
    
    def add_category(self, category_type, name):
        with self._get_connection() as conn:
            try:
                conn.execute("INSERT INTO categories (type, name) VALUES (?, ?)", 
                            (category_type, name))
                conn.commit()
                
                if category_type == 'income':
                    self.income_categories.append(name)
                else:
                    self.expense_categories.append(name)
            except sqlite3.IntegrityError:
                pass
    
    def add_initial_balance(self, amount):
        with self._get_connection() as conn:
            conn.execute('INSERT OR REPLACE INTO balance (id, amount) VALUES (1, ?)', (amount,))
            conn.commit()
    
    def add_transaction(self, date, trans_type, category, amount, description):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO transactions (ngay, loai, danh_muc, so_tien, mo_ta)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, trans_type, category, amount, description))
            conn.commit()
    
    def load_transactions(self):
        with self._get_connection() as conn:
            try:
                return pd.read_sql('SELECT * FROM transactions', conn, parse_dates=['ngay'])
            except:
                return pd.DataFrame(columns=['id', 'ngay', 'loai', 'danh_muc', 'so_tien', 'mo_ta'])
    
    def get_balance(self):
        with self._get_connection() as conn:
            balance = conn.execute('SELECT amount FROM balance WHERE id = 1').fetchone()
            if balance:
                initial_balance = balance[0]
            else:
                initial_balance = 0
            
            transactions = pd.read_sql('SELECT * FROM transactions', conn)
            if not transactions.empty:
                income = transactions[transactions['loai'] == 'Thu']['so_tien'].sum()
                expense = transactions[transactions['loai'] == 'Chi']['so_tien'].sum()
                return initial_balance + income - expense
            return initial_balance
    
    def get_category_summary(self):
        with self._get_connection() as conn:
            transactions = pd.read_sql('SELECT * FROM transactions', conn)
            if not transactions.empty:
                return transactions[transactions['loai'] == 'Chi'].groupby('danh_muc')['so_tien'].sum().to_dict()
            return {}
    
    def set_budget(self, category, amount):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO budgets (category, amount)
                VALUES (?, ?)
            ''', (category, amount))
            conn.commit()
    
    def get_budgets(self):
        with self._get_connection() as conn:
            budgets = conn.execute('SELECT category, amount FROM budgets').fetchall()
            return dict(budgets)
    
    def add_reminder(self, name, due_date, amount, category):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO reminders (name, due_date, amount, category)
                VALUES (?, ?, ?, ?)
            ''', (name, due_date, amount, category))
            conn.commit()
    
    def get_reminders(self):
        with self._get_connection() as conn:
            try:
                return pd.read_sql('SELECT * FROM reminders', conn)
            except:
                return pd.DataFrame(columns=['id', 'name', 'due_date', 'amount', 'category'])
    
    def add_saving_goal(self, name, amount, target_date):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT INTO saving_goals (name, amount, target_date)
                VALUES (?, ?, ?)
            ''', (name, amount, target_date))
            conn.commit()
    
    def get_saving_goals(self):
        with self._get_connection() as conn:
            try:
                return pd.read_sql('SELECT * FROM saving_goals', conn)
            except:
                return pd.DataFrame(columns=['id', 'name', 'amount', 'target_date'])
    
    def reset_data(self):
        with self._get_connection() as conn:
            conn.execute('DELETE FROM transactions')
            conn.execute('DELETE FROM balance')
            conn.execute('DELETE FROM budgets')
            conn.execute('DELETE FROM reminders')
            conn.execute('DELETE FROM saving_goals')
            conn.commit()