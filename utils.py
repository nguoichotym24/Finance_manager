import plotly.express as px
import pandas as pd

def format_currency(amount):
    return "{:,.0f} đ".format(amount) if amount >= 0 else "-{:,.0f} đ".format(abs(amount))

def create_expense_by_category_chart(category_summary):
    if not category_summary:
        return px.pie(names=['Không có dữ liệu'], values=[1])
    
    df = pd.DataFrame({
        'Danh mục': list(category_summary.keys()),
        'Số tiền': list(category_summary.values())
    })
    fig = px.pie(df, names='Danh mục', values='Số tiền', title='Phân bổ chi tiêu theo danh mục')
    fig.update_traces(textinfo='percent+label+value', texttemplate='%{label}<br>%{value:,.0f} đ<br>(%{percent})')
    return fig

def create_expense_trend_chart(transactions):
    if transactions.empty:
        return px.line(title='Không có dữ liệu')
    
    df = transactions.copy()
    df['ngay'] = pd.to_datetime(df['ngay'])
    df = df[df['loai'] == 'Chi']
    df = df.groupby(df['ngay'].dt.to_period('D').astype(str))['so_tien'].sum().reset_index()
    
    fig = px.line(df, x='ngay', y='so_tien', 
                 title='Xu hướng chi tiêu theo ngày',
                 labels={'ngay': 'Ngày', 'so_tien': 'Số tiền (đ)'})
    fig.update_xaxes(tickformat='%Y-%m-%d')
    fig.update_yaxes(tickprefix='', ticksuffix=' đ')
    return fig