import speech_recognition as sr
from moviepy import AudioFileClip
import soundfile as sf
import os
import csv
import shutil
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows



def convert_webm_to_wav(input_file, output_file):
    audio = AudioFileClip(input_file)
    audio.write_audiofile(output_file)
    audio.close()

def convert_mp3_to_wav(input_file, output_file):
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

    elif file.endswith(".webm"):
        convert_webm_to_wav(file, file.replace(".webm", ".wav"))
        return file.replace(".webm", ".wav")
    
    elif file.endswith(".mp3"):
        convert_mp3_to_wav(file, file.replace(".mp3", ".wav"))
        return file.replace(".mp3", ".wav")
    
    elif file.endswith(".m4a"):
        convert_m4a_to_wav(file, file.replace(".m4a", ".wav"))
        return file.replace(".m4a", ".wav")
    
    else:
        print("Unsupported file type")


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
        if not file_name.lower().endswith((".wav", ".mp3", ".webm", ".flac")):
            print(f"Skipping non-audio file: {file_name}")
            continue

        file_path = os.path.join(folder_path, file_name)
        converted_file = convert_audio_to_mp3(file_path)
        if converted_file:
            try:
                word_order = transcribe_audio(converted_file)
                results[file_name] = word_order
            except ValueError as e:
                print(f"Error processing {file_name}: {e}")
    return results

def save_results_to_csv(results, output_csv_path, condition):
    """
    Saves the transcription results to a CSV file.
    """
    with open(output_csv_path, mode="w", newline="") as csv_file:
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
def extract_subject_ids(folder_path):
    """
    Extracts subject IDs from filenames in the given folder.
    """
    ids = set()
    for file_name in os.listdir(folder_path):
        if file_name.startswith("R_") and "_" in file_name:
            ids.add(file_name.split("_")[1])  # Extract the ID between "R_" and the next "_"
    return ids

def copy_subject_files(subject_ids, source_folders, temp_folder):
    """
    Copies files matching the subject IDs from source folders to a temporary folder.
    """
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    for folder in source_folders:
        for file_name in os.listdir(folder):
            if file_name.startswith("R_") and "_" in file_name:
                file_id = file_name.split("_")[1]
                if file_id in subject_ids:
                    source_path = os.path.join(folder, file_name)
                    destination_path = os.path.join(temp_folder, file_name)
                    shutil.copy(source_path, destination_path)

def process_subject(temp_folder, output_csv_path, condition):
    """
    Processes audio files for a subject by transcribing them and saving results to a CSV.
    """
    results = process_folder(temp_folder)  # Use your existing process_folder function
    save_results_to_csv(results, output_csv_path, condition)  # Save results with condition

def handle_subjects(base_path, folders, output_csv_path, condition):
    """
    Processes all subjects and exports their data into a single CSV file.
    """
    # Extract all subject IDs from the sil folders
    all_subject_ids = set()
    for folder in folders:
        all_subject_ids.update(extract_subject_ids(folder))  # Collect all unique IDs

    print(f"Found {len(all_subject_ids)} unique subject IDs.")

    # Prepare to write to a single CSV file
    with open(output_csv_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        # Write header row
        writer.writerow(["File Name", "Trial Number", "Word Count", "Condition"] + TARGET_WORDS)

        # Process each subject ID individually
        for subject_index, subject_id in enumerate(sorted(all_subject_ids), start=1):  # Enumerate subjects with an index
            temp_folder = os.path.join(base_path, "temp_subject")  # Temporary folder for subject files
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)

            # Use a set to track copied files and avoid duplicates
            copied_files = set()

            # Collect files for the current subject ID from all sil and mus folders
            trial_number = 1  # Initialize trial number for the subject
            for folder in folders:
                folder_name = os.path.basename(folder)  # Get the name of the original folder
                for file_name in os.listdir(folder):
                    if file_name.startswith("R_") and "_" in file_name:
                        file_id = file_name.split("_")[1]
                        if file_id == subject_id and file_name not in copied_files:  # Match the current subject ID and avoid duplicates
                            source_path = os.path.join(folder, file_name)
                            # Rename the file according to the subject index and folder name
                            new_file_name = f"sub{subject_index}_{folder_name}.webm"
                            destination_path = os.path.join(temp_folder, new_file_name)
                            shutil.copy(source_path, destination_path)
                            copied_files.add(file_name)  # Add the file to the set of copied files

            # Process the files in the temp folder
            results = process_folder(temp_folder)  # Use your existing process_folder function
            # Sort by folder name and file name
            sorted_results = sorted(results.items(), key=lambda x: (x[0].split("_")[1], x[0]))

            # Write results for the current subject to the CSV
            for file_name, word_order in sorted_results:
                unique_word_count = len(set(word_order))  # Count unique words in the word_order list
                # Remove file extension from the file name
                file_name_no_ext = os.path.splitext(file_name)[0]
                row = [file_name_no_ext, trial_number, unique_word_count, condition]
                for word in TARGET_WORDS:
                    # Find all occurrences of the word and their positions
                    positions = [i + 1 for i, w in enumerate(word_order) if w == word]
                    row.append(", ".join(map(str, positions)) if positions else "")
                writer.writerow(row)
                trial_number += 1  # Increment trial number for each file

            # Clean up temporary folder
            shutil.rmtree(temp_folder)

    print(f"All subject data exported to {output_csv_path}")

def join_csv_files(silence_csv_path, music_csv_path, output_csv_path):
    """
    Joins two CSV files into a single CSV file.
    """
    with open(output_csv_path, mode="w", newline="") as output_file:
        writer = csv.writer(output_file)

        # Read and write the header from the first file
        with open(silence_csv_path, mode="r") as silence_file:
            reader = csv.reader(silence_file)
            header = next(reader)  # Extract the header row
            writer.writerow(header)  # Write the header to the output file

            # Write the rows from the silence file
            for row in reader:
                writer.writerow(row)

        # Read and write the rows from the second file (music file)
        with open(music_csv_path, mode="r") as music_file:
            reader = csv.reader(music_file)
            next(reader)  # Skip the header row
            for row in reader:
                writer.writerow(row)

    print(f"Joined CSV files into {output_csv_path}")

def export_to_excel_with_colors(input_path, output_path):
    # Define the column colors
    column_colors = {
        "drum": ("#FFCCCC", "#CC6666"),
        "curtain": ("#FFCCCC", "#CC6666"),
        "bell": ("#CCFFCC", "#66CC66"),
        "coffee": ("#CCFFCC", "#66CC66"),
        "school": ("#CCCCFF", "#6666CC"),
        "parent": ("#CCCCFF", "#6666CC"),
        "moon": ("#CCCCFF", "#6666CC"),
        "garden": ("#CCCCFF", "#6666CC"),
        "hat": ("#FFFFCC", "#CCCC66"),
        "farmer": ("#FFFFCC", "#CCCC66"),
        "nose": ("#FFFFCC", "#CCCC66"),
        "turkey": ("#FFFFCC", "#CCCC66"),
        "color": ("#FFCCFF", "#CC66CC"),
        "house": ("#FFCCFF", "#CC66CC"),
        "river": ("#CCCCCC", "#666666"),
    }

    # Read the CSV file
    df = pd.read_csv(input_path)

    # Create a new workbook
    wb = Workbook()
    ws = wb.active

    # Write the DataFrame to the worksheet
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        ws.append(row)

    # Apply the colors to the columns
    for col in df.columns:
        if col in column_colors:
            data_fill = PatternFill(start_color=column_colors[col][0][1:], 
                                  end_color=column_colors[col][0][1:], 
                                  fill_type="solid")
            header_fill = PatternFill(start_color=column_colors[col][1][1:], 
                                    end_color=column_colors[col][1][1:], 
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
    print(f"Styled Excel file saved to {output_path}")

def main():
    #folder_path = "//Users//maaymadar//Downloads//list1-mismatch11-6-25"
    base_path = "//Users//maaymadar//Downloads//2fromeach"
    silence_csv_path = os.path.join(base_path, "silence_results.csv")
    music_csv_path = os.path.join(base_path, "music_results.csv")
    output_csv_path = os.path.join(base_path, "full_data.csv")
    excel_path = os.path.join(base_path, "full_data_colored.xlsx")

    sil_folders = [os.path.join(base_path, folder) for folder in os.listdir(base_path) 
               if folder.startswith("sil") and os.path.isdir(os.path.join(base_path, folder))]
    mus_folders = [os.path.join(base_path, folder) for folder in os.listdir(base_path) 
                if folder.startswith("mus") and os.path.isdir(os.path.join(base_path, folder))]

    #handle_subjects(base_path, sil_folders, silence_csv_path)
    #handle_subjects(base_path, mus_folders, music_csv_path)

    #join_csv_files(silence_csv_path, music_csv_path, output_csv_path)

    export_to_excel_with_colors(output_csv_path, excel_path)

if __name__ == "__main__":
    main()