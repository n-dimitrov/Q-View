import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import pandas as pd

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

topic = 'Top Universities in Europe'

print("Searching for videos on topic: ", topic)
search_response = youtube.search().list(
    q=topic,
    part='id,snippet',
    maxResults=10,
    type='video'
).execute()

data = []
# generate a list of vidoes details
for item in search_response.get('items', []):
    vid = item['id']['videoId']
    title = item['snippet']['title']
    thumbnail = item['snippet']['thumbnails']['default']['url']
    published_at = item['snippet']['publishedAt']
    data.append({'Video ID': vid, 'Title': title, 'Thumbnail': thumbnail, 'Published At': published_at})

# Create a DataFrame
df = pd.DataFrame(data)
# sort by Published At
df = df.sort_values(by='Published At', ascending=False)
# Add a link to the video
df['Link'] = 'https://www.youtube.com/watch?v=' + df['Video ID']
# Add a column for the date
df['Date'] = pd.to_datetime(df['Published At'])
# Add a column for the number of days since the video was published
df['Days'] = (pd.Timestamp.now(tz='UTC') - df['Date']).dt.days

print(df)


# # Step 2: Download Captions
# transcripts = []
# for vid in video_ids:
#     try:
#         transcript = YouTubeTranscriptApi.get_transcript(vid)
#         text = " ".join([t['text'] for t in transcript])
#         transcripts.append(text)
#     except Exception as e:
#         print(f"Could not get transcript for video {vid}: {e}")

# # Step 3: Generate Summary
# combined_text = "\n".join(transcripts)