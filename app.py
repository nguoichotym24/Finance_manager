import streamlit as st
import pandas as pd
from datetime import datetime
from database import Database
from utils import create_expense_by_category_chart, create_expense_trend_chart, format_currency

# Khởi tạo session state
if 'db' not in st.session_state:
    st.session_state.db = Database()

# Tiêu đề ứng dụng
st.title('Quản lý Tài chính Cá nhân')

# Sidebar cho nhập liệu
with st.sidebar:
    st.header('Nhập giao dịch mới')

    # Thêm phần nhập số dư ban đầu
    st.subheader('Số dư ban đầu')
    initial_balance = st.number_input('Nhập số tiền hiện có', min_value=0)
    if st.button('Cập nhật số dư'):
        try:
            st.session_state.db.add_initial_balance(initial_balance)
            st.success('Đã cập nhật số dư ban đầu!')
            st.rerun()
        except Exception as e:
            st.error(f'Lỗi: {str(e)}')

    st.divider()  # Thêm đường phân cách

    # Phần nhập giao dịch
    st.subheader('Thêm giao dịch')
    date = st.date_input('Ngày', datetime.now())
    trans_type = st.selectbox('Loại giao dịch', ['Thu', 'Chi'])
    category = st.selectbox('Danh mục', st.session_state.db.categories)
    amount = st.number_input('Số tiền', min_value=0, key='transaction_amount')
    description = st.text_input('Mô tả')

    if st.button('Thêm giao dịch'):
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

    # Thêm nút xóa dữ liệu với xác nhận
    st.header('Xóa dữ liệu')
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = False

    if st.button('Xóa tất cả dữ liệu'):
        st.warning('Bạn có chắc chắn muốn xóa tất cả dữ liệu? Hành động này không thể hoàn tác!')
        st.session_state.confirm_delete = True
        st.rerun()

    if st.session_state.confirm_delete:
        if st.button('Xác nhận xóa'):
            st.session_state.db.reset_data()
            st.success('Đã xóa tất cả dữ liệu!')
            st.session_state.confirm_delete = False
            st.rerun()

# Main content
transactions = st.session_state.db.load_transactions()
balance = st.session_state.db.get_balance()
st.header('Tổng quan')
st.metric('Số dư hiện tại', format_currency(balance))

if not transactions.empty:
    # Biểu đồ phân tích
    st.header('Phân tích chi tiêu')

    col1, col2 = st.columns(2)

    with col1:
        category_summary = st.session_state.db.get_category_summary()
        st.plotly_chart(create_expense_by_category_chart(category_summary))

    with col2:
        st.plotly_chart(create_expense_trend_chart(transactions))

    # Bảng giao dịch
    st.header('Lịch sử giao dịch')
    transactions['ngay'] = pd.to_datetime(transactions['ngay'])
    transactions = transactions.sort_values('ngay', ascending=False)

    st.dataframe(
        transactions.rename(columns={
            'ngay': 'Ngày',
            'loai': 'Loại',
            'danh_muc': 'Danh mục',
            'so_tien': 'Số tiền',
            'mo_ta': 'Mô tả'
        }),
        hide_index=True
    )

    # Xuất báo cáo
    st.header('Báo cáo')
    if st.button('Tải xuống báo cáo CSV'):
        transactions.to_csv('bao_cao_tai_chinh.csv', index=False)
        st.success('Đã tạo file báo cáo "bao_cao_tai_chinh.csv"')
else:
    st.info('Chưa có giao dịch nào. Hãy thêm giao dịch mới ở menu bên trái.')