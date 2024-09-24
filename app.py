import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re

st.set_page_config(
    page_title="Q-View",
    page_icon="🟡",
    layout="wide",
)

def iso_duration_to_seconds(iso_duration):
    # Parse the ISO 8601 duration
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    
    if not match:
        return None
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def search_youtube(topic, maxResults):
    YOUTUBE_API_KEY = st.secrets['YOUTUBE_API_KEY']
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    search_response = youtube.search().list(
        q=topic,
        part='id,snippet',
        maxResults=maxResults,
        type='video'
    ).execute()
 
    video_ids = [item['id']['videoId'] for item in search_response['items']]
    video_response = youtube.videos().list(
        id=','.join(video_ids),
        part='statistics,contentDetails'
    ).execute()

    with st.expander('Response Details'):    
        st.subheader('Search')
        st.write(search_response)
        st.subheader('Videos')
        st.write(video_response)

    data = []
    for item in search_response.get('items', []):
        vid = item['id']['videoId']
        title = item['snippet']['title']
        thumbnail = item['snippet']['thumbnails']['default']['url']
        published_at = item['snippet']['publishedAt']

        # find the items in the video response with the same video ID
        # {  
        #     "kind":"youtube#video"
        #     "etag":"xCZ-CMSwma2Bg69JWg5edXS5A2U"
        #     "id":"PZ7lDrwYdZc"
        #     "contentDetails":{
        #         "duration":"PT28M11S"
        #         "dimension":"2d"
        #         "definition":"hd"
        #         "caption":"true"
        #         "licensedContent":true
        #         "contentRating":{}
        #         "projection":"rectangular"
        #     }
        #     "statistics":{
        #         "viewCount":"18402665"
        #         "likeCount":"715738"
        #         "favoriteCount":"0"
        #         "commentCount":"7613"
        #     }
        # }
        for item in video_response['items']:
            if item['id'] == vid:
                stats = item['statistics']
                content = item['contentDetails']
                # as integers
                views = int(stats['viewCount'])
                likes = int(stats['likeCount'])
                caption = content['caption'] == 'true'
                duration = content['duration']
                seconds = iso_duration_to_seconds(duration)

        data.append({'Video ID': vid, 'Title': title, 'Thumbnail': thumbnail, 'Published At': published_at, 'Views': views, 'Likes': likes, 'Caption': caption, 'Duration': duration, 'Seconds': seconds})  

        df = pd.DataFrame(data)
        df = df.sort_values(by='Published At', ascending=False)
        df['Link'] = 'https://www.youtube.com/watch?v=' + df['Video ID']
        df['Date'] = pd.to_datetime(df['Published At'])
        df['Days'] = (pd.Timestamp.now(tz='UTC') - df['Date']).dt.days
                
    return df

st.title('Q-View')
st.write('A simple tool to search for videos on YouTube and generate summaries of the search results')

with st.container(border=True):
    topic = st.text_input('Enter a topic to search for videos on YouTube', 'Top Universities in Europe')
    button = st.button('Q-View')
    if (button):
        with st.spinner('Searching... '):
            df = search_youtube(topic, 20)

            with st.expander('Results'):
                ff = st.data_editor(
                    df,
                    hide_index=True,
                    column_config={
                        "Video ID" : st.column_config.TextColumn(label="Video ID"),
                        "Title": st.column_config.TextColumn(label="Title"),
                        "Published At": st.column_config.TextColumn(label="Published At"),
                        "Duration": st.column_config.TextColumn(label="Duration"),
                        "Views": st.column_config.NumberColumn(label="Views"),
                        "Likes": st.column_config.NumberColumn(label="Likes"),
                        "Thumbnail": st.column_config.ImageColumn(label="Thumbnail"),
                        "Caption": st.column_config.CheckboxColumn(label="Caption"),
                    },
                    disabled=[],
                    column_order=('Title', 'Published At', 'Duration', 'Views', 'Likes', 'Thumbnail', 'image', 'feature', 'volume', 'Caption'),
                    )

            # only with cations
            df = df[(df['Caption'])]

            # sort by views
            df = df.sort_values(by='Views', ascending=False)

            # st.write(df)
            # itreate over the rows
            for index, row in df.iterrows():
                with st.container(border=True):
                    st.subheader(row['Title'])

                    col1, col2, col3 = st.columns(3)
                    col1.image(row['Thumbnail'])
                    col2.write(row['Link'])
                    pa = pd.to_datetime(row['Published At']).strftime('%Y-%m-%d')
                    col3.write('Published At ' + pa)

                    col4, col5, col6 = st.columns(3)
                    col4.metric('Views', row['Views'])
                    col5.metric('Likes', row['Likes'])
                    col6.metric('Duration (sec)', row['Seconds'])

