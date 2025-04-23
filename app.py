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

# --- Cấu trúc menu chính ---
menu_options = {
    "🏠 Tổng quan": "overview",
    "💸 Quản lý giao dịch": {
        "➕ Thêm giao dịch mới": "add_transaction",
        "📋 Xem lịch sử giao dịch": "view_transactions",
        "📊 Phân tích chi tiêu": "expense_analysis"
    },
    "📋 Quản lý danh mục": "manage_categories",
    "💰 Quản lý ngân sách": "manage_budgets",
    "⏰ Nhắc nhở thanh toán": "payment_reminders",
    "🎯 Mục tiêu tiết kiệm": "saving_goals",
    "⚙️ Cài đặt & Dữ liệu": "settings"
}

# --- Sidebar menu ---
with st.sidebar:
    st.header("📌 Menu chính")
    
    # Tạo menu đa cấp
    selected_menu = st.selectbox(
        "Chọn chức năng",
        options=list(menu_options.keys()),
        key="main_menu"
    )
    
    # Xác định mục được chọn
    if isinstance(menu_options[selected_menu], dict):
        submenu = st.selectbox(
            "Chọn mục con",
            options=list(menu_options[selected_menu].keys()),
            key="sub_menu"
        )
        selected_option = menu_options[selected_menu][submenu]
    else:
        selected_option = menu_options[selected_menu]

# --- Main content dựa trên menu được chọn ---
transactions = st.session_state.db.load_transactions()
balance = st.session_state.db.get_balance()

if selected_option == "overview":
    # --- Trang tổng quan ---
    st.header('🏠 Tổng quan tài chính')
    
    # Hiển thị các chỉ số chính
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Số dư hiện tại', format_currency(balance))
    with col2:
        total_income = transactions[transactions['loai'] == 'Thu']['so_tien'].sum()
        st.metric('Tổng thu nhập', format_currency(total_income))
    with col3:
        total_expense = transactions[transactions['loai'] == 'Chi']['so_tien'].sum()
        st.metric('Tổng chi tiêu', format_currency(total_expense))
    
    # Biểu đồ tổng quan
    if not transactions.empty:
        st.subheader('📈 Biểu đồ chi tiêu tháng này')
        st.plotly_chart(create_expense_by_category_chart(st.session_state.db.get_category_summary()))
        
        st.subheader('📅 Lịch sử giao dịch gần đây')
        st.dataframe(
            transactions.head(5).rename(columns={
                'ngay': 'Ngày',
                'loai': 'Loại',
                'danh_muc': 'Danh mục',
                'so_tien': 'Số tiền',
                'mo_ta': 'Mô tả'
            }),
            hide_index=True
        )

elif selected_option == "add_transaction":
    st.header('💸 Thêm giao dịch mới')
    
    # Tách selectbox ra khỏi form chính để có thể tự động rerun
    trans_type = st.radio(
        "Loại giao dịch",
        ["Thu", "Chi"],
        horizontal=True,
        key="trans_type_radio"
    )
    
    # Lấy danh mục tương ứng
    categories = (
        st.session_state.db.income_categories 
        if trans_type == "Thu" 
        else st.session_state.db.expense_categories
    )
    
    # Form chính
    with st.form("transaction_form"):
        date = st.date_input("Ngày", datetime.now())
        category = st.selectbox("Danh mục", categories)
        amount = st.number_input("Số tiền", min_value=0)
        description = st.text_input("Mô tả")
        
        submitted = st.form_submit_button("💾 Lưu giao dịch")
        
        # Debug (có thể bỏ sau khi kiểm tra)
        st.write(f"Đang chọn: {trans_type}")
        st.write(f"Danh mục hiển thị: {categories}")

    if submitted:
        try:
            st.session_state.db.add_transaction(
                date.strftime('%Y-%m-%d'),
                trans_type,
                category,
                amount,
                description
            )
            st.success("Giao dịch đã được lưu!")
        except Exception as e:
            st.error(f"Lỗi: {str(e)}")

elif selected_option == "view_transactions":
    # --- Xem lịch sử giao dịch ---
    st.header('📋 Lịch sử giao dịch')
    
    if not transactions.empty:
        # Bộ lọc
        with st.expander("🔍 Bộ lọc"):
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_type = st.selectbox('Loại giao dịch', ['Tất cả', 'Thu', 'Chi'])
            with col2:
                filter_category = st.selectbox('Danh mục', ['Tất cả'] + st.session_state.db.expense_categories + st.session_state.db.income_categories)
            with col3:
                date_range = st.date_input('Khoảng thời gian', [transactions['ngay'].min(), transactions['ngay'].max()])
        
        # Áp dụng bộ lọc
        filtered_transactions = transactions.copy()
        if filter_type != 'Tất cả':
            filtered_transactions = filtered_transactions[filtered_transactions['loai'] == filter_type]
        if filter_category != 'Tất cả':
            filtered_transactions = filtered_transactions[filtered_transactions['danh_muc'] == filter_category]
        if len(date_range) == 2:
            filtered_transactions = filtered_transactions[
                (filtered_transactions['ngay'] >= pd.to_datetime(date_range[0])) & 
                (filtered_transactions['ngay'] <= pd.to_datetime(date_range[1]))]
        
        # Hiển thị bảng
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
            height=500
        )
        
        # Xuất báo cáo
        st.download_button(
            label="📥 Tải xuống CSV",
            data=filtered_transactions.to_csv(index=False).encode('utf-8'),
            file_name='bao_cao_giao_dich.csv',
            mime='text/csv'
        )
    else:
        st.info('Chưa có giao dịch nào.')

elif selected_option == "expense_analysis":
    # --- Phân tích chi tiêu ---
    st.header('📊 Phân tích chi tiêu')
    
    if not transactions.empty:
        tab1, tab2 = st.tabs(["Phân bổ chi tiêu", "Xu hướng chi tiêu"])
        
        with tab1:
            st.subheader('Phân bổ chi tiêu theo danh mục')
            st.plotly_chart(create_expense_by_category_chart(st.session_state.db.get_category_summary()))
        
        with tab2:
            st.subheader('Xu hướng chi tiêu theo thời gian')
            st.plotly_chart(create_expense_trend_chart(transactions))
            
            st.subheader('Phân tích theo chu kỳ')
            time_period = st.selectbox('Chọn khoảng thời gian', ['Theo tháng', 'Theo quý', 'Theo năm'])
            
            if time_period == 'Theo tháng':
                transactions['period'] = transactions['ngay'].dt.to_period('M').astype(str)
            elif time_period == 'Theo quý':
                transactions['period'] = transactions['ngay'].dt.to_period('Q').astype(str)
            else:
                transactions['period'] = transactions['ngay'].dt.to_period('Y').astype(str)
            
            period_summary = transactions.groupby(['period', 'loai'])['so_tien'].sum().unstack().fillna(0)
            st.bar_chart(period_summary)
    else:
        st.info('Chưa có dữ liệu để phân tích.')

elif selected_option == "manage_categories":
    # --- Quản lý danh mục ---
    st.header('📋 Quản lý danh mục')
    
    tab1, tab2 = st.tabs(["Danh mục thu", "Danh mục chi"])
    
    with tab1:
        st.subheader("📥 Danh mục thu nhập")
        st.dataframe(pd.DataFrame(st.session_state.db.income_categories, columns=["Danh mục"]), hide_index=True)
        
        with st.form("add_income_category"):
            new_category = st.text_input("Thêm danh mục thu mới")
            submitted = st.form_submit_button("➕ Thêm")
            if submitted and new_category:
                st.session_state.db.add_category('income', new_category)
                st.success(f'Đã thêm danh mục "{new_category}"')
                st.rerun()
    
    with tab2:
        st.subheader("📤 Danh mục chi tiêu")
        st.dataframe(pd.DataFrame(st.session_state.db.expense_categories, columns=["Danh mục"]), hide_index=True)
        
        with st.form("add_expense_category"):
            new_category = st.text_input("Thêm danh mục chi mới")
            submitted = st.form_submit_button("➕ Thêm")
            if submitted and new_category:
                st.session_state.db.add_category('expense', new_category)
                st.success(f'Đã thêm danh mục "{new_category}"')
                st.rerun()

elif selected_option == "manage_budgets":
    # --- Quản lý ngân sách ---
    st.header('💰 Quản lý ngân sách')
    
    # Thêm/Sửa ngân sách
    with st.form("budget_form"):
        col1, col2 = st.columns(2)
        with col1:
            budget_category = st.selectbox('Danh mục', st.session_state.db.expense_categories)
        with col2:
            budget_amount = st.number_input('Số tiền ngân sách', min_value=0)
        
        submitted = st.form_submit_button("💾 Lưu ngân sách")
        if submitted:
            st.session_state.db.set_budget(budget_category, budget_amount)
            st.success(f'Đã đặt ngân sách {budget_category}: {format_currency(budget_amount)}')
            st.rerun()
    
    # Hiển thị ngân sách hiện tại
    budgets = st.session_state.db.get_budgets()
    if budgets:
        st.subheader('📊 Theo dõi ngân sách hiện tại')
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

elif selected_option == "payment_reminders":
    # --- Nhắc nhở thanh toán ---
    st.header('⏰ Nhắc nhở thanh toán')
    
    # Thêm nhắc nhở mới
    with st.form("reminder_form"):
        col1, col2 = st.columns(2)
        with col1:
            reminder_name = st.text_input('Tên nhắc nhở')
        with col2:
            reminder_date = st.date_input('Ngày đến hạn')
        
        col1, col2 = st.columns(2)
        with col1:
            reminder_amount = st.number_input('Số tiền', min_value=0)
        with col2:
            reminder_category = st.selectbox('Danh mục', st.session_state.db.expense_categories)
        
        submitted = st.form_submit_button("➕ Thêm nhắc nhở")
        if submitted:
            st.session_state.db.add_reminder(
                reminder_name,
                reminder_date.strftime('%Y-%m-%d'),
                reminder_amount,
                reminder_category
            )
            st.success('Đã thêm nhắc nhở!')
            st.rerun()
    
    # Hiển thị danh sách nhắc nhở
    reminders = st.session_state.db.get_reminders()
    if not reminders.empty:
        st.subheader('📋 Danh sách nhắc nhở')
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

elif selected_option == "saving_goals":
    # --- Mục tiêu tiết kiệm ---
    st.header('🎯 Mục tiêu tiết kiệm')
    
    # Thêm mục tiêu mới
    with st.form("goal_form"):
        col1, col2 = st.columns(2)
        with col1:
            goal_name = st.text_input('Tên mục tiêu')
        with col2:
            goal_amount = st.number_input('Số tiền mục tiêu', min_value=0)
        
        target_date = st.date_input('Ngày hoàn thành')
        
        submitted = st.form_submit_button("➕ Thêm mục tiêu")
        if submitted:
            st.session_state.db.add_saving_goal(
                goal_name,
                goal_amount,
                target_date.strftime('%Y-%m-%d')
            )
            st.success('Đã thêm mục tiêu!')
            st.rerun()
    
    # Hiển thị danh sách mục tiêu
    goals = st.session_state.db.get_saving_goals()
    if not goals.empty:
        st.subheader('📋 Danh sách mục tiêu')
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

elif selected_option == "settings":
    # --- Cài đặt & Dữ liệu ---
    st.header('⚙️ Cài đặt & Dữ liệu')
    
    # Số dư ban đầu
    st.subheader('💰 Số dư ban đầu')
    initial_balance = st.number_input('Nhập số tiền hiện có', min_value=0)
    if st.button('Cập nhật số dư'):
        try:
            st.session_state.db.add_initial_balance(initial_balance)
            st.success('Đã cập nhật số dư ban đầu!')
            st.rerun()
        except Exception as e:
            st.error(f'Lỗi: {str(e)}')
    
    # Quản lý dữ liệu
    st.subheader('🗄️ Quản lý dữ liệu')
    
    if st.button('🔄 Làm mới dữ liệu'):
        st.session_state.db.load_categories()
        st.rerun()
        st.success('Đã làm mới dữ liệu!')
    
    st.divider()
    
    # Xóa dữ liệu
    st.subheader('⚠️ Xóa dữ liệu')
    
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False
    
    if st.button('🗑️ Xóa tất cả dữ liệu'):
        st.session_state.show_delete_confirmation = True
    
    if st.session_state.show_delete_confirmation:
        st.warning('Bạn có chắc chắn muốn xóa tất cả dữ liệu?')
        col1, col2 = st.columns(2)
        with col1:
            if st.button('✅ Xác nhận'):
                st.session_state.db.reset_data()
                st.success('Đã xóa tất cả dữ liệu!')
                st.session_state.show_delete_confirmation = False
                st.rerun()
        with col2:
            if st.button('❌ Hủy bỏ'):
                st.session_state.show_delete_confirmation = False
                st.rerun()