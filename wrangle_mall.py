from imports import *


def get_mall_data(use_cache=True):
    filename = 'mall_customers.csv'
    
    if os.path.exists(filename):
        print('Reading from csv file...')
        return pd.read_csv(filename)
    
    
    url = f'mysql+pymysql://{env.user}:{env.password}@{env.host}/mall_customers'
    query = '''
    SELECT *
        FROM customers
        
    '''

    print('Getting a fresh copy from SQL database...')
    df = pd.read_sql(query, url)
    print('Saving to csv...')
    df.to_csv(filename, index=False)
    return df



def summary_info(df): 
    # Summarize data (shape, info, summary stats, dtypes, shape)
    print('--- Shape: {}'.format(df.shape))
    print('--- Descriptions')
    print(df.describe(include='all'))
    print('--- Info')
    return df.info()



def data_split(df, target):
    '''
    This function splits a dataframe into train, validate, and test in order to 
    explore the data and to create and validate models. 
    It takes in a dataframe and contains an integer for setting a seed for replication. 
    Test is 20% of the original dataset. The remaining 80% of the dataset is 
    divided between valiidate and train, with validate being .30*.80= 24% of 
    the original dataset, and train being .70*.80= 56% of the original dataset. 
    The function returns, train, validate and test dataframes. 
    '''
    
    train, test = train_test_split(df, test_size = .2, random_state=123)  
    train, validate = train_test_split(train, test_size=.3, random_state=123)


    print(f'train -> {train.shape}')
    print(f'validate -> {validate.shape}')
    print(f'test -> {test.shape}')
    
    return train, validate, test