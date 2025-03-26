import whisper # type: ignore
from google import genai
from google.genai import types # type: ignore
from openai import OpenAI # type: ignore
import argparse
from datetime import datetime
import os
import json
from typing import Callable, Optional, Dict, Any

# Load API keys from keys.json file
def load_api_keys():
    keys_path = "/Users/rushiljhaveri/Desktop/Coding/keys.json"
    try:
        with open(keys_path, 'r') as f:
            keys = json.load(f)
            return keys.get("OPENAI_API_KEY"), keys.get("GEMINI_API_KEY")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading API keys: {e}")
        return None, None

# Set API keys
OPENAI_API_KEY, GEMINI_API_KEY = load_api_keys()
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY if OPENAI_API_KEY else ""

def transcribe(audio_path: str, model_size: str) -> str:
    """
    Transcribes and translates the given audio file to English using Whisper.
    Returns the full transcription as a single paragraph without timestamps.
    
    Parameters:
      audio_path (str): Path to the audio file.
      model_size (str): Size of the Whisper model (default "base").
      
    Returns:
      str: The full transcription text.
    """

    # LOCAL MODEL
    # Load the Whisper model
    model = whisper.load_model(model_size)
    
    # Transcribe using the 'translate' task so that non-English content is translated to English.
    result = model.transcribe(audio_path, task="translate")
    return result["text"]

    # API MODEL
    #client = OpenAI()

    #audio_file = open(audio_path, "rb")
    #transcription = client.audio.translations.create(
    #   model="whisper-1", 
    #    file=audio_file,
    #    response_format="text"
    #)
    
    #return transcription

def analyze_text(text: str, job_role: str) -> str:
    """
    Sends the transcribed text to the Gemini 2.0 Flash thinking model for analysis using the
    Google Generative Language API.
    
    Parameters:
      text (str): The text to analyze.
      job_role (str): The job role context for the analysis.
    
    Returns:
      str: The output text from the API.
    """
    # Create a client object with your API key.
    # Replace 'GEMINI_API_KEY' with your actual key.
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Refining the transcript for increased accuracy
    # Read the prompt template from a file
    with open("/Users/rushiljhaveri/Desktop/Coding/AIAgents/LysnAI/resources/system_prompt.txt", "r") as file:
        system_prompt = file.read().strip()
    
    # Without system prompt
    # Combine the template with the transcribed text
    # prompt = system_prompt + text

    #response = client.models.generate_content(
    #  model="gemini-2.0-flash-thinking-exp",
    #  contents=[prompt]
    #)

    # With system prompt
    prompt = "Job Role: " + job_role + "\nTranscription: " + text

    response = client.models.generate_content(
        model="gemini-2.0-flash-thinking-exp",
        config=types.GenerateContentConfig(
        system_instruction=system_prompt),
        contents=[prompt]
    )
    
    # Extract and return only the output from the response.
    output = response.text
    #print("=== Analysis Output ===")
    #print(output)
    return output

def main(audio_path: str, job_role: str = "", model_size: str = "base", progress_callback: Optional[Callable[[str], None]] = None) -> str:
    """
    Process an audio file by transcribing it and then analyzing the transcription.
    
    Parameters:
      audio_path (str): Path to the audio file.
      job_role (str): Job role context for the analysis.
      model_size (str): Size of the Whisper model.
      progress_callback (Callable): Optional callback function to report progress.
      
    Returns:
      str: The analysis output.
    """
    # Step 1: Transcribe the audio file using Whisper.
    if progress_callback:
        progress_callback("transcribing")
    
    transcription = transcribe(audio_path, model_size)
    
    # Step 2: Analyze the transcription using Gemini.
    if progress_callback:
        progress_callback("analyzing")
    
    analysis_result = analyze_text(transcription, job_role)
    
    if progress_callback:
        progress_callback("complete")

    return analysis_result

#if __name__ == "__main__":
    #parser = argparse.ArgumentParser(description="Transcribe and Analyze an audio file.")
    #parser.add_argument('--audio', type=str, help='Path to the audio file', default="/Users/rushiljhaveri/Desktop/Coding/AIAgents/LysnAI/resources/Interview.mp3")
    #args = parser.parse_args()
    
    #main(args.audio)