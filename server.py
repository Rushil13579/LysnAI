from flask import Flask, request, jsonify, Response, stream_with_context # type: ignore
import os
import tempfile
from analyseAudio import main as analyse_audio
import json
import threading
import uuid
import time

app = Flask(__name__, static_folder='.', static_url_path='')

# Dictionary to store analysis status for each session
analysis_status = {}

@app.route('/')
def index():
    return app.send_static_file('LysnAI.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio_file']
    job_role = request.form.get('job_role', '')
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Initialize status for this session
    analysis_status[session_id] = {
        'stage': 'starting',
        'result': None,
        'error': None,
        'complete': False
    }
    
    # Save the uploaded file to a temporary location
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_file_path = temp_file.name
    temp_file.close()
    
    try:
        audio_file.save(temp_file_path)
        
        # Define a callback function to update the analysis stage
        def progress_callback(stage):
            analysis_status[session_id]['stage'] = stage
            if stage == 'complete':
                analysis_status[session_id]['complete'] = True
        
        # Start analysis in a separate thread
        def process_audio():
            try:
                # Call the analyseAudio.py script with the progress callback
                result = analyse_audio(temp_file_path, job_role, progress_callback=progress_callback)
                
                # Store the result
                analysis_status[session_id]['result'] = result
            except Exception as e:
                analysis_status[session_id]['error'] = str(e)
                analysis_status[session_id]['complete'] = True
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # Start the processing thread
        threading.Thread(target=process_audio).start()
        
        # Return the session ID to the client
        return jsonify({'session_id': session_id})
    except Exception as e:
        # Clean up in case of error
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        return jsonify({'error': str(e)}), 500

@app.route('/analysis_status/<session_id>', methods=['GET'])
def get_analysis_status(session_id):
    if session_id not in analysis_status:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    status = analysis_status[session_id]
    
    # If there was an error, return it
    if status['error']:
        return jsonify({
            'stage': 'error',
            'error': status['error']
        })
    
    # If complete, return the result
    if status['complete']:
        result = status['result']
        # Clean up after some time (in a production app, you'd want a better cleanup strategy)
        def cleanup():
            time.sleep(300)  # Keep the result for 5 minutes
            if session_id in analysis_status:
                del analysis_status[session_id]
        
        threading.Thread(target=cleanup).start()
        
        return jsonify({
            'stage': 'complete',
            'result': result
        })
    
    # Otherwise, return the current stage
    return jsonify({
        'stage': status['stage']
    })

@app.route('/analysis_stream/<session_id>')
def analysis_stream(session_id):
    """Stream updates about the analysis status using Server-Sent Events."""
    if session_id not in analysis_status:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    def generate():
        last_stage = None
        
        while session_id in analysis_status:
            status = analysis_status[session_id]
            current_stage = status['stage']
            
            # Only send an update if the stage has changed
            if current_stage != last_stage:
                if status['error']:
                    yield f"data: {json.dumps({'stage': 'error', 'error': status['error']})}\n\n"
                    break
                
                if status['complete']:
                    yield f"data: {json.dumps({'stage': 'complete', 'result': status['result']})}\n\n"
                    break
                
                yield f"data: {json.dumps({'stage': current_stage})}\n\n"
                last_stage = current_stage
            
            time.sleep(0.5)  # Check for updates every 0.5 seconds
    
    return Response(stream_with_context(generate()), 
                   mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                            'Connection': 'keep-alive'})

@app.route('/export_to_sheets', methods=['POST'])
def export_to_sheets():
    try:
        # Get the analysis result and sheets_id from the request
        data = request.json
        if not data or 'analysis_result' not in data:
            return jsonify({'error': 'No analysis result provided'}), 400
        
        analysis_result = data['analysis_result']
        
        # Get the sheets_id from the request, or use the default if not provided
        sheets_id = data.get('sheets_id', '1lLk7GQvzz0G_j48M2IrVVQ_-USVYPRPERLjOfNIc_H4')
        
        # If sheets_id is empty, use the default
        if not sheets_id.strip():
            sheets_id = '1lLk7GQvzz0G_j48M2IrVVQ_-USVYPRPERLjOfNIc_H4'
        
        # Import the postToSheets module and call its main function
        from postToSheets import main as post_to_sheets_main
        
        # Call the main function with the analysis result and sheets_id
        result = post_to_sheets_main(analysis_result, sheets_id)
        
        return jsonify({'success': True, 'message': 'Data successfully exported to Google Sheets'})
    except Exception as e:
        print(f"Error exporting to sheets: {str(e)}")
        return jsonify({'error': f'Failed to export to Google Sheets. Please check your Google Sheet URL: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 