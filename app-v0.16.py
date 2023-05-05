import os
from dotenv import load_dotenv
import time
import re
import openai
import yt_dlp
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import concurrent.futures

load_dotenv()

openai.api_key = os.environ['CHATGPT_API_KEY']
def generate_question(podcast_name, host_name, guest_names, topic):
    if guest_names:
        guests = ', '.join(guest_names)
        question = f"Please provide a well-structured and coherent summary of the following portion of this transcript from {podcast_name} featuring the host(s): {host_name} and guest(s) {guests}. Provide examples, details and quotes from the transcript to explain what they are talking about. This is going to be sent in sections. Do not start the response with any intro, just go into the providing the examples. No need for a conclusion sentence either."
    else:
        question = f"Please provide a well-structured and coherent summary of the following portion of this transcript from {podcast_name}  featuring the host(s): {host_name}. Provide examples, details and quotes from the transcript to explain what they are talking about. This is going to be sent in sections.Do not start the response with any intro, just go into the providing the examples. No need for a conclusion sentence either."
    return question
def create_questions_file(directory, filename, podcast_name, host_name, guest_names, topic):
    # Create the directory structure
    questions_directory = os.path.join(directory, "chatgpt", "questions")
    os.makedirs(questions_directory, exist_ok=True)
    
    # Create the file path
    file_path = os.path.join(questions_directory, filename)
    
    # Generate the question and write it to the file
    question = generate_question(podcast_name, host_name, guest_names, topic)
    with open(file_path, "w") as file:
        file.write(question + "\n")
    
    return file_path

def generate_youtube_description(final_summary, topic):
    # Prepare the prompt for ChatGPT
    prompt = f"Generate a YouTube video description for a channel called 'The Pod Slice', which summarizes long-form podcasts. The video is based on the following summary:\n\n{final_summary}\n\nPlease create 3-5 chapters in sequential order and then  bullet points about those topics based on the summary and make sure there is a intro paragraph summarazing what this video is about. Make sure to include the words: AI summary, the pod slice, podcast summary, and podcast recap. "

    # Send the prompt to ChatGPT
    completion = get_chat_completion(prompt)

    # Extract the generated description
    youtube_description = completion.choices[0].message['content'].lstrip()

    return youtube_description

def generate_youtube_tags(youtube_description):
    prompt = f"Generate popular SEO tags in CSV format based on the following YouTube video description:\n{youtube_description}"
    completion = get_chat_completion(prompt)
    response_text = completion.choices[0].message['content'].lstrip()
    tags = [tag.strip() for tag in response_text.split(',') if tag.strip()]
    csv_tags = ', '.join(tags)
    return csv_tags




def read_questions(filename):
    with open(filename, 'r') as file:
        questions = [line.strip() for line in file.readlines()]
    return questions

def read_transcript(filename):
    with open(filename, 'r') as file:
        transcript = file.read()
    return transcript

def save_response_to_file(response, file_path):
    with open(file_path, "w") as file:
        file.write(response.lstrip())

def split_text(text, chunk_size=1000):
    words = text.split()
    num_chunks = (len(words) + chunk_size - 1) // chunk_size
    return [" ".join(words[i * chunk_size:(i + 1) * chunk_size]) for i in range(num_chunks)]


def save_combined_chunks_to_file(combined_chunks, directory):
    output_file = os.path.join(directory, "summary-out-chunks.txt")
    with open(output_file, "w") as file:
        for chunk in combined_chunks:
            file.write(chunk)
            file.write("\n")
    print(f"Combined chunks saved to {os.path.abspath(output_file)}")
def save_combined_sum1_to_file(directory):
    sum1_directory = os.path.join(directory, "chatgpt", "sum1")
    output_file = os.path.join(sum1_directory, "summary-out-chunks.txt")

    combined_text = ""
    summary_files = []
    for file_name in sorted(os.listdir(sum1_directory)):
        if file_name.startswith("summary-") and file_name.endswith(".txt"):
            summary_files.append(file_name)
            with open(os.path.join(sum1_directory, file_name), "r") as file:
                combined_text += file.read()

    # Check if output_file exists and has the same number of lines as summaries
    if os.path.exists(output_file):
        with open(output_file, "r") as file:
            existing_lines = file.readlines()
        if len(existing_lines) > 10:
            print(f"Skipping writing to {os.path.abspath(output_file)}: File already contains all summaries.")
            return

    with open(output_file, "w") as file:
        file.write(combined_text)

    print(f"Combined summaries saved to {os.path.abspath(output_file)}")

def save_combined_sum2_to_file(directory):
    sum2_directory = os.path.join(directory, "chatgpt", "sum2")
    output_file = os.path.join(sum2_directory, "summary-out-chunks.txt")

    combined_text = ""
    summary_files = []
    for file_name in sorted(os.listdir(sum2_directory)):
        if file_name.startswith("summary-out") and file_name.endswith(".txt"):
            summary_files.append(file_name)
            with open(os.path.join(sum2_directory, file_name), "r") as file:
                combined_text += file.read()

    # Check if output_file exists and has the same number of lines as summaries
    if os.path.exists(output_file):
        with open(output_file, "r") as file:
            existing_lines = file.readlines()
        if len(existing_lines) > 10:
            print(f"Skipping writing to {os.path.abspath(output_file)}: File already contains all summaries.")
            return

    with open(output_file, "w") as file:
        file.write(combined_text)

    print(f"Combined summaries saved to {os.path.abspath(output_file)}")


def split_text_into_paragraphs(text, num_paragraphs=6):
    paragraphs = [p for p in text.strip().split('\n') if p.strip()]
    print(len(paragraphs)/num_paragraphs)
    num_chunks = (len(paragraphs) + num_paragraphs - 1) // num_paragraphs
    return ["\n".join(paragraphs[i * num_paragraphs:(i + 1) * num_paragraphs]) for i in range(num_chunks)]


def get_chat_completion(prompt, tries=3, delay=2, backoff=2, max_delay=30, timeout=30):
    current_try = 0
    while current_try < tries:
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(openai.ChatCompletion.create, model='gpt-3.5-turbo', messages=[
                    {'role': 'system', 'content': 'You are a detailed and analytical assistant, skilled at summarizing complex podcast transcripts into engaging and concise scripts suitable for a YouTube audience.'},
                    {'role': 'user', 'content': prompt}
                ], temperature=1, max_tokens=2500)
                completion = future.result(timeout=timeout)
            return completion
        except (Exception, concurrent.futures.TimeoutError) as e:
            current_try += 1
            if current_try == tries:
                raise e
            wait_time = min(delay * (backoff ** (current_try - 1)), max_delay)
            print(f"Retry attempt {current_try} failed. Waiting {wait_time} seconds before the next attempt.")
            time.sleep(wait_time)

def process_chunks(transcript, questions, directory):
    chunks = split_text(transcript)
    response_files = []
    
    sum1_directory = os.path.join(directory, "chatgpt", "sum1")
    os.makedirs(sum1_directory, exist_ok=True)

    for i, chunk_text in enumerate(chunks):
        response_file = os.path.join(sum1_directory, f"summary-{i+1}.txt")
        if os.path.exists(response_file):
            with open(response_file, "r") as file:
                existing_text = file.read()
            if len(existing_text.split()) > 10:
                print(f"Skipping chunk {i+1}: Existing summary has more than 10 words.")
                response_files.append(response_file)
                continue
        print(f"Processing chunk {i+1}")
        for question in questions:
            prompt = f"{question}\n{chunk_text}"
            completion = get_chat_completion(prompt)
            response_text = completion.choices[0].message['content'].lstrip()
            save_response_to_file(response_text, response_file)
        response_files.append(response_file)
             # Move on to the next chunk

    return response_files






def process_combined_chunks(combined_chunks, combined_questions, directory):
    response_files = []

    os.makedirs(os.path.join(directory, "chatgpt", "sum2"), exist_ok=True)

    for i, combined_chunk in enumerate(combined_chunks):
        response_file = os.path.join(directory, "chatgpt", "sum2", f"summary-out-{i*4+1}-{(i+1)*4}.txt")
        if os.path.exists(response_file):
            with open(response_file, "r") as file:
                existing_text = file.read()
            if len(existing_text.split()) > 10:
                print(f"Skipping combined chunk {i+1}: Existing summary has more than 10 words.")
                response_files.append(response_file)
                continue
        print(f"Processing combined chunk {i+1}")
        for question in combined_questions:
            prompt = f"{question}\n{combined_chunk}"
            completion = get_chat_completion(prompt)
            response_text = completion.choices[0].message['content'].lstrip()
            save_response_to_file(response_text, response_file)
            response_files.append(response_file)

    return response_files

def process_final_chunks(summary_out_chunks_file, final_question_file, directory):
    with open(summary_out_chunks_file, 'r') as file:
        summary_out_chunks_text = file.read()
    with open(final_question_file, 'r') as file:
        final_question = file.read().strip()

    final_chunks = split_text_into_paragraphs(summary_out_chunks_text)
    response_files = []

    sum3_directory = os.path.join(directory, "chatgpt", "sum3")
    os.makedirs(sum3_directory, exist_ok=True)

    for i, final_chunk in enumerate(final_chunks):
        response_file = os.path.join(sum3_directory, f"final-summary-{i+1}.txt")

        if os.path.exists(response_file):
            with open(response_file, "r") as file:
                existing_text = file.read()
            if len(existing_text.split()) > 10:
                print(f"Skipping final chunk {i+1}: Existing summary has more than 10 words.")
                response_files.append(response_file)
                continue

        print(f"Processing final chunk {i+1}")
        prompt = f"{final_question}\n{final_chunk}"
        completion = get_chat_completion(prompt)
        response_text = completion.choices[0].message['content'].lstrip()
        save_response_to_file(response_text, response_file)
        response_files.append(response_file)

        combine_final_summaries(response_files, directory)

    return response_files

def combine_final_summaries(response_files, directory):
    output_file = os.path.join(directory, "chatgpt", "sum3", "final-summary.txt")
    combined_text = ""

    for file_path in response_files:
        with open(file_path, "r") as file:
            combined_text += file.read() + "\n"

    with open(output_file, "w") as file:
        file.write(combined_text)

    print(f"Final summary saved to {os.path.abspath(output_file)}")



def progress_bar(progress_data):
    progress = progress_data.get("percentage")
    if progress is None:
        return
    progress = progress / 100
    bar_length = 50
    filled_length = int(round(bar_length * progress))
    bar = '=' * filled_length + ' ' * (bar_length - filled_length)
    print(f'\r[{bar}] {progress * 100:.1f}%', end='')

def sanitize_filename(filename):
    return re.sub(r'[\\/:"*?<>|]', '', filename)

def download_video_and_transcript(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(video_url, download=False)
    
    channel_name = sanitize_filename(info.get('uploader', '').replace(' ', '-').replace('"', '').replace("'", "").replace(',', ''))
    video_title = sanitize_filename(info.get('title', '').replace(' ', '').replace('"', '').replace("'", "").replace(',', ''))
    directory = f"{channel_name}-{video_title}"
    os.makedirs(directory, exist_ok=True)

    
    # Download thumbnail
    thumbnail_url = info.get('thumbnail', None)
    if thumbnail_url:
        print("Downloading thumbnail...")
        response = requests.get(thumbnail_url)
        with open(f"{directory}/{directory}-thumbnail.jpg", "wb") as file:
            file.write(response.content)
        print("Thumbnail downloaded!")
    
    print("Downloading video...")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]',
        'outtmpl': f'{directory}/{directory}-video.%(ext)s',
        'progress_hooks': [progress_bar],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    print("\nDownload complete!")

    # Get list of available transcripts
    available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
    transcript = None

    # Check if English transcript is available
    try:
        transcript = available_transcripts.find_transcript(['en'])
    except Exception:
        pass

    # If English not available, check for Spanish
    if not transcript:
        try:
            transcript = available_transcripts.find_transcript(['es'])
        except Exception:
            print("English and Spanish transcripts are not available.")
            return

    transcript_list = transcript.fetch()
    file_name = f"{directory}/{directory}-transcript.txt"
    
    with open(file_name, "w") as file:
        for line in transcript_list:
            text = line["text"]
            file.write(text + "\n")
    print(f"Transcript saved to {os.path.abspath(file_name)}")
    return file_name, directory



def combine_all_summaries(directory):
    sum1_directory = os.path.join(directory, "chatgpt", "sum1")
    
    # Get a list of all the summary files in the directory, in numerical order
    summary_files = sorted([f for f in os.listdir(sum1_directory) if f.startswith("summary-")], key=lambda f: int(f.split('-')[1].split('.')[0]))
    
    # Combine all the summaries into one string
    combined_summary = ""
    for filename in summary_files:
        with open(os.path.join(sum1_directory, filename), "r") as file:
            combined_summary += file.read()
            combined_summary += "\n\n"  # add a separator between summaries

    # Write the combined summary to a new file
    output_file = os.path.join(sum1_directory, "summary-all.txt")
    with open(output_file, "w") as file:
        file.write(combined_summary)

    print(f"Combined all summaries saved to {os.path.abspath(output_file)}")

def combine_responses(response_files):
    combined_text = ""
    for file_path in response_files:
        with open(file_path, "r") as file:
            combined_text += file.read()
    return combined_text
def main():
    podcast_name = "Huberman Lab Podcast"
    host_name = "Dr. Andrew Huberman"
    guest_names = ["Dr. Noam Sobel"]
    topic = ""


    video_id = "cS7cNaBrkxo"
    transcript_file, directory = download_video_and_transcript(video_id)
    
    questions_file = create_questions_file(directory, "question-1.txt", podcast_name, host_name, guest_names, topic)
    questions = read_questions(questions_file)
    transcript = read_transcript(transcript_file)    

    response_files = process_chunks(transcript, questions, directory)
    # combined_chunks = [combine_responses(response_files[i:i + 4]) for i in range(0, len(response_files), 4)]

   
    # save_combined_sum1_to_file(directory)


    # Change the questions file for the combined file if needed
    # combined_questions_file = os.path.join(directory, "chatgpt", "questions", "question-1.txt")
    # combined_questions = read_questions(combined_questions_file)
    # process_combined_chunks(combined_chunks, combined_questions, directory)
    # save_combined_chunks_to_file(combined_chunks, directory)
    final_summary_file1 = os.path.join(directory, "chatgpt", "sum1", "summary-out-chunks.txt")
    combine_all_summaries(directory)
    youtube_description_file1 = os.path.join(directory, "chatgpt", "sum1", "youtube_description.txt")
    if os.path.exists(youtube_description_file1):
        print(f"YouTube description file already exists at {os.path.abspath(youtube_description_file1)}. Skipping generation.")
        with open(youtube_description_file1, "r") as file:
            youtube_description = file.read()
    else:
        youtube_description = generate_youtube_description(final_summary_file1, topic)
        with open(youtube_description_file1, "w") as file:
            file.write(youtube_description)
        print(f"YouTube description saved to {os.path.abspath(youtube_description_file1)}")
    
    youtube_tags_file1 = os.path.join(directory, "chatgpt", "sum1", "youtube_tags.txt")
    if os.path.exists(youtube_tags_file1):
        print(f"YouTube tags file already exists at {os.path.abspath(youtube_tags_file1)}. Skipping generation.")
    else:
        youtube_tags = generate_youtube_tags(youtube_description)
        with open(youtube_tags_file1, "w") as file:
            file.write(youtube_tags)
        print(f"YouTube tags saved to {os.path.abspath(youtube_tags_file1)}")



if __name__ == "__main__":
    main()
   