import pandas as pd
import plotly.express as px
import janitor as jn
from os import listdir
from os.path import isfile, join

# Returns dataframe without columns that we dont use
def loadCsv(csv, columnsToKeep):
    df = pd.read_csv(csv)
    allColumns = ['page_id', 'page_name', 'ad_creation_time', 'ad_delivery_start_time', 'ad_delivery_stop_time', 'byline', 'ad_creative_bodies', 'ad_creative_link_titles', 'ad_creative_link_captions', 'ad_creative_link_descriptions', 'impressions', 'spend', 'currency', 'demographic_distribution', 'delivery_by_region', 'publisher_platforms', 'estimated_audience_size', 'languages']
    columnsToDrop = [item for item in allColumns if item not in columnsToKeep]
    df = df.drop(columns=columnsToDrop)
    return df

def loadCsvsFromDir(dir, columns):
    dfs = []
    onlyfiles = [f for f in listdir(dir) if isfile(join(dir, f))]
    for file in onlyfiles:
        dfs.append(loadCsv(dir + '/' + file, columns))

    df = pd.concat(dfs)
    return df

# Change column
column = 'languages'
democratDir = './ads/democrats'
republicanDir = './ads/republicans'
amountNonOtherBars = 9

# Load all files
democratDf = loadCsvsFromDir(democratDir, [column])
republicanDf = loadCsvsFromDir(republicanDir, [column])

totalDemo = len(democratDf)
demoFilledIn = 0
totalRepublic = len(republicanDf)
republicFilledIn = 0

partyCountResults = []
for party, df in {'Democrats': democratDf, 'Republicans': republicanDf}.items():
    df = df.dropna(subset=[column])
    if party == 'Democrats':
        demoFilledIn = len(df)
    else:
        republicFilledIn = len(df)
    groupBy = df.groupby(column, as_index=False)
    countResult = groupBy.count()
    countResult = countResult.rename(columns={'ad_archive_id': 'count'})
    countResult = countResult.assign(Party=party)
    countResult = countResult.sort_values(by = 'count', ascending=False)
    
    nonOtherBars = countResult.iloc[:amountNonOtherBars,:]
    otherBar = countResult.iloc[amountNonOtherBars:,:]
    otherBarValue = otherBar['count'].sum()
    otherRow = pd.Series({
        column: 'Other',
        'count': otherBarValue,
        'Party': party
    })
    result = pd.concat([
        nonOtherBars, 
        pd.DataFrame([otherRow], columns=otherRow.index)]
    ).reset_index(drop=True)

    partyCountResults.append(result)

# Merge data sets
concatinatedCounts = pd.concat(partyCountResults)

fig = px.histogram(
    concatinatedCounts,
    x='Party',
    y='count',
    color=column,
    title="Ads with " + column + ' data: Democrats: ' + str(round(demoFilledIn/totalDemo*100)) + '%, Republicans: ' + str(round(republicFilledIn/totalRepublic*100)) + '%.',
    text_auto=True,
    barmode='group'
)
fig.update_layout(
    yaxis_title=column.capitalize(),
    font_size=30
)
fig.show()

