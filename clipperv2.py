import os
from moviepy.editor import VideoFileClip

def create_clips(video_path, clip_duration, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video = VideoFileClip(video_path)
    video_duration = video.duration
    print(f"Video duration: {video_duration}")

    num_clips = 160
    for i in range(num_clips):
        start_time = i * clip_duration
        end_time = start_time + clip_duration
        clip = video.subclip(start_time, end_time)
        print(f"Creating clip {i + 1}, start time: {start_time}, end time: {end_time}")

        clip_path = os.path.join(output_folder, f'clip_{i + 1}.mp4')
        clip.write_videofile(clip_path, codec='libx264', audio_codec='aac')
        print(f"Clip {i + 1} saved as: {clip_path}")

    video.close()

if __name__ == '__main__':
    video_path = "/Users/billdarnalljr/Desktop/yt-transcripts/beta/Andrew-Huberman-Dr.NoamSobelHowSmellsInfluenceOurHormonesHealth&BehaviorHubermanLabPodcast/Andrew-Huberman-Dr.NoamSobelHowSmellsInfluenceOurHormonesHealth&BehaviorHubermanLabPodcast-video.mp4"
    clip_duration = 60  # seconds
    output_folder = 'clips'
    print("Starting the script")

    create_clips(video_path, clip_duration, output_folder)
