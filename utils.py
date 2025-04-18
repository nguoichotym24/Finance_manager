import plotly.express as px
import pandas as pd
from i18n import translator

def format_currency(amount):
    return "{:,.0f} đ".format(amount) if amount >= 0 else "-{:,.0f} đ".format(abs(amount))

def create_expense_by_category_chart(category_summary):
    if not category_summary:
        return px.pie(names=[translator.t('no_data')], values=[1])
    
    df = pd.DataFrame({
        translator.t('category'): list(category_summary.keys()),
        translator.t('amount'): list(category_summary.values())
    })
    fig = px.pie(df, names=translator.t('category'), values=translator.t('amount'), 
                title=translator.t('expense_distribution_chart'))
    fig.update_traces(textinfo='percent+label+value', 
                     texttemplate='%{label}<br>%{value:,.0f} đ<br>(%{percent})')
    return fig

def create_expense_trend_chart(transactions):
    if transactions.empty:
        return px.line(title=translator.t('no_data'))
    
    df = transactions.copy()
    df['ngay'] = pd.to_datetime(df['ngay'])
    df = df[df['loai'] == 'Chi']
    df = df.groupby(df['ngay'].dt.to_period('D').astype(str))['so_tien'].sum().reset_index()
    
    fig = px.line(df, x='ngay', y='so_tien', 
                 title=translator.t('expense_trend_chart'),
                 labels={'ngay': translator.t('date'), 'so_tien': f"{translator.t('amount')} (đ)"})
    fig.update_xaxes(tickformat='%Y-%m-%d')
    fig.update_yaxes(tickprefix='', ticksuffix=' đ')
    return fig