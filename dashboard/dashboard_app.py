import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

def load_data():
    base_path = os.getcwd()

    order_items_dataset = os.path.join(base_path, 'dashboard', 'order_items_dataset.csv')
    orders_dataset = os.path.join(base_path, 'dashboard', 'orders_dataset.csv')
    review_product_df_path = os.path.join(base_path, 'dashboard', 'review_product_df.csv')

    try:
        order_items = pd.read_csv(order_items_dataset)
        orders_data = pd.read_csv(orders_dataset)
        review_product_df = pd.read_csv(review_product_df_path)
    except FileNotFoundError as e:
        st.error(f"File not found: {e}")
        return None, None  # Return None if loading fails

    final_orders_df = pd.merge(orders_data, order_items, on='order_id', how='inner')

    return final_orders_df, review_product_df

# Function to get monthly orders data
def get_monthly_orders(final_orders_df):
    final_orders_df['order_purchase_timestamp'] = pd.to_datetime(final_orders_df['order_purchase_timestamp'])
    max_date = final_orders_df['order_purchase_timestamp'].max()
    last_six_months = final_orders_df[final_orders_df['order_purchase_timestamp'] >= (max_date - pd.DateOffset(months=6))]
    
    monthly_orders_df = last_six_months.resample(rule='ME', on='order_purchase_timestamp').agg(
        order_count=('order_id', 'nunique'),
        revenue=('price', 'sum')
    ).reset_index()
    
    monthly_orders_df['order_purchase_timestamp'] = monthly_orders_df['order_purchase_timestamp'].dt.strftime('%B-%Y')
    return monthly_orders_df

# Function to get category analysis
def get_category_analysis(review_product_df):
    category_analysis = review_product_df.groupby('product_category_name_english').agg(
        average_review_score=('review_score', 'mean'),
        total_reviews=('review_score', 'count')
    ).reset_index()
    
    top_categories = category_analysis.sort_values(by='average_review_score', ascending=False).head(10)
    return top_categories

# Function to get RFM DataFrame
def get_rfm_data(final_orders_df):
    one_month_ago = final_orders_df['order_purchase_timestamp'].max() - pd.DateOffset(months=1)
    last_month_orders = final_orders_df[final_orders_df['order_purchase_timestamp'] >= one_month_ago]
    
    rfm_last_month_df = last_month_orders.groupby('customer_id').agg({
        'order_purchase_timestamp': lambda x: (last_month_orders['order_purchase_timestamp'].max() - x.max()).days,
        'order_id': 'count',
        'price': 'sum'
    }).reset_index()
    
    rfm_last_month_df.columns = ['customer_id', 'recency', 'frequency', 'monetary']
    return rfm_last_month_df

# Function to plot monthly revenue
def plot_monthly_revenue(monthly_orders_df):
    plt.figure(figsize=(10, 6))
    plt.plot(monthly_orders_df['order_purchase_timestamp'], monthly_orders_df['revenue'], marker='o')
    plt.title('Total Pendapatan per Bulan')
    plt.xlabel('Bulan')
    plt.ylabel('Pendapatan')
    plt.xticks(rotation=45)
    plt.grid()
    st.pyplot(plt)

# Function to plot purchase patterns
def plot_purchase_patterns(rfm_last_month_df):
    plt.figure(figsize=(12, 6))

    # Subplot for Recency
    plt.subplot(1, 3, 1)
    sns.histplot(rfm_last_month_df['recency'], bins=30, kde=True, color='skyblue')
    plt.title('Distribusi Recency')
    plt.xlabel('Hari Sejak Pembelian Terakhir')
    plt.ylabel('Jumlah Pelanggan')

    # Subplot for Frequency
    plt.subplot(1, 3, 2)
    sns.histplot(rfm_last_month_df['frequency'], bins=30, kde=True, color='lightgreen')
    plt.title('Distribusi Frequency')
    plt.xlabel('Jumlah Pembelian')
    plt.ylabel('Jumlah Pelanggan')

    # Subplot for Monetary
    plt.subplot(1, 3, 3)
    sns.histplot(rfm_last_month_df['monetary'], bins=30, kde=True, color='salmon')
    plt.title('Distribusi Monetary')
    plt.xlabel('Total Pengeluaran')
    plt.ylabel('Jumlah Pelanggan')

    plt.tight_layout()
    st.pyplot(plt)

# Function to plot top categories
def plot_top_categories(top_categories):
    plt.figure(figsize=(12, 6))
    sns.barplot(
        x='average_review_score', 
        y='product_category_name_english', 
        data=top_categories,  
        color='skyblue'
    )
    plt.xlabel('Rata-rata Skor Ulasan')
    plt.ylabel('Kategori Produk')
    plt.title('10 Kategori Produk Teratas')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    st.pyplot(plt)

# Function to plot best customers
def plot_best_customers(rfm_last_month_df):
    best_customers = rfm_last_month_df[
        (rfm_last_month_df['recency'] <= rfm_last_month_df['recency'].quantile(0.25)) &
        (rfm_last_month_df['frequency'] >= rfm_last_month_df['frequency'].quantile(0.75)) &
        (rfm_last_month_df['monetary'] >= rfm_last_month_df['monetary'].quantile(0.75))
    ]
    best_customers_top5 = best_customers.sort_values(by=['monetary', 'frequency', 'recency'], ascending=[False, False, True]).head(5)

    # Create a figure with 3 subplots in a single column
    plt.figure(figsize=(10, 15))

    # Define a base color and a darker shade for higher values
    base_color = 'skyblue'
    darker_color = '#005fa3'  # Darker shade of blue

    # Function to determine bar colors
    def get_color(value, max_value):
        return darker_color if value >= max_value * 0.75 else base_color

    # Subplot for Recency
    plt.subplot(3, 1, 1)
    max_recency = best_customers_top5['recency'].max()
    plt.bar(best_customers_top5['customer_id'], best_customers_top5['recency'],
            color=[get_color(val, max_recency) for val in best_customers_top5['recency']])
    plt.title('Top 5 Pelanggan - Recency')
    plt.xlabel('Customer ID')
    plt.ylabel('Recency (Hari)')
    plt.xticks(rotation=45)

    # Subplot for Frequency
    plt.subplot(3, 1, 2)
    max_frequency = best_customers_top5['frequency'].max()
    plt.bar(best_customers_top5['customer_id'], best_customers_top5['frequency'],
            color=[get_color(val, max_frequency) for val in best_customers_top5['frequency']])
    plt.title('Top 5 Pelanggan - Frequency')
    plt.xlabel('Customer ID')
    plt.ylabel('Frequency (Jumlah Pembelian)')
    plt.xticks(rotation=45)

    # Subplot for Monetary
    plt.subplot(3, 1, 3)
    max_monetary = best_customers_top5['monetary'].max()
    plt.bar(best_customers_top5['customer_id'], best_customers_top5['monetary'],
            color=[get_color(val, max_monetary) for val in best_customers_top5['monetary']])
    plt.title('Top 5 Pelanggan - Monetary')
    plt.xlabel('Customer ID')
    plt.ylabel('Monetary (Total Pengeluaran)')
    plt.xticks(rotation=45)

    plt.tight_layout()
    st.pyplot(plt)

# Main Streamlit App
def main():
    st.title("Analisis Data E-commerce")
    
    # Load data
    final_orders_df, review_product_df = load_data()
    
    # Check if data was loaded successfully
    if final_orders_df is not None and review_product_df is not None:
        # Data Aggregation
        monthly_orders_df = get_monthly_orders(final_orders_df)
        top_categories = get_category_analysis(review_product_df)
        rfm_last_month_df = get_rfm_data(final_orders_df)

        # Visualizations
        st.subheader("Total Pendapatan per Bulan dalam 6 Bulan Terakhir")
        plot_monthly_revenue(monthly_orders_df)

        st.subheader("Distribusi Pola Pembelian Pelanggan")
        plot_purchase_patterns(rfm_last_month_df)

        st.subheader("10 Kategori Produk Teratas Berdasarkan Rata-rata Skor Ulasan")
        plot_top_categories(top_categories)

        st.subheader("Top 5 Pelanggan dengan Kinerja Terbaik")
        plot_best_customers(rfm_last_month_df)

if __name__ == "__main__":
    main()
