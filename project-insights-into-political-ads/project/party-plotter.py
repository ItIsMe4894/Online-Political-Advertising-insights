import pandas as pd
import plotly.express as px
import janitor as jn
from os import listdir
from os.path import isfile, join

# Returns dataframe without columns that we dont use
def loadCsv(csv):
    df = pd.read_csv(csv)
    df = df.drop(columns=['page_id', 'page_name', 'ad_creation_time', 'ad_delivery_stop_time', 'byline', 'impressions', 'spend', 'currency', 'demographic_distribution', 'delivery_by_region', 'publisher_platforms', 'estimated_audience_size', 'languages'])
    return df

def loadCsvsFromDir(dir):
    dfs = []
    onlyfiles = [f for f in listdir(dir) if isfile(join(dir, f))]
    for file in onlyfiles:
        dfs.append(loadCsv(dir + '/' + file))

    df = pd.concat(dfs)
    return df.sort_values('ad_delivery_start_time')

# Change keyword
keyword = 'president'
democratDir = './ads/democrats'
republicanDir = './ads/republicans'

# Load all files
democratDf = loadCsvsFromDir(democratDir)
democratTotal = len(democratDf)
republicanDf = loadCsvsFromDir(republicanDir)
republicanTotal = len(republicanDf)


earliestDate = None # Used to fill up dataset
latestDate = None # Used to fill up dataset

# Loop over keywords to get all counts of keywords
partyCountResults = []
democratFilledIn = 0
republicanFilledIn = 0
for party, df in {'Democrats': democratDf, 'Republicans': republicanDf}.items():
    # Query all columns that contain 'content'
    query = "ad_creative_bodies.str.contains('" + keyword + "', na=False) or "
    query += "ad_creative_link_titles.str.contains('" + keyword + "', na=False) or "
    query += "ad_creative_link_captions.str.contains('" + keyword + "', na=False) or "
    query += "ad_creative_link_descriptions.str.contains('" + keyword + "', na=False)"
    df = df.query(query, engine='python')
    if df.empty:
        continue

    if party == 'Democrats':
        democratFilledIn += len(df)
    else:
        republicanFilledIn += len(df)
    # Group by start time and count the ads. All ads at this point contain the above keyword, so we can count them all
    # This results in having a count per date
    dateGroups = df.groupby('ad_delivery_start_time', as_index=False)
    countResult = dateGroups.count()

    # Clean up columns
    countResult = countResult.rename(columns={'ad_archive_id': party})
    countResult = countResult.drop(columns=['ad_creative_bodies', 'ad_creative_link_titles', 'ad_creative_link_captions', 'ad_creative_link_descriptions'])
    countResult['ad_delivery_start_time'] = pd.to_datetime(countResult['ad_delivery_start_time'])

    earliest = countResult['ad_delivery_start_time'].min()
    latest = countResult['ad_delivery_start_time'].max()
    if earliestDate is None or earliest < earliestDate:
        earliestDate = earliest
    if latestDate is None or latest > latestDate:
        latestDate = latest
    
    partyCountResults.append(countResult)

if len(partyCountResults) == 0:
    print('No results found matching the keyword')
    exit()

# Generate complete list of dates and add them to result with '0' values
dates = dict(ad_delivery_start_time = pd.date_range(earliestDate, latestDate, freq='1D'))

# Merge data sets
mergedCounts = None
for partycountResult in partyCountResults:
    partycountResult = partycountResult.complete(dates, fill_value=0)
    if mergedCounts is None:
        mergedCounts = partycountResult
    else:
        mergedCounts = pd.merge(mergedCounts, partycountResult, on = 'ad_delivery_start_time')

# Below code generates an interactive line graph
print(mergedCounts.head(10))
fig = px.line(mergedCounts, x = 'ad_delivery_start_time', y = ['Democrats', 'Republicans'], title='Keyword ' + keyword + ' found in ads, Democrats: ' + str(round(democratFilledIn/democratTotal*100)) + '%, Republicans: ' + str(round(republicanFilledIn/republicanTotal*100)) + '%.')
fig.update_layout(yaxis_title="Amount of ads with keyword '" + keyword + "'", xaxis_title="Date", legend_title="Party", font_size=30)
fig.show()



