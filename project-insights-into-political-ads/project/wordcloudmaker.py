import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
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


def draw_wordcloud(wordcloud, size, fileName):
    plt.figure(figsize=size)
    plt.imshow(wordcloud)
    plt.axis("off")
    wordcloud.to_file('wordcloud-' + fileName + '.png')


year = '2020'  # change the year to get the words from just that year
month = '10'  # change the month to get the words from just that month
democratDir = './ads/democrats'
republicanDir = './ads/republicans'

extraStopWords = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w',
    'x', 'y', 'z'
]
for word in extraStopWords:
    STOPWORDS.add(word)

for party, directory in {'democrats': democratDir, 'republicans': republicanDir}.items():
    dfs = []
    onlyfiles = [f for f in listdir(directory) if isfile(join(directory, f))]
    for file in onlyfiles:
        dfs.append(loadCsv(directory + '/' + file))

    df = pd.concat(dfs)
    columnsToCheck = ['ad_creative_bodies', 'ad_creative_link_titles', 'ad_creative_link_descriptions']
    df = df.dropna(subset=columnsToCheck)

    if year != '':
        query = "ad_delivery_start_time.str.contains('" + year + "', na=False)"
        df = df.query(query, engine='python')

    if month != '':
        query = "ad_delivery_start_time.str.contains('-" + month + "-', na=False)"
        df = df.query(query, engine='python')

    words = ''
    for column in columnsToCheck:
        # iterate through the csv file 
        words += ' '.join(df[column].astype(str))

    wordcloud = WordCloud(width=1500,
                          height=1000,
                          random_state=42,
                          collocations=False,
                          background_color='lightgreen',
                          colormap='tab10',
                          stopwords=STOPWORDS).generate(words)
    fileName = party
    if year != '':
        fileName += '-year-' + year
    if month != '':
        fileName += '-month-' + month
    draw_wordcloud(wordcloud, (12, 8), fileName)
