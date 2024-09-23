from youtube_transcript_api import YouTubeTranscriptApi

video_id = '2DzlydHQ3fQ'
print("Getting transcript for video: ", video_id)
transcript = YouTubeTranscriptApi.get_transcript(video_id)
transcript = " ".join([t['text'] for t in transcript])
print(transcript)
