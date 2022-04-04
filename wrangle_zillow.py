from imports import *

sql = """
SELECT prop.*, 
       pred.logerror, 
       pred.transactiondate, 
       air.airconditioningdesc, 
       arch.architecturalstyledesc, 
       build.buildingclassdesc, 
       heat.heatingorsystemdesc, 
       landuse.propertylandusedesc, 
       story.storydesc, 
       construct.typeconstructiondesc 
FROM   properties_2017 prop  
       INNER JOIN (SELECT parcelid,
       					  logerror,
                          Max(transactiondate) transactiondate 
                   FROM   predictions_2017 
                   GROUP  BY parcelid, logerror) pred
               USING (parcelid) 
       LEFT JOIN airconditioningtype air USING (airconditioningtypeid) 
       LEFT JOIN architecturalstyletype arch USING (architecturalstyletypeid) 
       LEFT JOIN buildingclasstype build USING (buildingclasstypeid) 
       LEFT JOIN heatingorsystemtype heat USING (heatingorsystemtypeid) 
       LEFT JOIN propertylandusetype landuse USING (propertylandusetypeid) 
       LEFT JOIN storytype story USING (storytypeid) 
       LEFT JOIN typeconstructiontype construct USING (typeconstructiontypeid) 
WHERE  prop.latitude IS NOT NULL 
       AND prop.longitude IS NOT NULL AND transactiondate <= '2017-12-31' 
"""

# acquire zillow data using the query
def get_db_url(database):
    from env import host, user, password
    url = f'mysql+pymysql://{user}:{password}@{host}/{database}'
    return url


# acquire zillow data using the query
def get_zillow():
    filename = 'zillow.csv'
    
    if os.path.exists(filename):
        print('Reading from csv file...')
        return pd.read_csv(filename)
    
    url = get_db_url('zillow')
    print('Getting a fresh copy from SQL database...')
    zillow_df = pd.read_sql(sql, url, index_col='id')
    zillow_df = zillow_df.drop_duplicates(subset = 'parcelid')
    print('Saving to csv...')
    zillow_df.to_csv(filename, index=False)
    return zillow_df



def summary_info(df): 
    # Summarize data (shape, info, summary stats, dtypes, shape)
    print('--- Shape: {}'.format(df.shape))
    print('--- Descriptions')
    print(df.describe(include='all'))
    print('--- Info')
    return df.info()


def univariate_distributions(df):
    # plot some distributions 

    plt.figure(figsize = (12,8))
    plt.subplot(221)
    plt.hist(df.bedroomcnt, bins = 10)
    plt.title('Bedrooms')



    plt.subplot(222)
    plt.hist(df.calculatedfinishedsquarefeet, bins = 100)
    plt.title('finished area')



    plt.subplot(223)
    plt.hist(df.logerror, bins = 100)
    plt.title('logerror')



    plt.subplot(224)
    plt.hist(df.taxvaluedollarcnt, bins = 100)
    plt.title('taxvaluedollarcnt')

    return plt.tight_layout()



def missing_values_per_column(df):
    # Nulls by column
    missing_in_columns = pd.concat([
        df.isna().sum().rename('count').sort_values(ascending = False),
        df.isna().mean().rename('percent')
    ], axis=1)
    return missing_in_columns


def missing_values_per_row(df):
# nulls by row
    missing_in_rows = pd.concat([
        df.isna().sum(axis=1).rename('n_cols_missing'),
        df.isna().mean(axis=1).rename('percent_missing'),
        ], axis=1).value_counts().to_frame(name='row_counts').sort_index().reset_index()
 
    return missing_in_rows

def remove_columns(df, cols_to_remove = ['buildingqualitytypeid', 'heatingsystemtypeid', 'propertyzoningdesc', 'heatingorsystemdesc']):  
    df = df.drop(columns=cols_to_remove)
    return df

def handle_missing_values(df, prop_required_column = .5, prop_required_row = .5):
    threshold = int(round(prop_required_column*len(df.index),0))
    df.dropna(axis=1, thresh=threshold, inplace=True)
    threshold = int(round(prop_required_row*len(df.columns),0))
    df.dropna(axis=0, thresh=threshold, inplace=True)
    return df


def data_prep(df, cols_to_remove=['censustractandblock','finishedsquarefeet12','buildingqualitytypeid', 'heatingorsystemtypeid', 'propertyzoningdesc', 'heatingorsystemdesc', 'unitcnt'], prop_required_column=.5, prop_required_row=.5):
    df = remove_columns(df, cols_to_remove)
    df = handle_missing_values(df, prop_required_column, prop_required_row)
   
    # Make categorical column for location based upon the name of the county that belongs to the cooresponding state_county_code (fips code)
    df['county_code_bin'] = pd.cut(df.fips, bins=[0, 6037.0, 6059.0, 6111.0], 
                             labels = ['Los Angeles County', 'Orange County',
                             'Ventura County'])
   
    # Make dummy columns for state_county_code using the binned column for processin gin modeling later. 
    dummy_df = pd.get_dummies(df[['county_code_bin']], dummy_na=False, drop_first=[True])
    
    # Add dummy columns to dataframe
    df = pd.concat([df, dummy_df], axis=1)

    # Make categorical column for square_feet.
    df['home_sizes'] = pd.cut(df.calculatedfinishedsquarefeet, bins=[0, 1800, 4000, 6000, 25000], 
                             labels = ['Small: 0 - 1799sqft',
                             'Medium: 1800 - 3999sqft', 'Large: 4000 - 5999sqft', 'Extra-Large: 6000 - 25000sqft'])
    
    # Make categorical column for total_rooms, combining number of bedrooms and bathrooms.
    df['total_rooms'] = df['bedroomcnt'] + df['bathroomcnt']
    
    # Make categorical column for bedrooms.
    df['bedroom_bins'] = pd.cut(df.bedroomcnt, bins=[0, 2, 4, 6, 15], 
                             labels = ['Small: 0-2 bedrooms',
                             'Medium: 3-4 bedrooms', 'Large: 5-6 bedrooms', 'Extra-Large: 7-15 bedrooms'])
    
    # Make categorical column for square_feet.
    df['bathroom_bins'] = pd.cut(df.bathroomcnt, bins=[0, 2, 4, 6, 15], 
                             labels = ['Small: 0-2 bathrooms',
                             'Medium: 3-4 bathrooms', 'Large: 5-6 bathrooms', 'Extra-Large: 8-15 bathrooms'])
    return df




def single_family_homes(df):
    # Restrict df to only properties that meet single unit criteria

    #261: Single Family Residential, #262: Rural Residence, #263: Mobile Homes, 
    #264: Townhomes, #265 Cluster Homes, #266: Condominium, #268: Row House, 
    #273 Bungalow, #275 Manufactured, #276 Patio Home, #279 Inferred Single Family Residence

    single_use = [261, 262, 263, 264, 265, 266, 268, 273, 275, 276, 279]
    df = df[df.propertylandusetypeid.isin(single_use)]

    # Restrict df to only those properties with at least 1 bath & bed and > 400 sqft area (to not include tiny homes)
    
    df = df[(df.bedroomcnt > 0) & (df.bathroomcnt > 0) & ((df.unitcnt<=1)|df.unitcnt.isnull()) & (df.calculatedfinishedsquarefeet>400)]

    return df

def one_hot_encode(df):
    df['is_female'] = df.gender == 'Female'
    df = df.drop(columns='gender')
    return df

def split(df):
    train_and_validate, test = train_test_split(df, random_state=123, test_size=.15)
    train, validate = train_test_split(train_and_validate, random_state=123, test_size=.2)

    print('Train: %d rows, %d cols' % train.shape)
    print('Validate: %d rows, %d cols' % validate.shape)
    print('Test: %d rows, %d cols' % test.shape)

    return train, validate, test

def scale(train, validate, test, columns_to_scale):
    columns_to_scale = []
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

