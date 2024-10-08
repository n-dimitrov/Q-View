import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from youtube_transcript_api import YouTubeTranscriptApi
from st_files_connection import FilesConnection
import requests
import json

st.set_page_config(
    page_title="Q-View",
    page_icon="🟡",
    layout="wide",
)

GCS_BUCKET = 'q-view'
GCS_STOGAGE_PATH = f'gs://{GCS_BUCKET}'

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
                views = 0
                if 'viewCount' in stats:
                    views = int(stats['viewCount'])
                likes = 0
                if 'likeCount' in stats:
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

transcripts_files = []
youtube_videos = []
now = pd.Timestamp.now(tz='UTC').strftime('%Y%m%d-%H%M%S')
path = f"{now}"

# video search results
with st.container(border=True):
    st.subheader('Input')
    topic = st.text_input('Enter a topic to search for videos on YouTube', 'The future of AI')
    button = st.button('Q-View')
    if (button):
        with st.spinner('Searching... '):
            df = search_youtube(topic, 20)
            path = f'{now}-{topic.replace(" ", "-")}'

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
            
            # max 5
            df = df.head(5)

            # connect to google cloud storage
            conn = st.connection('gcs', type=FilesConnection)

            # itreate over the rows
            for index, row in df.iterrows():
                with st.container(border=True):
                    title = row['Title']
                    st.subheader(title)

                    video_id = row['Video ID']
                    st.write(video_id)

                    col1, col2, col3 = st.columns(3)
                    col1.image(row['Thumbnail'])
                    col2.write(row['Link'])
                    pa = pd.to_datetime(row['Published At']).strftime('%Y-%m-%d')
                    days = row['Days']
                    col3.write('Published At ' + pa + " / " + str(days) + " days ago")    

                    col4, col5, col6 = st.columns(3)
                    col4.metric('Views', row['Views'])
                    col5.metric('Likes', row['Likes'])
                    col6.metric('Duration (sec)', row['Seconds'])

                    youtube_videos.append({
                        'title': title,
                        'id': video_id,
                        'link': row['Link'],
                        'published_at': pa,
                        'days': days,
                        'views': row['Views'],
                        'likes': row['Likes'],
                        'duration': row['Seconds']
                    })

                    # try to get the transcript
                    transcript = ''
                    try:
                        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
                        transcript = " ".join([t['text'] for t in transcript])
                    except:
                        st.error('No transcript available')
                        pass

                    with st.expander('Transcript'):
                        st.write(transcript)

                    with st.spinner("Uploading transcript..."):
                        filename = f"{GCS_STOGAGE_PATH}/{path}/{video_id}.txt"
                        with conn.open(filename, "w") as f:
                            f.write(transcript)
                        # st.write("Transcript uploaded to " + filename)
                        transcripts_files.append(filename)


        with st.container(border=True):
            st.subheader('Request Summary')
            json_filename = f"{GCS_STOGAGE_PATH}/{path}/request.json"
            result_filename = f"{GCS_STOGAGE_PATH}/{path}/result.json"
            request_json = {
                'topic': topic,
                'videos': youtube_videos,
                'transcripts': transcripts_files,
                'prompt': 'You are a helpful AI assistant wich acts as a tutor for students. Your first task is to generate a nice summary of the provided transcripts which are related to the topic of ' + topic + '. Please provide a summary of the provided transcripts. Your second task is to generate a 10 questions related to the same topic based only on information from the provided transcripts. Please provide 10 questions related to the topic and the answer.'
            }

            json_string = json.dumps(request_json)
            with st.expander('Request JSON', expanded=False):
                st.write(request_json)
            with st.spinner("Uploading request..."):
                with conn.open(json_filename, "w") as f:
                    f.write(json_string)
                st.write("Request file uploaded to " + json_filename)

        with st.container(border=True):
            st.subheader('Result')
            # send the request to the AI
            with st.spinner("AI processing..."):
                headers = {
                    "Content-Type": "application/json; charset=UTF-8"
                }
                url = "https://q-view-706353392380.europe-west3.run.app"
                response = requests.post(url, headers=headers, json=request_json)
                if response.status_code in [200, 201]:
                    result = response.json()
                    st.info(result['result'])
                    # save the result
                    with conn.open(result_filename, "w") as f:
                        f.write(json.dumps(result))
                    st.write("Result file uploaded to " + result_filename)
                else:
                    st.error(f"Error: Received status code {response.status_code}")



            



