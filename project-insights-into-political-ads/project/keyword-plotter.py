import pandas as pd
import plotly.express as px
import janitor as jn
from os import listdir
from os.path import isfile, join


# Returns dataframe without columns that we dont use
def loadCsv(csv):
    df = pd.read_csv(csv)
    df = df.drop(
        columns=['page_id', 'page_name', 'ad_creation_time', 'ad_delivery_stop_time', 'byline', 'impressions', 'spend',
                 'currency', 'demographic_distribution', 'delivery_by_region', 'publisher_platforms',
                 'estimated_audience_size', 'languages'])
    return df


# Change this array to look for other keywords
keywords = ['Trump', 'Biden', 'vote', 'donate', 'election', 'president']
directories = ['./ads/democrats', './ads/republicans']

# Load all files
dfs = []
for directory in directories:
    onlyfiles = [f for f in listdir(directory) if isfile(join(directory, f))]
    for file in onlyfiles:
        dfs.append(loadCsv(directory + '/' + file))

df = pd.concat(dfs)
df = df.sort_values('ad_delivery_start_time')

totalRecords = len(df)

earliestDate = None  # Used to fill up dataset
latestDate = None  # Used to fill up dataset

# Loop over keywords to get all counts of keywords
keywordCountResults = []
keywordsFound = []
filledInRecords = 0
for keyword in keywords:
    # Query all columns that contain 'content'
    query = "ad_creative_bodies.str.contains('" + keyword + "', na=False) or "
    query += "ad_creative_link_titles.str.contains('" + keyword + "', na=False) or "
    query += "ad_creative_link_captions.str.contains('" + keyword + "', na=False) or "
    query += "ad_creative_link_descriptions.str.contains('" + keyword + "', na=False)"
    keywordDf = df.query(query, engine='python')
    if keywordDf.empty:
        continue

    filledInRecords += len(keywordDf)

    # Group by start time and count the ads. All ads at this point contain the above keyword, so we can count them all
    # This results in having a count per date
    dateGroups = keywordDf.groupby('ad_delivery_start_time', as_index=False)
    countResult = dateGroups.count()

    # Clean up columns
    countResult = countResult.rename(columns={'ad_archive_id': keyword})
    countResult = countResult.drop(
        columns=['ad_creative_bodies', 'ad_creative_link_titles', 'ad_creative_link_captions',
                 'ad_creative_link_descriptions'])
    countResult['ad_delivery_start_time'] = pd.to_datetime(countResult['ad_delivery_start_time'])

    keywordEarliest = countResult['ad_delivery_start_time'].min()
    keywordLatest = countResult['ad_delivery_start_time'].max()
    if earliestDate is None or keywordEarliest < earliestDate and str(keywordEarliest) != 'NaT':
        earliestDate = keywordEarliest
    if latestDate is None or keywordLatest > latestDate and str(keywordLatest) != 'NaT':
        latestDate = keywordLatest

    keywordsFound.append(keyword)
    keywordCountResults.append(countResult)

# Generate complete list of dates and add them to result with '0' values
dates = dict(ad_delivery_start_time=pd.date_range(earliestDate, latestDate, freq='1D'))

# Merge data sets
mergedCounts = None
for keywordCountResult in keywordCountResults:
    keywordCountResult = keywordCountResult.complete(dates, fill_value=0)
    if mergedCounts is None:
        mergedCounts = keywordCountResult
    else:
        mergedCounts = pd.merge(mergedCounts, keywordCountResult, on='ad_delivery_start_time')

# Below code generates an interactive line graph
print(mergedCounts.head(10))
fig = px.line(mergedCounts, x='ad_delivery_start_time', y=keywordsFound,
              title='Keywords found in ads. Ads that match any of the keywords: ' + str(
                  round(filledInRecords / totalRecords * 100)) + '%.',
              )
fig.update_layout(yaxis_title='Amount of ads matching a keyword', xaxis_title="Date", legend_title="Keyword",
                  font_size=30)
fig.show()
