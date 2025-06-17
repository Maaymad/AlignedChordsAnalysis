import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
from moviepy import AudioFileClip
import soundfile as sf
import os
import csv


def convert_webm_to_wav(input_file, output_file):
    audio = AudioFileClip(input_file)
    audio.write_audiofile(output_file)
    audio.close()

def convert_mp3_to_wav(input_file, output_file):
    audio = AudioFileClip(input_file)
    audio.write_audiofile(output_file)
    audio.close()

def convert_mp4_to_wav(input_file, output_file):
    audio = AudioFileClip(input_file)
    audio.write_audiofile(output_file)
    audio.close()

def convert_m4a_to_wav(input_file, output_file):
    audio = AudioFileClip(input_file)
    audio.write_audiofile(output_file)
    audio.close()

# List of target words
TARGET_WORDS = ["drum", "curtain", "bell", "coffee", "school", "parent", 
                "moon", "garden", "hat", "farmer", "nose", "turkey", 
                "color", "house", "river"]

#function that recives a file, checks the type of the file and converts it to mp3 if it is a webm or mp4 or m4a
def convert_audio_to_mp3(file):

    if file.endswith(".wav"):
        return file

    if file.endswith(".webm"):
        convert_webm_to_wav(file, file.replace(".webm", ".wav"))
        return file.replace(".webm", ".wav")
    
    if file.endswith(".mp3"):
        convert_mp3_to_wav(file, file.replace(".mp3", ".wav"))
        return file.replace(".mp3", ".wav")
    
    elif file.endswith(".mp4"):
        convert_mp4_to_wav(file, file.replace(".mp4", ".wav"))
        return file.replace(".mp4", ".wav")
    
    elif file.endswith(".m4a"):
        convert_m4a_to_wav(file, file.replace(".m4a", ".wav"))
        return file.replace(".m4a", ".wav")
    
    else:
        print("Unsupported file type")

def process_audio_file(file_path):
    """
    Reads the audio file and saves it in WAV format using soundfile.
    """
    try:
        # Read the audio file
        data, samplerate = sf.read(file_path)

        # Define the output path for the converted file
        output_path = file_path.replace(".mp3", ".wav")  # Example for MP3 to WAV conversion
        sf.write(output_path, data, samplerate)
        print(f"Converted {file_path} to {output_path}")

        # Return the path to the converted file
        return output_path
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def transcribe_audio(file_path):
    """
    Transcribes an audio file using Google Web Speech API.
    Filters the transcript to include only target words and their order.
    """
    recognizer = sr.Recognizer()
    converted_path = convert_audio_to_mp3(file_path)
    print(f"Transcribing {converted_path}...")
    try:
        # Ensure the file is in the right format
        if converted_path is None:
            raise ValueError("File conversion failed or unsupported file type.")

        with sr.AudioFile(converted_path) as source:
            audio_data = recognizer.record(source)

        try:
            transcript = recognizer.recognize_google(audio_data).lower()  # Convert transcript to lowercase
            # Filter and map the transcript to target words
            word_order = [word for word in transcript.split() if word in TARGET_WORDS]
            return word_order
        except sr.UnknownValueError:
            return []
        except sr.RequestError as e:
            return f"Error: {e}"
    
    except Exception as e:
        raise ValueError(f"Failed to transcribe audio file {file_path}: {e}")

def process_folder(folder_path):
    """
    Processes all audio files in the folder and converts them to WAV format.
    """
    results = {}
    for file_name in os.listdir(folder_path):
        # Skip non-audio files like .DS_Store
        if not file_name.lower().endswith((".wav", ".mp3", ".aac", ".flac")):
            print(f"Skipping non-audio file: {file_name}")
            continue

        file_path = os.path.join(folder_path, file_name)
        converted_file = process_audio_file(file_path)
        if converted_file:
            try:
                word_order = transcribe_audio(converted_file)
                results[file_name] = word_order
            except ValueError as e:
                print(f"Error processing {file_name}: {e}")
    return results

def save_results_to_csv(results, output_csv_path):
    """
    Saves the transcription results to a CSV file.
    """
    with open(output_csv_path, mode="w", newline="") as csv_file:
        condition = "silence"
        writer = csv.writer(csv_file)
        # Write header row
        writer.writerow(["File Name", "Word Count", "Condition"] + TARGET_WORDS)

        # Write rows for each file, sorted by file name
        for file_name in sorted(results.keys()):  # Sort file names alphabetically
            word_order = results[file_name]
            # Calculate the sum of unique words said
            unique_word_count = len(set(word_order))  # Count unique words in the word_order list

            row = [file_name, unique_word_count, condition]  # Add condition after unique_word_count
            for word in TARGET_WORDS:
                # Find all occurrences of the word and their positions
                positions = [i + 1 for i, w in enumerate(word_order) if w == word]
                row.append(", ".join(map(str, positions)) if positions else "")
            
            writer.writerow(row)

def main():
    folder_path = "//Users//maaymadar//Downloads//list1-mismatch11-6-25"
    if not os.path.isdir(folder_path):
        print("Invalid folder path. Please provide a valid folder.")
        return

    results = process_folder(folder_path)
    output_csv_path = "//Users//maaymadar//Downloads//list1-mismatch11-6-25/subject1.csv" #input("Enter the path to save the CSV file (e.g., output.csv): ")
    save_results_to_csv(results, output_csv_path)
    print(f"Results saved to {output_csv_path}")

if __name__ == "__main__":
    main()