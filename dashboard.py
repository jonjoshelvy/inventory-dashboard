import streamlit as st
import pandas as pd
import datetime
import os
from datetime import date
import plotly.express as px


# Data persistence functions
def load_data():
    """Load inventory and sales data from CSV files or create empty DataFrames"""
    try:
        inventory = pd.read_csv("inventory.csv")
    except FileNotFoundError:
        inventory = pd.DataFrame(columns=[
            'Product Name', 'Product Type', 'Gender', 'Size', 'Color',
            'SKU/Code', 'Quantity', 'Restock Threshold', 'Cost Price', 'Selling Price'
        ])

    try:
        sales = pd.read_csv("sales.csv", parse_dates=['Date'])
    except FileNotFoundError:
        sales = pd.DataFrame(columns=[
            'Date', 'Product Name', 'Quantity Sold', 'Size', 'Gender',
            'Customer Name', 'Payment Status', 'Cost Price', 'Selling Price', 'Profit'
        ])

    return inventory, sales


def save_data(inventory, sales):
    """Save current data to CSV files"""
    inventory.to_csv("inventory.csv", index=False)
    sales.to_csv("sales.csv", index=False)


# Initialize data
if 'inventory' not in st.session_state or 'sales' not in st.session_state:
    st.session_state.inventory, st.session_state.sales = load_data()

# Dashboard layout
st.set_page_config(layout="wide")
st.title("Product Inventory and Sales Dashboard")

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Inventory Management", "Sales Tracking", "Analytics Dashboard"])

# Inventory Management Page
if page == "Inventory Management":
    st.header("Product Inventory Management")

    # Add new product form
    with st.expander("Add New Product"):
        with st.form("product_form"):
            col1, col2 = st.columns(2)

            with col1:
                product_name = st.text_input("Product Name*")
                product_type = st.selectbox("Product Type*",
                                            ["T-shirt", "Hoodie", "Tracksuit", "Pants", "Hat", "Other"])
                gender = st.selectbox("Gender*", ["Male", "Female", "Unisex"])
                size = st.selectbox("Size*", ["XS", "S", "M", "L", "XL", "XXL"])
                color = st.text_input("Color*")

            with col2:
                sku = st.text_input("SKU/Code")
                quantity = st.number_input("Quantity in Stock*", min_value=0, step=1)
                restock_threshold = st.number_input("Restock Threshold*", min_value=0, step=1)
                cost_price = st.number_input("Cost Price*", min_value=0.0, format="%.2f")
                selling_price = st.number_input("Selling Price*", min_value=0.0, format="%.2f")

            submitted = st.form_submit_button("Add Product")

            if submitted:
                if product_name and product_type and gender and size and color and quantity and restock_threshold and cost_price and selling_price:
                    new_product = pd.DataFrame([{
                        'Product Name': product_name,
                        'Product Type': product_type,
                        'Gender': gender,
                        'Size': size,
                        'Color': color,
                        'SKU/Code': sku,
                        'Quantity': quantity,
                        'Restock Threshold': restock_threshold,
                        'Cost Price': cost_price,
                        'Selling Price': selling_price
                    }])

                    st.session_state.inventory = pd.concat([st.session_state.inventory, new_product], ignore_index=True)
                    save_data(st.session_state.inventory, st.session_state.sales)
                    st.success("Product added successfully!")
                else:
                    st.error("Please fill in all required fields (marked with *)")

    # Inventory display and management
    st.subheader("Current Inventory")

    if not st.session_state.inventory.empty:
        edited_inventory = st.data_editor(
            st.session_state.inventory,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Quantity": st.column_config.NumberColumn(
                    "Quantity",
                    help="Current stock quantity",
                    min_value=0,
                    step=1
                ),
                "Restock Threshold": st.column_config.NumberColumn(
                    "Restock Threshold",
                    help="Quantity at which to reorder",
                    min_value=0,
                    step=1
                ),
                "Cost Price": st.column_config.NumberColumn(
                    "Cost Price",
                    help="Cost price per unit",
                    min_value=0.0,
                    format="%.2f"
                ),
                "Selling Price": st.column_config.NumberColumn(
                    "Selling Price",
                    help="Selling price per unit",
                    min_value=0.0,
                    format="%.2f"
                )
            }
        )

        if st.button("Update Inventory"):
            st.session_state.inventory = edited_inventory
            save_data(st.session_state.inventory, st.session_state.sales)
            st.success("Inventory updated successfully!")

        low_stock = st.session_state.inventory[
            st.session_state.inventory['Quantity'] <= st.session_state.inventory['Restock Threshold']
            ]

        if not low_stock.empty:
            st.subheader("⚠️ Low Stock Alert")
            st.dataframe(low_stock, use_container_width=True)
    else:
        st.info("No products in inventory. Add some products to get started.")

# Sales Tracking Page
elif page == "Sales Tracking":
    st.header("Sales Tracking")

    with st.expander("Record New Sale"):
        with st.form("sale_form"):
            col1, col2 = st.columns(2)

            with col1:
                date_sold = st.date_input("Date of Sale*", date.today())
                product_name = st.selectbox(
                    "Product Sold*",
                    st.session_state.inventory['Product Name'].unique() if not st.session_state.inventory.empty else []
                )
                quantity_sold = st.number_input("Quantity Sold*", min_value=1, step=1)

            with col2:
                if product_name and not st.session_state.inventory.empty:
                    product_details = st.session_state.inventory[
                        st.session_state.inventory['Product Name'] == product_name
                        ].iloc[0]

                    size = st.selectbox("Size*", [product_details['Size']], disabled=True)
                    gender = st.selectbox("Gender*", [product_details['Gender']], disabled=True)
                else:
                    size = st.selectbox("Size*", ["XS", "S", "M", "L", "XL", "XXL"])
                    gender = st.selectbox("Gender*", ["Male", "Female", "Unisex"])

                customer_name = st.text_input("Customer Name")
                payment_status = st.selectbox("Payment Status*", ["Paid", "Pending", "Cancelled"])

            submitted = st.form_submit_button("Record Sale")

            if submitted:
                if product_name and quantity_sold and size and gender and payment_status:
                    product_details = st.session_state.inventory[
                        (st.session_state.inventory['Product Name'] == product_name) &
                        (st.session_state.inventory['Size'] == size) &
                        (st.session_state.inventory['Gender'] == gender)
                        ]

                    if not product_details.empty:
                        product_details = product_details.iloc[0]

                        if product_details['Quantity'] >= quantity_sold:
                            profit = (product_details['Selling Price'] - product_details['Cost Price']) * quantity_sold

                            new_sale = pd.DataFrame([{
                                'Date': date_sold,
                                'Product Name': product_name,
                                'Quantity Sold': quantity_sold,
                                'Size': size,
                                'Gender': gender,
                                'Customer Name': customer_name,
                                'Payment Status': payment_status,
                                'Cost Price': product_details['Cost Price'],
                                'Selling Price': product_details['Selling Price'],
                                'Profit': profit
                            }])

                            st.session_state.sales = pd.concat([st.session_state.sales, new_sale], ignore_index=True)

                            st.session_state.inventory.loc[
                                (st.session_state.inventory['Product Name'] == product_name) &
                                (st.session_state.inventory['Size'] == size) &
                                (st.session_state.inventory['Gender'] == gender),
                                'Quantity'
                            ] -= quantity_sold

                            save_data(st.session_state.inventory, st.session_state.sales)
                            st.success("Sale recorded successfully!")
                        else:
                            st.error("Not enough stock available for this product!")
                    else:
                        st.error("Product not found in inventory!")
                else:
                    st.error("Please fill in all required fields (marked with *)")

    st.subheader("Sales Records")

    if not st.session_state.sales.empty:
        st.dataframe(
            st.session_state.sales.sort_values('Date', ascending=False),
            use_container_width=True
        )

        if st.button("Export Sales Data to CSV"):
            csv = st.session_state.sales.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"sales_data_{date.today()}.csv",
                mime="text/csv"
            )
    else:
        st.info("No sales records yet. Record some sales to get started.")

# Analytics Dashboard Page
elif page == "Analytics Dashboard":
    st.header("Analytics Dashboard")

    if st.session_state.sales.empty or st.session_state.inventory.empty:
        st.warning("Not enough data to display analytics. Add some products and sales first.")
    else:
        col1, col2, col3 = st.columns(3)

        total_sales = st.session_state.sales['Quantity Sold'].sum()
        total_revenue = (st.session_state.sales['Quantity Sold'] * st.session_state.sales['Selling Price']).sum()
        total_profit = st.session_state.sales['Profit'].sum()

        col1.metric("Total Products Sold", total_sales)
        col2.metric("Total Revenue", f"${total_revenue:,.2f}")
        col3.metric("Total Profit", f"${total_profit:,.2f}")

        st.subheader("Sales Over Time")
        sales_by_date = st.session_state.sales.groupby('Date').agg({
            'Quantity Sold': 'sum',
            'Profit': 'sum'
        }).reset_index()

        fig = px.line(
            sales_by_date,
            x='Date',
            y='Quantity Sold',
            title="Daily Sales Quantity",
            labels={'Quantity Sold': 'Number of Items Sold'}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Profit by Product")
        profit_by_product = st.session_state.sales.groupby('Product Name').agg({
            'Quantity Sold': 'sum',
            'Profit': 'sum'
        }).reset_index().sort_values('Profit', ascending=False)

        fig2 = px.bar(
            profit_by_product,
            x='Product Name',
            y='Profit',
            title="Total Profit by Product",
            labels={'Profit': 'Total Profit ($)'}
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Inventory Status")
        inventory_status = st.session_state.inventory.copy()
        inventory_status['Stock Value'] = inventory_status['Quantity'] * inventory_status['Cost Price']

        fig3 = px.treemap(
            inventory_status,
            path=['Product Type', 'Product Name'],
            values='Stock Value',
            title="Inventory Value by Product Type"
        )
        st.plotly_chart(fig3, use_container_width=True)

        if not st.session_state.sales.empty:
            st.subheader("Payment Status Breakdown")
            payment_status = st.session_state.sales['Payment Status'].value_counts().reset_index()
            payment_status.columns = ['Status', 'Count']

            fig4 = px.pie(
                payment_status,
                names='Status',
                values='Count',
                title="Payment Status Distribution"
            )
            st.plotly_chart(fig4, use_container_width=True)

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)