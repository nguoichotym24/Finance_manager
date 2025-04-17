import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from database import Database
from utils import create_expense_by_category_chart, create_expense_trend_chart, format_currency

# Khởi tạo session state
if 'db' not in st.session_state:
    st.session_state.db = Database()
    st.session_state.db.load_categories()

# Tiêu đề ứng dụng
st.title('💰 Quản lý Tài chính Cá nhân')

# --- Phần xác thực ---
with st.sidebar:
    st.subheader('🔐 Bảo mật')
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        password = st.text_input('Mật khẩu', type='password', key='auth_password')
        if st.button('Đăng nhập'):
            if hashlib.sha256(password.encode()).hexdigest() == '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92':
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error('Mật khẩu không đúng')
    else:
        st.success('Đã đăng nhập')
        if st.button('Đăng xuất'):
            st.session_state.authenticated = False
            st.rerun()

if not st.session_state.authenticated:
    st.warning('Vui lòng đăng nhập để sử dụng ứng dụng')
    st.stop()

# --- Sidebar cho nhập liệu ---
with st.sidebar:
    st.header('📝 Nhập giao dịch mới')

    # Thêm phần nhập số dư ban đầu
    st.subheader('💰 Số dư ban đầu')
    initial_balance = st.number_input('Nhập số tiền hiện có', min_value=0, key='initial_balance')
    if st.button('Cập nhật số dư'):
        try:
            st.session_state.db.add_initial_balance(initial_balance)
            st.success('Đã cập nhật số dư ban đầu!')
            st.rerun()
        except Exception as e:
            st.error(f'Lỗi: {str(e)}')

    st.divider()

    # Phần nhập giao dịch
    st.subheader('➕ Thêm giao dịch')
    date = st.date_input('Ngày', datetime.now(), key='transaction_date')
    trans_type = st.selectbox('Loại giao dịch', ['Thu', 'Chi'], key='transaction_type')
    
    # Hiển thị danh mục phù hợp
    if trans_type == 'Thu':
        categories = st.session_state.db.income_categories
    else:
        categories = st.session_state.db.expense_categories
    
    col1, col2 = st.columns([3, 1])
    with col1:
        category = st.selectbox('Danh mục', categories, key='transaction_category')
    with col2:
        st.write("")
        st.write("")
        with st.expander("➕"):
            new_category = st.text_input('Thêm mới', key='new_category')
            if st.button('Thêm', key='add_category'):
                if new_category:
                    st.session_state.db.add_category(trans_type.lower(), new_category)
                    st.success(f'Đã thêm danh mục "{new_category}"')
                    st.rerun()
    
    amount = st.number_input('Số tiền', min_value=0, key='transaction_amount')
    description = st.text_input('Mô tả', key='transaction_description')

    if st.button('💾 Lưu giao dịch', key='add_transaction'):
        try:
            st.session_state.db.add_transaction(
                date.strftime('%Y-%m-%d'),
                trans_type,
                category,
                amount,
                description
            )
            st.success('Đã thêm giao dịch thành công!')
            st.rerun()
        except Exception as e:
            st.error(f'Lỗi: {str(e)}')

    st.divider()

    # Quản lý ngân sách
    st.subheader('📊 Quản lý ngân sách')
    budget_category = st.selectbox('Danh mục', st.session_state.db.expense_categories, key='budget_category')
    budget_amount = st.number_input('Số tiền ngân sách', min_value=0, key='budget_amount')
    if st.button('💾 Lưu ngân sách', key='set_budget'):
        st.session_state.db.set_budget(budget_category, budget_amount)
        st.success(f'Đã đặt ngân sách {budget_category}: {format_currency(budget_amount)}')
        st.rerun()

    st.divider()

    # Nhắc nhở thanh toán
    st.subheader('⏰ Nhắc nhở thanh toán')
    reminder_name = st.text_input('Tên nhắc nhở', key='reminder_name')
    reminder_date = st.date_input('Ngày đến hạn', key='reminder_date')
    reminder_amount = st.number_input('Số tiền', min_value=0, key='reminder_amount')
    reminder_category = st.selectbox('Danh mục', st.session_state.db.expense_categories, key='reminder_category')
    
    if st.button('➕ Thêm nhắc nhở', key='add_reminder'):
        st.session_state.db.add_reminder(
            reminder_name,
            reminder_date.strftime('%Y-%m-%d'),
            reminder_amount,
            reminder_category
        )
        st.success('Đã thêm nhắc nhở!')
        st.rerun()

    st.divider()

    # Mục tiêu tiết kiệm
    st.subheader('🎯 Mục tiêu tiết kiệm')
    goal_name = st.text_input('Tên mục tiêu', key='goal_name')
    goal_amount = st.number_input('Số tiền mục tiêu', min_value=0, key='goal_amount')
    target_date = st.date_input('Ngày hoàn thành', key='target_date')
    
    if st.button('➕ Thêm mục tiêu', key='add_goal'):
        st.session_state.db.add_saving_goal(
            goal_name,
            goal_amount,
            target_date.strftime('%Y-%m-%d')
        )
        st.success('Đã thêm mục tiêu!')
        st.rerun()

    st.divider()

    # Xóa dữ liệu
    st.subheader('⚠️ Quản lý dữ liệu')
    
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False
    
    if st.button('🗑️ Xóa tất cả dữ liệu', key='delete_button'):
        st.session_state.show_delete_confirmation = True
    
    if st.session_state.show_delete_confirmation:
        st.warning('Bạn có chắc chắn muốn xóa tất cả dữ liệu?')
        col1, col2 = st.columns(2)
        with col1:
            if st.button('✅ Xác nhận', key='confirm_delete'):
                st.session_state.db.reset_data()
                st.success('Đã xóa tất cả dữ liệu!')
                st.session_state.show_delete_confirmation = False
                st.rerun()
        with col2:
            if st.button('❌ Hủy bỏ', key='cancel_delete'):
                st.session_state.show_delete_confirmation = False
                st.rerun()

# --- Main content ---
transactions = st.session_state.db.load_transactions()
balance = st.session_state.db.get_balance()

# Tổng quan
st.header('📊 Tổng quan')
col1, col2, col3 = st.columns(3)
with col1:
    st.metric('Số dư hiện tại', format_currency(balance))
with col2:
    total_income = transactions[transactions['loai'] == 'Thu']['so_tien'].sum()
    st.metric('Tổng thu nhập', format_currency(total_income))
with col3:
    total_expense = transactions[transactions['loai'] == 'Chi']['so_tien'].sum()
    st.metric('Tổng chi tiêu', format_currency(total_expense))

# Theo dõi ngân sách
budgets = st.session_state.db.get_budgets()
if budgets:
    st.subheader('📈 Theo dõi ngân sách')
    expenses_by_category = st.session_state.db.get_category_summary()
    
    for category, budget in budgets.items():
        spent = expenses_by_category.get(category, 0)
        progress = min(spent / budget * 100, 100) if budget > 0 else 0
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write(f"**{category}**")
            st.write(f"{format_currency(spent)} / {format_currency(budget)}")
        with col2:
            st.progress(int(progress))
            if spent > budget:
                st.warning(f"Vượt ngân sách {format_currency(spent - budget)}")

# Nhắc nhở thanh toán
reminders = st.session_state.db.get_reminders()
if not reminders.empty:
    st.header('🔔 Nhắc nhở thanh toán')
    today = datetime.now().date()
    
    for _, row in reminders.iterrows():
        due_date = datetime.strptime(row['due_date'], '%Y-%m-%d').date()
        days_left = (due_date - today).days
        
        if days_left < 0:
            st.error(f"**QUÁ HẠN**: {row['name']} - {format_currency(row['amount'])} - {row['category']} (Quá hạn {abs(days_left)} ngày)")
        elif days_left <= 7:
            st.warning(f"**SẮP ĐẾN HẠN**: {row['name']} - {format_currency(row['amount'])} - {row['category']} (Còn {days_left} ngày)")
        else:
            st.info(f"{row['name']} - {format_currency(row['amount'])} - {row['category']} (Còn {days_left} ngày)")

# Mục tiêu tiết kiệm
goals = st.session_state.db.get_saving_goals()
if not goals.empty:
    st.header('🏆 Mục tiêu tiết kiệm')
    today = datetime.now().date()
    
    for _, row in goals.iterrows():
        target_date = datetime.strptime(row['target_date'], '%Y-%m-%d').date()
        days_left = (target_date - today).days
        progress = min(balance / row['amount'] * 100, 100)
        
        st.subheader(row['name'])
        st.progress(int(progress))
        st.write(f"{format_currency(balance)} / {format_currency(row['amount'])} ({progress:.1f}%)")
        st.write(f"⏳ Còn {days_left} ngày để hoàn thành")
        
        if balance >= row['amount']:
            st.balloons()
            st.success("🎉 Chúc mừng! Bạn đã đạt được mục tiêu!")

# Phân tích chi tiêu
if not transactions.empty:
    st.header('📊 Phân tích chi tiêu')

    # Biểu đồ phân bổ chi tiêu
    st.subheader('Phân bổ chi tiêu theo danh mục')
    category_summary = st.session_state.db.get_category_summary()
    st.plotly_chart(create_expense_by_category_chart(category_summary))

    # Biểu đồ xu hướng
    st.subheader('Xu hướng chi tiêu theo thời gian')
    st.plotly_chart(create_expense_trend_chart(transactions))

    # Phân tích theo thời gian
    st.subheader('Phân tích theo thời gian')
    time_period = st.selectbox('Chọn khoảng thời gian', ['Theo tháng', 'Theo quý', 'Theo năm'], key='time_period')

    if time_period == 'Theo tháng':
        transactions['period'] = transactions['ngay'].dt.to_period('M').astype(str)
    elif time_period == 'Theo quý':
        transactions['period'] = transactions['ngay'].dt.to_period('Q').astype(str)
    else:
        transactions['period'] = transactions['ngay'].dt.to_period('Y').astype(str)

    period_summary = transactions.groupby(['period', 'loai'])['so_tien'].sum().unstack().fillna(0)
    st.bar_chart(period_summary)

    # Lịch sử giao dịch
    st.header('📋 Lịch sử giao dịch')
    transactions['ngay'] = pd.to_datetime(transactions['ngay'])
    transactions = transactions.sort_values('ngay', ascending=False)

    # Thêm bộ lọc
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox('Loại giao dịch', ['Tất cả', 'Thu', 'Chi'], key='filter_type')
    with col2:
        filter_category = st.selectbox('Danh mục', ['Tất cả'] + st.session_state.db.expense_categories + st.session_state.db.income_categories, key='filter_category')
    with col3:
        date_range = st.date_input('Khoảng thời gian', [transactions['ngay'].min(), transactions['ngay'].max()], key='date_range')

    filtered_transactions = transactions.copy()
    if filter_type != 'Tất cả':
        filtered_transactions = filtered_transactions[filtered_transactions['loai'] == filter_type]
    if filter_category != 'Tất cả':
        filtered_transactions = filtered_transactions[filtered_transactions['danh_muc'] == filter_category]
    if len(date_range) == 2:
        filtered_transactions = filtered_transactions[
            (filtered_transactions['ngay'] >= pd.to_datetime(date_range[0])) & 
            (filtered_transactions['ngay'] <= pd.to_datetime(date_range[1]))
        ]

    st.dataframe(
        filtered_transactions.rename(columns={
            'ngay': 'Ngày',
            'loai': 'Loại',
            'danh_muc': 'Danh mục',
            'so_tien': 'Số tiền',
            'mo_ta': 'Mô tả'
        }),
        hide_index=True,
        use_container_width=True,
        height=400
    )

    # Xuất báo cáo
    st.header('📤 Xuất báo cáo')
    if st.button('📥 Tải xuống báo cáo CSV'):
        transactions.to_csv('bao_cao_tai_chinh.csv', index=False)
        st.success('Đã tạo file báo cáo "bao_cao_tai_chinh.csv"')
else:
    st.info('Chưa có giao dịch nào. Hãy thêm giao dịch mới ở menu bên trái.')