import os
import csv
import shutil
import tempfile
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill

from pydub import AudioSegment
from pydub.utils import which
import soundfile as sf
from moviepy import AudioFileClip
from deepgram import DeepgramClient, PrerecordedOptions

DEEPGRAM_API_KEY = "0621d176ddc509704a86222ef09ef360933d086a"

# List of target words
TARGET_WORDS = ["drum", "curtain", "bell", "coffee", "school", "parent", 
                "moon", "garden", "hat", "farmer", "nose", "turkey", 
                "color", "house", "river"]

#function that recives a file, checks the type of the file and converts it to mp3 if it is a webm or mp4 or m4a
def convert_audio_to_wav(file, temp_dir):
    base_name = os.path.splitext(os.path.basename(file))[0]
    output_path = os.path.join(temp_dir, base_name + ".wav")

    if file.endswith(".wav"):
        shutil.copy(file, output_path)
        return output_path

    elif file.endswith(".webm") or file.endswith(".mp3") or file.endswith(".m4a"):
        try:
            audio = AudioFileClip(file)
            audio.write_audiofile(output_path)
            audio.close()
            return output_path
        except Exception as e:
            print(f"Error converting {file}: {e}")
            return None
    else:
        print(f"Unsupported file type: {file}")
        return None


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

def transcribe_audio(file_path, DEEPGRAM_API_KEY):
    """
    Transcribes an audio file using Deepgram (synchronous version).
    Filters the transcript to include only target words and their order.
    """
    print(f"Transcribing {file_path}...")

    # debug timeouts
    current_time = datetime.now()
    print("Current time:", current_time)

    try:
        if file_path is None:
            raise ValueError("File path is None or unsupported file type.")

        # Initialize the Deepgram client
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        
        # Set Deepgram options
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language = "en-GB"
        )

        # Open the audio file
        with open(file_path, "rb") as file:
            buffer_data = file.read()

        # Send the audio to Deepgram for transcription
        response = deepgram.listen.rest.v("1").transcribe_file(
            {"buffer": buffer_data}, options, timeout=120
        )

        # Extract words from the response
        transcript_words = []
        if response.results is not None:
            channels = response.results.channels
            for channel in channels:
                for alternative in channel.alternatives:
                    if alternative.words:
                        transcript_words.extend([word.word.lower() for word in alternative.words])
                    elif alternative.transcript:
                        transcript_words.extend(alternative.transcript.lower().split())

        # Filter and map the transcript to target words
        word_order = [word for word in transcript_words if word in TARGET_WORDS]
        return word_order

    except Exception as e:
        print(f"Error transcribing {file_path}: {e}")
        return []

def process_folder(folder_path):
    """
    Processes all audio files in the folder:
    Converts them to WAV and transcribes using Deepgram.
    Uses a temporary folder for converted files.
    """
    results = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary folder: {temp_dir}")

        for file_name in os.listdir(folder_path):
            if not file_name.lower().endswith((".wav", ".mp3", ".m4a", ".webm")):
                print(f"Skipping non-audio file: {file_name}")
                continue

            file_path = os.path.join(folder_path, file_name)
            converted_file = convert_audio_to_wav(file_path, temp_dir)

            if converted_file:
                try:
                    word_order = transcribe_audio(converted_file, DEEPGRAM_API_KEY)
                    results[file_name] = word_order
                except ValueError as e:
                    print(f"Error processing {file_name}: {e}")

        # At this point, temp_dir will be deleted automatically
    return results

def save_results_to_csv(results, output_csv_path, subject_name):
    """
    Saves the transcription results to a CSV file.
    Adds columns for File Name, Subject, Condition, Word Count, and each target word.
    The target word columns contain numbers indicating the order in which the words are said.
    """
    with open(output_csv_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        # Write header row
        writer.writerow(["File Name", "Subject", "Condition", "Word Count"] + TARGET_WORDS)

        # Write rows for each file, sorted by file name
        for file_name in sorted(results.keys()):  # Sort file names alphabetically
            word_order = results[file_name]
            # Calculate the sum of unique words said
            unique_word_count = len(set(word_order))  # Count unique words in the word_order list

            # Determine condition based on folder name
            if "mismatch" in output_csv_path.lower():
                condition = "mismatch"
            elif "match" in output_csv_path.lower():
                condition = "match"
            else:
                condition = "unknown"

            # Create a dictionary to store the order of each target word
            word_positions = {word: [] for word in TARGET_WORDS}
            for index, word in enumerate(word_order, start=1):
                if word in TARGET_WORDS:
                    word_positions[word].append(index)

            # Flatten the word positions into a single row
            row = [file_name, subject_name, condition, unique_word_count]
            for word in TARGET_WORDS:
                row.append(",".join(map(str, word_positions[word])) if word_positions[word] else "")

            writer.writerow(row)

def export_to_excel_with_colors(input_path, output_path):
    # Define the column colors
    column_colors = {
        "drum": ("FFCCCC", "CC6666"),
        "curtain": ("FFCCCC", "CC6666"),
        "bell": ("CCFFCC", "66CC66"),
        "coffee": ("CCFFCC", "66CC66"),
        "school": ("CCCCFF", "6666CC"),
        "parent": ("CCCCFF", "6666CC"),
        "moon": ("CCCCFF", "6666CC"),
        "garden": ("CCCCFF", "6666CC"),
        "hat": ("FFFFCC", "CCCC66"),
        "farmer": ("FFFFCC", "CCCC66"),
        "nose": ("FFFFCC", "CCCC66"),
        "turkey": ("FFFFCC", "CCCC66"),
        "color": ("FFCCFF", "CC66CC"),
        "house": ("FFCCFF", "CC66CC"),
        "river": ("CCCCCC", "666666"),
    }

    # Read the CSV file, keeping "NA" as string
    df = pd.read_csv(input_path, keep_default_na=False, na_values=[])

    # Create a new workbook
    wb = Workbook()
    ws = wb.active

    # Write the DataFrame to the worksheet
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        ws.append(row)

    # Apply the colors to the columns
    for col in df.columns:
        if col in column_colors:
            data_fill = PatternFill(start_color=column_colors[col][0],
                                  end_color=column_colors[col][0],
                                  fill_type="solid")
            header_fill = PatternFill(start_color=column_colors[col][1],
                                    end_color=column_colors[col][1],
                                    fill_type="solid")

            # Color the header
            header_cell = ws.cell(row=1, column=df.columns.get_loc(col)+1)
            header_cell.fill = header_fill

            # Color the data cells
            for row in range(2, ws.max_row + 1):
                cell = ws.cell(row=row, column=df.columns.get_loc(col)+1)
                cell.fill = data_fill

    # Save the workbook
    wb.save(output_path)
    print(f"Colored Excel file saved to {output_path}")

def main():
    folder_path = '//Users//maaymadar//Downloads//list 1 - mismatch 11-6-25'
    subject_number = "1"
    subject_name = f"Subject_{subject_number}"
    output_csv_path = f"{folder_path}/{subject_name}.csv"
    output_excel_path = f"{folder_path}/{subject_name}_colored.xlsx"

    results = process_folder(folder_path)
    save_results_to_csv(results, output_csv_path, subject_number)
    print(f"Results saved to {output_csv_path}")

    # Export results to Excel with colors
    export_to_excel_with_colors(output_csv_path, output_excel_path)

if __name__ == "__main__":
    main()