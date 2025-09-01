import pandas as pd
import os
from sqlalchemy import create_engine
import logging
import time
logging.basicConfig(
    filename="logs/ingestation_db.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)
engine = create_engine('sqlite:///inventory.db')
def ingest_db(df, table_name, engine):
    ''' this function ingests the dataframe in the db'''
    df.to_sql(table_name, con=engine, if_exists='replace', index=False)

def load_raw_data():
    ''' this function loads all the raw data from the data folder and 
    returns a list of dataframes and ingest them in the db'''
    start = time.time()
    for file in os.listdir('data'):
        if file.endswith('.csv'):
            df = pd.read_csv('data/'+file)
            logging.info(f'Ingesting {file} in db')
            ingest_db(df, file[:-4], engine)
    end = time.time()
    total_time = (end - start)/60
    logging.info('------------Ingestion completed------------')
    logging.info(f'Total time taken to ingest data: {total_time} minutes')

if __name__ == '__main__':
    load_raw_data()