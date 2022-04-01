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

