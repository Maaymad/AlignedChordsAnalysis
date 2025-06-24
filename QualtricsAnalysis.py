from moviepy import AudioFileClip
import json
import wave
import vosk
import os
import csv
import shutil
import pandas as pd
from pydub import AudioSegment
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

MODEL_PATH = "//Users//maaymadar//Downloads//vosk-model-small-en-us-0.15"  # Update this path to your downloaded model
model = vosk.Model(MODEL_PATH)

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
def convert_audio_to_wav(file):
    """Convert audio file to WAV format with correct sample rate for Vosk (16kHz mono, 16-bit PCM)"""
    if file.endswith(".wav"):
        # Check if WAV file has correct sample rate (16kHz mono, 16-bit PCM)
        try:
            with wave.open(file, 'rb') as wf:
                if wf.getframerate() == 16000 and wf.getnchannels() == 1 and wf.getsampwidth() == 2:
                    return file
                else:
                    # Convert to correct format (16kHz mono, 16-bit PCM)
                    output_file = file.replace(".wav", "_converted.wav")
                    audio = AudioSegment.from_wav(file)
                    audio = audio.set_frame_rate(16000).set_channels(1)  # Set sample rate to 16kHz and convert to mono
                    audio.export(output_file, format="wav", parameters=["-acodec", "pcm_s16le"])  # Export as 16-bit PCM
                    return output_file
        except Exception as e:
            print(f"Error checking WAV file {file}: {e}")
            return None

    elif file.endswith(".webm"):
        output_file = file.replace(".webm", ".wav")
        audio = AudioSegment.from_file(file, format="webm")
        # Convert to mono and set sample rate to 16kHz
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_file, format="wav", parameters=["-acodec", "pcm_s16le"])  # Export as 16-bit PCM
        return output_file

    elif file.endswith(".mp3"):
        output_file = file.replace(".mp3", ".wav")
        audio = AudioSegment.from_file(file, format="mp3")
        # Convert to mono and set sample rate to 16kHz
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_file, format="wav", parameters=["-acodec", "pcm_s16le"])  # Export as 16-bit PCM
        return output_file

    elif file.endswith(".m4a"):
        output_file = file.replace(".m4a", ".wav")
        audio = AudioSegment.from_file(file, format="m4a")
        # Convert to mono and set sample rate to 16kHz
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_file, format="wav", parameters=["-acodec", "pcm_s16le"])  # Export as 16-bit PCM
        return output_file

    else:
        print("Unsupported file type")
        return None

def transcribe_audio_vosk(file_path):
    """
    Transcribes an audio file using Vosk.
    Filters the transcript to include only target words and their order.
    """
    #converted_path = convert_audio_to_wav(file_path)
    print(f"Transcribing {file_path}...")
    
    try:
        if file_path is None:
            raise ValueError("File conversion failed or unsupported file type.")

        # Open the WAV file
        wf = wave.open(file_path, 'rb')
        
        # Check if the file is in the correct format
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError(f"Audio file must be 16kHz mono PCM. Got: channels={wf.getnchannels()}, "
                           f"sampwidth={wf.getsampwidth()}, framerate={wf.getframerate()}")

        # Initialize recognizer
        rec = vosk.KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        
        transcript_words = []
        
        # Process audio in chunks
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if 'text' in result:
                    words = result['text'].lower().split()
                    transcript_words.extend(words)
        
        # Get final result
        final_result = json.loads(rec.FinalResult())
        if 'text' in final_result:
            words = final_result['text'].lower().split()
            transcript_words.extend(words)
        
        wf.close()
        
        # Filter and map the transcript to target words
        word_order = [word for word in transcript_words if word in TARGET_WORDS]
        return word_order

    except Exception as e:
        print(f"Error transcribing {file_path}: {e}")
        return []

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
        converted_file = convert_audio_to_wav(file_path)
        if converted_file:
            try:
                word_order = transcribe_audio_vosk(converted_file)
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

def get_expected_trials(condition):
    """
    Returns the list of expected trial patterns based on the condition.
    """
    if condition == "music":
        return ["mus1_1", "mus1_2", "mus1_3", "mus1_4", "mus1_5", "mus2_1", "mus2_2", "mus2_3"]
    elif condition == "silence":
        return ["sil1_1", "sil1_2", "sil1_3", "sil1_4", "sil1_5", "sil2_1", "sil2_2", "sil2_3"]
    else:
        raise ValueError(f"Unknown condition: {condition}")

def collect_subject_files(subject_id, subject_index, folders, expected_trials, temp_folder):
    """
    Collects and copies files for a specific subject from all folders.
    Returns a dictionary mapping trial patterns to copied file names.
    """
    found_files = {}
    
    for folder in folders:
        folder_name = os.path.basename(folder)  # e.g., "mus1_1", "sil2_3", etc.
        for file_name in os.listdir(folder):
            if file_name.startswith("R_") and "_" in file_name:
                file_id = file_name.split("_")[1]
                if file_id == subject_id and folder_name in expected_trials:
                    source_path = os.path.join(folder, file_name)
                    new_file_name = f"sub{subject_index}_{folder_name}.webm"
                    destination_path = os.path.join(temp_folder, new_file_name)
                    shutil.copy(source_path, destination_path)
                    found_files[folder_name] = new_file_name
    
    return found_files

def create_trial_row(subject_index, trial_number, expected_trial, found_files, results, condition):
    """
    Creates a CSV row for a single trial, handling both found and missing trials.
    """
    file_name_no_ext = f"sub{subject_index}_{expected_trial}"
    
    if expected_trial in found_files and found_files[expected_trial] in results:
        # File was found and processed successfully
        word_order = results[found_files[expected_trial]]
        unique_word_count = len(set(word_order))
        row = [file_name_no_ext, trial_number, unique_word_count, condition]
        
        # Add word positions
        for word in TARGET_WORDS:
            positions = [i + 1 for i, w in enumerate(word_order) if w == word]
            row.append(", ".join(map(str, positions)) if positions else "")
    else:
        # File was missing or failed to process
        row = [file_name_no_ext, trial_number, "NA", condition]
        # Add empty strings for all target words
        for word in TARGET_WORDS:
            row.append("")
    
    return row

def process_single_subject(subject_id, subject_index, folders, expected_trials, base_path, condition):
    """
    Processes all trials for a single subject and returns the rows for CSV writing.
    """
    temp_folder = os.path.join(base_path, "temp_subject")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
    
    try:
        # Collect files for this subject
        found_files = collect_subject_files(subject_id, subject_index, folders, expected_trials, temp_folder)
        
        # Process the files that were found
        results = process_folder(temp_folder) if found_files else {}
        
        # Create rows for all expected trials
        rows = []
        for trial_number, expected_trial in enumerate(expected_trials, start=1):
            row = create_trial_row(subject_index, trial_number, expected_trial, found_files, results, condition)
            rows.append(row)
        
        return rows
    
    finally:
        # Always clean up temporary folder
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

def determine_condition_from_folders(folders):
    """
    Determines the condition (music or silence) based on folder names.
    """
    folder_names = [os.path.basename(folder) for folder in folders]
    
    # Check if any folder starts with "mus"
    if any(name.startswith("mus") for name in folder_names):
        return "music"
    # Check if any folder starts with "sil"
    elif any(name.startswith("sil") for name in folder_names):
        return "silence"
    else:
        raise ValueError(f"Cannot determine condition from folder names: {folder_names}")

def handle_subjects(base_path, folders, output_csv_path, condition=None):
    """
    Processes all subjects and exports their data into a single CSV file.
    Ensures all 8 expected trials are present, marking missing ones as NA.
    """
    # Determine condition if not provided
    if condition is None:
        condition = determine_condition_from_folders(folders)
        print(f"Detected condition: {condition}")

    # Extract all subject IDs from the folders
    all_subject_ids = set()
    for folder in folders:
        all_subject_ids.update(extract_subject_ids(folder))

    print(f"Found {len(all_subject_ids)} unique subject IDs.")

    # Get expected trial patterns for this condition
    expected_trials = get_expected_trials(condition)

    # Prepare to write to a single CSV file
    with open(output_csv_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        # Write header row
        writer.writerow(["File Name", "Trial Number", "Word Count", "Condition"] + TARGET_WORDS)

        # Process each subject ID individually
        for subject_index, subject_id in enumerate(sorted(all_subject_ids), start=1):
            rows = process_single_subject(subject_id, subject_index, folders, expected_trials, base_path, condition)
            
            # Write all rows for this subject
            for row in rows:
                writer.writerow(row)

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

    handle_subjects(base_path, sil_folders, silence_csv_path)
    handle_subjects(base_path, mus_folders, music_csv_path)

    join_csv_files(silence_csv_path, music_csv_path, output_csv_path)

    export_to_excel_with_colors(output_csv_path, excel_path)

if __name__ == "__main__":
    main()