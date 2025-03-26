import gspread # type: ignore
from google.oauth2.service_account import Credentials # type: ignore
from datetime import datetime

# Define the scope for the Google Sheets API
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

# Use the service account credentials (make sure credentials.json is in the same directory)
SERVICE_ACCOUNT_FILE = '/Users/rushiljhaveri/Desktop/Coding/AIAgents/LysnAI/resources/credentials.json'
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
client = gspread.authorize(creds)

def post_to_sheets(analysis_result: dict, sheet_id: str):
    """
    Posts interview data to Google Sheets.
    
    Args:
        analysis_result (dict): Dictionary containing interview data.
        sheet_id (str): ID of the Google Sheet.
    """
    # Open the Google Sheet by its key (ID)
    sheet = client.open_by_key(sheet_id).sheet1

    # Prepare the row data in the order corresponding to your Google Sheet columns:
    # Column A: timestamp, Column B: interviewer_name, etc.
    row = [
        datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        analysis_result["export_data"]["interviewer_name"],
        analysis_result["export_data"]["candidate_name"],
        analysis_result["export_data"]["job_role"],
        analysis_result["export_data"]["work_experience"],
        analysis_result["export_data"]["salary_expectations"],
        analysis_result["short_summary"]
    ]
    
    # Append the row to the sheet (this adds a new row at the bottom)
    sheet.append_row(row)
    return True

def main(analysis_result: dict, sheet_id: str="1lLk7GQvzz0G_j48M2IrVVQ_-USVYPRPERLjOfNIc_H4"): # HARDCODED IDK WHY COS IM BORED
    return post_to_sheets(analysis_result, sheet_id)
