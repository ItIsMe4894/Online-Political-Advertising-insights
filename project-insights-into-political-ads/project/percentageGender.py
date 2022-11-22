import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import janitor as jn
from os import listdir
from os.path import isfile, join
import json

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

def flatten_nested_json_df(df):

    df = df.reset_index()


    # search for columns to explode/flatten
    s = (df.applymap(type) == list).all()
    list_columns = s[s].index.tolist()

    s = (df.applymap(type) == dict).all()
    dict_columns = s[s].index.tolist()

    while len(list_columns) > 0 or len(dict_columns) > 0:
        new_columns = []

        for col in dict_columns:
            # explode dictionaries horizontally, adding new columns
            horiz_exploded = pd.json_normalize(df[col]).add_prefix(f'{col}.')
            horiz_exploded.index = df.index
            df = pd.concat([df, horiz_exploded], axis=1).drop(columns=[col])
            new_columns.extend(horiz_exploded.columns) # inplace

        for col in list_columns:
            # explode lists vertically, adding new columns
            df = df.drop(columns=[col]).join(df[col].explode().to_frame())
            new_columns.append(col)

        # check if there are still dict o list fields to flatten
        s = (df[new_columns].applymap(type) == list).all()
        list_columns = s[s].index.tolist()

        s = (df[new_columns].applymap(type) == dict).all()
        dict_columns = s[s].index.tolist()


    return df

metricColumn = 'publisher_platforms' # or language
groupByColumn = 'age' # or gender
demographicColumn = 'demographic_distribution'
democratDir = './ads/democrats'
republicanDir = './ads/republicans'
gender = 'female'
percentage = 0.95

# Load all files
democratDf = loadCsvsFromDir(democratDir, [demographicColumn, metricColumn])
republicanDf = loadCsvsFromDir(republicanDir, [demographicColumn, metricColumn])

partyCountResults = []
for party, df in {'Democrats': democratDf, 'Republicans': republicanDf}.items():
    totalRecords = len(df)
    columnsToCheck = [demographicColumn]
    if metricColumn != '':
        columnsToCheck.append(metricColumn)
    df = df.dropna(subset=columnsToCheck)

    filled = len(df)

    df[demographicColumn] = '[' + df[demographicColumn] + ']'
    columnLists = df[demographicColumn].tolist()
    totalJson = []
    for columnList in columnLists:
        try:
            totalJson.append(json.loads(columnList))
        except:
            totalJson.append([])

    df[demographicColumn] = totalJson
    df = flatten_nested_json_df(df)

    df = df.rename(columns={'demographic_distribution.age': 'age', 'demographic_distribution.gender': 'gender', 'demographic_distribution.percentage': 'amount'})

    groupBy = df.groupby(['ad_archive_id', 'gender'], as_index=False)
    countResult = groupBy.sum()

    res = countResult.query("amount > " + str(percentage))
    res2 = res.query("gender == '" + gender + "'")

    print(party + ': ' + str((len(res2)/filled) * 100) + "% of the ads has an audience that consists of at least " + str(percentage*100) + "% " + gender)

