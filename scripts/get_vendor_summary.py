import sqlite3
import pandas as pd
import logging
from ingestion_db import ingest_db

logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)


def create_vendor_summary(conn):
    ''' this function will merge the different tables to get the overall vendor summary 
    and adding new columns in the resulting table'''
    vendor_sales_summary = pd.read_sql_query("""with FreightSummary as (
    select
        VendorNumber,
        SUM(Freight) as TotalFreightCost
    from vendor_invoice
    group by VendorNumber
    ),
                                            
    PurchaseSummary as (
        select
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.Description,
            pp.Price as ActualPrice,
            pp.Volume,
            sum(p.Quantity) as TotalPurchaseQuantity,
            sum(p.Dollars) as TotalPurchaseDollars
        from purchases p
        join purchase_prices pp
        on p.Brand = pp.Brand
        where p.PurchasePrice > 0
        group by p.VendorNumber, p.VendorName, p.Brand, p.Description, pp.Price, pp.Volume
    ),
                                            
    SalesSummary as (
        select 
            VendorNo,
            Brand,
            sum(SalesQuantity) as TotalSalesQuantity,
            sum(SalesDollars) as TotalSalesDollars,
            sum(SalesPrice) as TotalSalesPrice,
            sum(ExciseTax) as TotalExciseTax
        from sales
        group by VendorNo, Brand
    )

    select
        ps.VendorNumber,
        ps.VendorName,
        ps.Brand,
        ps.Description,
        ps.ActualPrice,
        ps.Volume,
        ps.TotalPurchaseQuantity,
        ps.TotalPurchaseDollars,
        ss.TotalSalesQuantity,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalExciseTax,
        fs.TotalFreightCost
    from PurchaseSummary ps
    left join SalesSummary ss
    on ps.VendorNumber = ss.VendorNo
    and ps.Brand = ss.Brand
    left join FreightSummary fs
    on ps.VendorNumber = fs.VendorNumber
    order by ps.TotalPurchaseDollars desc
    """, conn)
    
    return vendor_sales_summary

def clean_data(df):
    ''' this function will clean the data and handle missing values'''
    #changing data types to float
    df['Volume'] = df['Volume'].astype(float)

    #filling missing values with 0
    df.fillna(0, inplace=True)

    #removing spaces from categorial columns
    df['VendorName'] = df['VendorName'].str.strip()
    df['Description'] = df['Description'].str.strip()

    #creating new columns for better analysis
    df['GrossMargin'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars']
    df['ProfitMargin'] = df['GrossMargin'] / df['TotalSalesDollars']
    df['StockTurnover'] = df['TotalSalesQuantity'] / df['TotalPurchaseQuantity']
    df['SalestoPurchaseRatio'] = df['TotalSalesDollars'] / df['TotalPurchaseDollars']

    return df

if __name__ == "__main__":
    #creating a connection to the database
    conn = sqlite3.connect('inventory.db')

    logging.info("Creating vendor sales summary")
    summary_df = create_vendor_summary(conn)
    logging.info(summary_df.head())

    logging.info("Cleaning data....")
    clean_df = clean_data(summary_df)
    logging.info(clean_df.head())

    logging.info('Ingesting data....')
    ingest_db(clean_df, 'vendor_sales_summary', conn)
    logging.info('Data ingested successfully')

