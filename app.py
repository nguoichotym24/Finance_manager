import streamlit as st
import pandas as pd
import json
from datetime import datetime
import hashlib
from database import Database
from utils import create_expense_by_category_chart, create_expense_trend_chart, format_currency
from i18n import translator

# Khởi tạo session state
if 'db' not in st.session_state:
    st.session_state.db = Database()
    st.session_state.db.load_categories()

# Thêm sau phần khởi tạo session state
if 'translator' not in st.session_state:
    st.session_state.translator = translator
    st.session_state.translator.load_translations()  # Force reload translations

# Tiêu đề ứng dụng
st.title(translator.t("app_title"))

# --- Phần xác thực ---
with st.sidebar:
    st.subheader(f'🔐 {translator.t("security")}')
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        password = st.text_input(translator.t("password"), type='password', key='auth_password')
        if st.button(translator.t("login_button")):
            if hashlib.sha256(password.encode()).hexdigest() == '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92':
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error(translator.t("wrong_password"))
    else:
        st.success(translator.t("logged_in"))
        if st.button(translator.t("logout_button")):
            st.session_state.authenticated = False
            st.rerun()

    # Chọn ngôn ngữ
    lang = st.selectbox("🌐", ["Việt Nam", "English"], index=0 if translator.current_language == 'vi' else 1)
    translator.set_language('vi' if lang == 'Việt Nam' else 'en')

if not st.session_state.authenticated:
    st.warning(translator.t("login_warning"))
    st.stop()

# --- Cấu trúc menu chính ---
menu_options = {
    translator.t("overview"): "overview",
    translator.t("transaction_management"): {
        translator.t("add_transaction"): "add_transaction",
        translator.t("view_transactions"): "view_transactions",
        translator.t("expense_analysis"): "expense_analysis"
    },
    translator.t("manage_categories"): "manage_categories",
    translator.t("manage_budgets"): "manage_budgets",
    translator.t("payment_reminders"): "payment_reminders",
    translator.t("saving_goals"): "saving_goals",
    translator.t("settings"): "settings"
}

# --- Sidebar menu ---
with st.sidebar:
    st.header(translator.t("main_menu"))
    
    selected_main = st.selectbox(
        translator.t("select_function"),
        options=list(menu_options.keys()),
        key="main_menu"
    )
    
    # Xử lý submenu
    selected_option = menu_options[selected_main]
    if isinstance(selected_option, dict):
        selected_sub = st.selectbox(
            translator.t("select_submenu"),
            options=list(selected_option.keys()),
            key="sub_menu"
        )
        selected_option = selected_option[selected_sub]

# --- Main content ---
transactions = st.session_state.db.load_transactions()
balance = st.session_state.db.get_balance()

if selected_option == "overview":
    st.header(f'🏠 {translator.t("overview")}')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(translator.t("current_balance"), format_currency(balance))
    with col2:
        total_income = transactions[transactions['loai'] == 'Thu']['so_tien'].sum()
        st.metric(translator.t("total_income"), format_currency(total_income))
    with col3:
        total_expense = transactions[transactions['loai'] == 'Chi']['so_tien'].sum()
        st.metric(translator.t("total_expense"), format_currency(total_expense))
    
    if not transactions.empty:
        st.subheader(translator.t("expense_by_category"))
        st.plotly_chart(create_expense_by_category_chart(st.session_state.db.get_category_summary()))
        
        st.subheader(translator.t("recent_transactions"))
        st.dataframe(
            transactions.head(5).rename(columns={
                'ngay': translator.t("date"),
                'loai': translator.t("type"),
                'danh_muc': translator.t("category"),
                'so_tien': translator.t("amount"),
                'mo_ta': translator.t("description")
            }),
            hide_index=True
        )

elif selected_option == "add_transaction":
    st.header(f'💸 {translator.t("add_transaction")}')
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input(translator.t("date"), datetime.now())
        with col2:
            trans_type = st.selectbox(translator.t("type"), [translator.t("income"), translator.t("expense")])
        
        categories = (st.session_state.db.income_categories if trans_type == translator.t("income") 
                     else st.session_state.db.expense_categories)
        category = st.selectbox(translator.t("category"), categories)
        amount = st.number_input(translator.t("amount"), min_value=0)
        description = st.text_input(translator.t("description"))
        
        submitted = st.form_submit_button(translator.t("save_transaction"))
        if submitted:
            try:
                st.session_state.db.add_transaction(
                    date.strftime('%Y-%m-%d'),
                    'Thu' if trans_type == translator.t("income") else 'Chi',
                    category,
                    amount,
                    description
                )
                st.success(translator.t("transaction_success"))
                st.rerun()
            except Exception as e:
                st.error(f"{translator.t('error')}: {str(e)}")

elif selected_option == "view_transactions":
    st.header(f'📋 {translator.t("transaction_history")}')
    
    if not transactions.empty:
        with st.expander(f"🔍 {translator.t('filter')}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_type = st.selectbox(translator.t("type"), ['All', translator.t("income"), translator.t("expense")])
            with col2:
                categories = ['All'] + st.session_state.db.expense_categories + st.session_state.db.income_categories
                filter_category = st.selectbox(translator.t("category"), categories)
            with col3:
                date_range = st.date_input(translator.t("date_range"), 
                                         [transactions['ngay'].min(), transactions['ngay'].max()])
        
        filtered_transactions = transactions.copy()
        if filter_type != 'All':
            trans_type = 'Thu' if filter_type == translator.t("income") else 'Chi'
            filtered_transactions = filtered_transactions[filtered_transactions['loai'] == trans_type]
        if filter_category != 'All':
            filtered_transactions = filtered_transactions[filtered_transactions['danh_muc'] == filter_category]
        if len(date_range) == 2:
            filtered_transactions = filtered_transactions[
                (filtered_transactions['ngay'] >= pd.to_datetime(date_range[0])) & 
                (filtered_transactions['ngay'] <= pd.to_datetime(date_range[1]))]
        
        st.dataframe(
            filtered_transactions.rename(columns={
                'ngay': translator.t("date"),
                'loai': translator.t("type"),
                'danh_muc': translator.t("category"),
                'so_tien': translator.t("amount"),
                'mo_ta': translator.t("description")
            }),
            hide_index=True,
            use_container_width=True
        )
        
        st.download_button(
            label=translator.t("download_csv"),
            data=filtered_transactions.to_csv(index=False).encode('utf-8'),
            file_name='transactions.csv',
            mime='text/csv'
        )
    else:
        st.info(translator.t("no_transactions"))

elif selected_option == "expense_analysis":
    st.header(f'📊 {translator.t("expense_analysis")}')
    
    if not transactions.empty:
        tab1, tab2 = st.tabs([
            translator.t("spending_by_category"),
            translator.t("spending_trend")
        ])
        
        with tab1:
            st.subheader(translator.t("spending_by_category"))
            category_summary = st.session_state.db.get_category_summary()
            if category_summary:
                st.plotly_chart(create_expense_by_category_chart(category_summary))
            else:
                st.info(translator.t("no_expense_data"))
        
        with tab2:
            st.subheader(translator.t("spending_trend"))
            st.plotly_chart(create_expense_trend_chart(transactions))
            
            st.subheader(translator.t("periodic_analysis"))
            period = st.selectbox(translator.t("select_period"), [
                translator.t("monthly"),
                translator.t("quarterly"),
                translator.t("yearly")
            ])
            
            period_map = {
                translator.t("monthly"): 'M',
                translator.t("quarterly"): 'Q',
                translator.t("yearly"): 'Y'
            }
            transactions['period'] = transactions['ngay'].dt.to_period(
                period_map[period]
            ).astype(str)
            
            period_summary = transactions.groupby(['period', 'loai'])['so_tien'].sum().unstack().fillna(0)
            st.bar_chart(period_summary)
    else:
        st.info(translator.t("no_transaction_data"))

elif selected_option == "manage_categories":
    st.header(f'📋 {translator.t("manage_categories")}')
    
    tab1, tab2 = st.tabs([
        translator.t("income_categories"),
        translator.t("expense_categories")
    ])
    
    with tab1:
        st.subheader(translator.t("income_categories_list"))
        income_df = pd.DataFrame(st.session_state.db.income_categories, columns=[translator.t("category")])
        st.dataframe(income_df, hide_index=True)
        
        with st.form("new_income_category"):
            new_category = st.text_input(translator.t("new_income_category"))
            if st.form_submit_button(translator.t("add_category")):
                try:
                    st.session_state.db.add_category('income', new_category)
                    st.success(translator.t("category_added"))
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
    
    with tab2:
        st.subheader(translator.t("expense_categories_list"))
        expense_df = pd.DataFrame(st.session_state.db.expense_categories, columns=[translator.t("category")])
        st.dataframe(expense_df, hide_index=True)
        
        with st.form("new_expense_category"):
            new_category = st.text_input(translator.t("new_expense_category"))
            if st.form_submit_button(translator.t("add_category")):
                try:
                    st.session_state.db.add_category('expense', new_category)
                    st.success(translator.t("category_added"))
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

elif selected_option == "manage_budgets":
    st.header(f'💰 {translator.t("manage_budgets")}')
    
    with st.form("budget_form"):
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                translator.t("select_category"),
                st.session_state.db.expense_categories
            )
        with col2:
            amount = st.number_input(
                translator.t("budget_amount"),
                min_value=0,
                step=100000
            )
        
        if st.form_submit_button(translator.t("save_budget")):
            st.session_state.db.set_budget(category, amount)
            st.success(translator.t("budget_saved"))
            st.rerun()
    
    st.subheader(translator.t("current_budgets"))
    budgets = st.session_state.db.get_budgets()
    expenses = st.session_state.db.get_category_summary()
    
    if budgets:
        for category, budget in budgets.items():
            spent = expenses.get(category, 0)
            progress = min(spent / budget * 100, 100) if budget > 0 else 0
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"**{category}**")
                st.caption(f"{format_currency(spent)} / {format_currency(budget)}")
            with col2:
                st.progress(int(progress))
                if spent > budget:
                    st.error(translator.t("budget_exceeded").format(
                        over=format_currency(spent - budget)
                    ))
    else:
        st.info(translator.t("no_budgets_set"))

elif selected_option == "payment_reminders":
    st.header(f'⏰ {translator.t("payment_reminders")}')
    
    with st.form("reminder_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(translator.t("reminder_name"))
        with col2:
            due_date = st.date_input(translator.t("due_date"))
        
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input(translator.t("amount"), min_value=0)
        with col2:
            category = st.selectbox(
                translator.t("category"),
                st.session_state.db.expense_categories
            )
        
        if st.form_submit_button(translator.t("add_reminder")):
            st.session_state.db.add_reminder(
                name,
                due_date.strftime('%Y-%m-%d'),
                amount,
                category
            )
            st.success(translator.t("reminder_added"))
            st.rerun()
    
    st.subheader(translator.t("active_reminders"))
    reminders = st.session_state.db.get_reminders()
    today = datetime.now().date()
    
    if not reminders.empty:
        for _, row in reminders.iterrows():
            due_date = datetime.strptime(row['due_date'], "%Y-%m-%d").date()  # Thêm dòng này
            days_left = (due_date - today).days
            status = ""
            
            if days_left < 0:
                status = f"❌ {translator.t('overdue')} {abs(days_left)} {translator.t('days')}"
                st.error(f"**{row['name']}** - {format_currency(row['amount'])} - {row['category']} - {status}")
            elif days_left <= 3:
                status = f"⚠️ {days_left} {translator.t('days_left')}"
                st.warning(f"**{row['name']}** - {format_currency(row['amount'])} - {row['category']} - {status}")
            else:
                status = f"⏳ {days_left} {translator.t('days_left')}"
                st.info(f"**{row['name']}** - {format_currency(row['amount'])} - {row['category']} - {status}")
    else:
        st.info(translator.t("no_active_reminders"))

elif selected_option == "saving_goals":
    st.header(f'🎯 {translator.t("saving_goals")}')
    
    with st.form("saving_goal_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(translator.t("goal_name"))
        with col2:
            target_amount = st.number_input(
                translator.t("target_amount"),
                min_value=1000,
                step=100000
            )
        
        target_date = st.date_input(translator.t("target_date"))
        
        if st.form_submit_button(translator.t("add_goal")):
            st.session_state.db.add_saving_goal(
                name,
                target_amount,
                target_date.strftime('%Y-%m-%d')
            )
            st.success(translator.t("goal_added"))
            st.rerun()
    
    st.subheader(translator.t("active_goals"))
    goals = st.session_state.db.get_saving_goals()
    current_balance = st.session_state.db.get_balance()
    
    if not goals.empty:
        today = datetime.now().date()
        for _, row in goals.iterrows():
            target_date = datetime.strptime(row['target_date'], "%Y-%m-%d").date()  # Thêm dòng này
            days_left = (target_date - today).days
            progress = min((current_balance / row['amount']) * 100, 100)
            
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric(translator.t("target"), format_currency(row['amount']))
                    st.caption(f"{translator.t('days_left')}: {max(days_left, 0)}")
                with col2:
                    st.progress(int(progress))
                    st.caption(f"{format_currency(current_balance)} / {format_currency(row['amount'])} ({progress:.1f}%)")
                
                if current_balance >= row['amount']:
                    st.balloons()
                    st.success(translator.t("goal_achieved"))
    else:
        st.info(translator.t("no_active_goals"))

elif selected_option == "settings":
    st.header(f'⚙️ {translator.t("settings")}')
    
    st.subheader(translator.t("initial_balance"))
    initial_balance = st.number_input(translator.t("enter_initial_balance"), min_value=0)
    if st.button(translator.t("update_balance")):
        st.session_state.db.add_initial_balance(initial_balance)
        st.success(translator.t("balance_updated"))
        st.rerun()
    
    st.subheader(translator.t("data_management"))
    if st.button(translator.t("refresh_data")):
        st.session_state.db.load_categories()
        st.rerun()
    
    st.subheader(f'⚠️ {translator.t("delete_data")}')
    if st.button(translator.t("delete_all_data")):
        st.session_state.db.reset_data()
        st.success(translator.t("data_deleted"))
        st.rerun()

    # Phần sao lưu và khôi phục dữ liệu
    st.divider()
    st.subheader(f'💾 {translator.t("backup_restore")}')
    
    col1, col2 = st.columns(2)
    with col1:
        # Xuất dữ liệu
        if st.button(translator.t("export_data")):
            try:
                data = {
                    "transactions": st.session_state.db.load_transactions().to_dict(orient="records"),
                    "budgets": st.session_state.db.get_budgets(),
                    "reminders": st.session_state.db.get_reminders().to_dict(orient="records"),
                    "goals": st.session_state.db.get_saving_goals().to_dict(orient="records")
                }
                st.download_button(
                    label=translator.t("download_backup"),
                    data=json.dumps(data, ensure_ascii=False, indent=2),
                    file_name=f"finance_backup_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"{translator.t('export_error')}: {str(e)}")
    
    with col2:
        # Nhập dữ liệu
        uploaded_file = st.file_uploader(translator.t("upload_backup"), type=["json"])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                
                # Xác nhận ghi đè dữ liệu
                if st.checkbox(translator.t("confirm_overwrite")):
                    if st.button(translator.t("import_data")):
                        # Xóa dữ liệu cũ
                        st.session_state.db.reset_data()
                        
                        # Khôi phục transactions
                        for transaction in data.get("transactions", []):
                            st.session_state.db.add_transaction(
                                transaction["ngay"],
                                transaction["loai"],
                                transaction["danh_muc"],
                                transaction["so_tien"],
                                transaction["mo_ta"]
                            )
                        
                        # Khôi phục budgets
                        for category, amount in data.get("budgets", {}).items():
                            st.session_state.db.set_budget(category, amount)
                        
                        # Khôi phục reminders
                        for reminder in data.get("reminders", []):
                            st.session_state.db.add_reminder(
                                reminder["name"],
                                reminder["due_date"],
                                reminder["amount"],
                                reminder["category"]
                            )
                        
                        # Khôi phục saving goals
                        for goal in data.get("goals", []):
                            st.session_state.db.add_saving_goal(
                                goal["name"],
                                goal["amount"],
                                goal["target_date"]
                            )
                        
                        st.success(translator.t("restore_success"))
                        st.rerun()
            except Exception as e:
                st.error(f"{translator.t('import_error')}: {str(e)}")

# Kết thúc phần settings