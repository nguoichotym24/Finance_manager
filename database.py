import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
from contextlib import contextmanager

class Database:
    def __init__(self, db_name='finance.db'):
        self.db_name = db_name
        self._ensure_tables_exist()
        self.income_categories = []
        self.expense_categories = []
        self.load_categories()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()
    
    def _ensure_tables_exist(self):
        with self._get_connection() as conn:
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
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS balance (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    amount REAL DEFAULT 0
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    amount REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    due_date TEXT,
                    amount REAL,
                    category TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS saving_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    amount REAL,
                    target_date TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT,
                    name TEXT,
                    UNIQUE(type, name)
                )
            ''')
            
            conn.commit()
    
    def load_categories(self, language='vi'):  # Đảm bảo phương thức này tồn tại
        with self._get_connection() as conn:
            self.income_categories = [row[0] for row in 
                conn.execute("SELECT name FROM categories WHERE type = 'income'")]
            self.expense_categories = [row[0] for row in 
                conn.execute("SELECT name FROM categories WHERE type = 'expense'")]
            
            if not self.income_categories:
                # Phần thêm danh mục mặc định theo ngôn ngữ
                if language == 'vi':
                    default_income = ['Lương', 'Thưởng', 'Đầu tư', 'Kinh doanh', 'Quà tặng', 'Khác']
                else:
                    default_income = ['Salary', 'Bonus', 'Investment', 'Business', 'Gift', 'Other']
                
                for cat in default_income:
                    self.add_category('income', cat)
            
            if not self.expense_categories:
                if language == 'vi':
                    default_expense = ['Ăn uống', 'Nhà ở', 'Đi lại', 'Giải trí', 'Y tế', 'Giáo dục', 'Tiết kiệm', 'Khác']
                else:
                    default_expense = ['Food', 'Housing', 'Transport', 'Entertainment', 'Healthcare', 'Education', 'Savings', 'Other']
                
                for cat in default_expense:
                    self.add_category('expense', cat)
    
    def add_category(self, category_type, name):
        with self._get_connection() as conn:
            try:
                conn.execute("INSERT INTO categories (type, name) VALUES (?, ?)", 
                            (category_type, name))
                conn.commit()
                
                if category_type == 'income':
                    if name not in self.income_categories:
                        self.income_categories.append(name)
                else:
                    if name not in self.expense_categories:
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