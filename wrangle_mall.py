from imports import *

'''
1. Acquire data from mall_customers.customers in mysql database.
2. Missing values
3. One-hot-encoding (pd.get_dummies)
4. Split the data into train, validate, and split
5. Scaling
Add, commit, and push all of your work.
'''



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

def one_hot_encode(df):
    df['is_female'] = df.gender == 'Female'
    df = df.drop(columns='gender')
    return df

def split(df):
    '''
    This function splits a dataframe into train, validate, and test in order to 
    explore the data and to create and validate models. 
    It takes in a dataframe and contains an integer for setting a seed for replication. 
    Test is 20% of the original dataset. The remaining 80% of the dataset is 
    divided between valiidate and train, with validate being .30*.80= 24% of 
    the original dataset, and train being .70*.80= 56% of the original dataset. 
    The function returns, train, validate and test dataframes. 
    '''
    
    train_and_validate, test = train_test_split(df, random_state=123, test_size=.15)
    train, validate = train_test_split(train_and_validate, random_state=123, test_size=.2)

    print('Train: %d rows, %d cols' % train.shape)
    print('Validate: %d rows, %d cols' % validate.shape)
    print('Test: %d rows, %d cols' % test.shape)
    
    return train, validate, test



def scale(train, validate, test):
    columns_to_scale = ['age', 'spending_score', 'annual_income']
    train_scaled = train.copy()
    validate_scaled = validate.copy()
    test_scaled = test.copy()

    scaler = MinMaxScaler()
    scaler.fit(train[columns_to_scale])

    train_scaled[columns_to_scale] = scaler.transform(train[columns_to_scale])
    validate_scaled[columns_to_scale] = scaler.transform(validate[columns_to_scale])
    test_scaled[columns_to_scale] = scaler.transform(test[columns_to_scale])

    return train_scaled, validate_scaled, test_scaled

def get_exploration_data():
    df = acquire()
    train, validate, test = split(df)
    return train

def get_modeling_data(scale_data=False):
    df = acquire()
    df = one_hot_encode(df)
    train, validate, test = split(df)
    if scale_data:
        return scale(train, validate, test)
    else:
        return train, validate, test