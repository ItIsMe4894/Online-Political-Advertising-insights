import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import janitor as jn
from os import listdir
from os.path import isfile, join
import json
from quantiphy import Quantity

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

def processMetricColumn(val):
    vals = val.replace(',', '').split()
    maxVal = int(vals[1])
    if len(vals) == 4:
        maxVal = int(vals[3])
    return (int(vals[1]) + maxVal) / 2

def to_units(x):
    units = {-12: "T",-9: "B",-6: "M",-3: "K",0: "",3: "m",6: "µ",9: "n",12: "p",15: "f"}
    k = -12
    while x * 10.0**k < 1: 
        k += 3
    return f"{x*10.0**k:1,.3f}{units[k]}"

def getYear(x):
    return x.split('-')[0]

metricColumn = 'spend'
democratDir = './ads/democrats'
republicanDir = './ads/republicans'

# Load all files
democratDf = loadCsvsFromDir(democratDir, [metricColumn, 'ad_delivery_start_time'])
republicanDf = loadCsvsFromDir(republicanDir, [metricColumn, 'ad_delivery_start_time'])
democratTotal = len(democratDf)
democratFilled = 0
republicanTotal = len(republicanDf)
republicanFilled = 0

partyCountResults = []
for party, df in {'Democrats': democratDf, 'Republicans': republicanDf}.items():
    df = df.dropna(subset=[metricColumn, 'ad_delivery_start_time'])

    if party == 'Democrats':
        democratFilled = len(df)
    else:
        republicanFilled = len(df)

    df[metricColumn] = df[metricColumn].apply(processMetricColumn)
    df = df.rename(columns={'ad_delivery_start_time': 'Date'})
    df['Date'] = df['Date'].apply(getYear)

    df = df.groupby('Date', as_index=False)
    df = df.sum()
    df = df.assign(Party=party)
    partyCountResults.append(df)

concatinatedCounts = pd.concat(partyCountResults)

fig = px.bar(
    concatinatedCounts,
    x='Date',
    y=metricColumn,
    color='Party',
    title='Spend per party per year. Democrats filled in: ' + str(round(democratFilled / democratTotal * 100)) + '%. Republicans filled in: ' + str(round(republicanFilled / republicanTotal * 100)) + '%.',
    barmode='group',
    text_auto=True
)
fig.update_layout(font_size=30)
fig.show()

