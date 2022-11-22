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
    allColumns = ['page_id', 'page_name', 'ad_creation_time', 'ad_delivery_start_time', 'ad_delivery_stop_time',
                  'byline', 'ad_creative_bodies', 'ad_creative_link_titles', 'ad_creative_link_captions',
                  'ad_creative_link_descriptions', 'impressions', 'spend', 'currency', 'demographic_distribution',
                  'delivery_by_region', 'publisher_platforms', 'estimated_audience_size', 'languages']
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
    units = {-12: "T", -9: "B", -6: "M", -3: "K", 0: "", 3: "m", 6: "µ", 9: "n", 12: "p", 15: "f"}
    k = -12
    while x * 10.0 ** k < 1:
        k += 3
    return f"{x * 10.0 ** k:1,.3f}{units[k]}"


def flatten_nested_json_df(df):
    df = df.reset_index()

    print(f"original shape: {df.shape}")
    print(f"original columns: {df.columns}")

    # search for columns to explode/flatten
    s = (df.applymap(type) == list).all()
    list_columns = s[s].index.tolist()

    s = (df.applymap(type) == dict).all()
    dict_columns = s[s].index.tolist()

    print(f"lists: {list_columns}, dicts: {dict_columns}")
    while len(list_columns) > 0 or len(dict_columns) > 0:
        new_columns = []

        for col in dict_columns:
            print(f"flattening: {col}")
            # explode dictionaries horizontally, adding new columns
            horiz_exploded = pd.json_normalize(df[col]).add_prefix(f'{col}.')
            horiz_exploded.index = df.index
            df = pd.concat([df, horiz_exploded], axis=1).drop(columns=[col])
            new_columns.extend(horiz_exploded.columns)  # inplace

        for col in list_columns:
            print(f"exploding: {col}")
            # explode lists vertically, adding new columns
            df = df.drop(columns=[col]).join(df[col].explode().to_frame())
            new_columns.append(col)

        # check if there are still dict o list fields to flatten
        s = (df[new_columns].applymap(type) == list).all()
        list_columns = s[s].index.tolist()

        s = (df[new_columns].applymap(type) == dict).all()
        dict_columns = s[s].index.tolist()

        print(f"lists: {list_columns}, dicts: {dict_columns}")

    print(f"final shape: {df.shape}")
    print(f"final columns: {df.columns}")
    return df


coordinatesDf = pd.read_csv('./coordinates.csv')

metricColumn = 'spend'  # or spend
stateColumn = 'delivery_by_region'
democratDir = './ads/democrats'
republicanDir = './ads/republicans'

# Load all files
democratDf = loadCsvsFromDir(democratDir, [stateColumn, metricColumn])
republicanDf = loadCsvsFromDir(republicanDir, [stateColumn, metricColumn])

partyCountResults = []
totalRecords = 0
for party, df in {'Democrats': democratDf, 'Republicans': republicanDf}.items():
    totalRecords = len(df)
    columnsToCheck = [stateColumn]
    if metricColumn != '':
        columnsToCheck.append(metricColumn)
    df = df.dropna(subset=columnsToCheck)
    filledInRecords = len(df)
    df[stateColumn] = '[' + df[stateColumn] + ']'
    columnLists = df[stateColumn].tolist()
    totalJson = []
    for columnList in columnLists:
        try:
            totalJson.append(json.loads(columnList))
        except:
            totalJson.append([])

    df[stateColumn] = totalJson
    if metricColumn != '':
        df[metricColumn] = df[metricColumn].apply(processMetricColumn)
    totalAds = len(df)
    df = flatten_nested_json_df(df)

    if metricColumn != '':
        df[metricColumn] *= df['delivery_by_region.percentage']

    df = df.groupby('delivery_by_region.region', as_index=False)
    df = df.sum()
    df['delivery_by_region.percentage'] = df['delivery_by_region.percentage'] / totalAds * 100
    df = df.rename(columns={'delivery_by_region.region': 'state', 'delivery_by_region.percentage': 'percentage'})
    df = pd.merge(df, coordinatesDf, on='state')

    countColumn = 'percentage'
    if metricColumn != '':
        countColumn = metricColumn

    df['formattedData'] = df[countColumn].apply(to_units)
    df['summary'] = (
            "<b>" + df['state'] + "</b><br>" +
            countColumn.capitalize() + ": " + df['formattedData']
    )

    sumOfCount = to_units(df.sum()[countColumn])

    fig = go.Figure(data=go.Scattergeo(
        locationmode='USA-states',
        hovertemplate=
        "%{text}<extra></extra>",
        text=df['summary'],
        textposition="top center",
        mode='markers+text',
        lat=df['lat'],
        lon=df['lon'],
        marker=dict(
            size=df[countColumn] / df[countColumn].max() * 60,
            reversescale=True,
            autocolorscale=False,
            symbol='circle',
            line=dict(
                width=0.5,
                color='rgba(0, 0, 0)'
            ),
            colorscale='plasma',
            cmin=0,
            color=df[countColumn],
            cmax=df[countColumn].max(),
            colorbar_title=countColumn
        )
    ))

    fig.update_layout(
        title='Distribution ' + countColumn + ' of ads of ' + party + '. Ads with ' + countColumn + ' data: ' + str(
            round(filledInRecords / totalRecords * 100)) + '%. Total ' + countColumn + ': ' + str(sumOfCount),
        geo=dict(
            scope='usa',
            projection_type='albers usa',
            showland=True,
            landcolor="rgb(250, 250, 250)",
            subunitcolor="rgb(217, 217, 217)",
            countrycolor="rgb(217, 217, 217)",
            countrywidth=0.5,
            subunitwidth=0.5
        ),
        font_size=13
    )
    fig.show()
