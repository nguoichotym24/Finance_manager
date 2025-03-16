import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_expense_by_category_chart(data):
    fig = px.pie(
        values=data.values,
        names=data.index,
        title='Phân bố chi tiêu theo danh mục'
    )
    return fig

def create_expense_trend_chart(df):
    df['ngay'] = pd.to_datetime(df['ngay'])
    daily_expenses = df[df['loai'] == 'Chi'].groupby('ngay')['so_tien'].sum().reset_index()
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily_expenses['ngay'],
            y=daily_expenses['so_tien'],
            mode='lines+markers',
            name='Chi tiêu hàng ngày'
        )
    )
    fig.update_layout(
        title='Xu hướng chi tiêu theo thời gian',
        xaxis_title='Ngày',
        yaxis_title='Số tiền (VND)'
    )
    return fig

def format_currency(amount):
    return f"{amount:,.0f} VND"
