from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
import os
from werkzeug.utils import secure_filename
from XML_to_CSV_Converter import convert_bpmn_to_csv
from send_to_chatgpt import send_csv_to_chatgpt
import tempfile  # For creating a temporary directory
import shutil  # For deleting the folder

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a random secret key

# Define separate folders for CSVs and ChatGPT responses
CSV_FOLDER = 'generated_csvs'
RESPONSE_FOLDER = 'chatgpt_responses'
app.config['CSV_FOLDER'] = CSV_FOLDER
app.config['RESPONSE_FOLDER'] = RESPONSE_FOLDER

# Ensure the folders exist
os.makedirs(CSV_FOLDER, exist_ok=True)
os.makedirs(RESPONSE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    input_file = request.files['input_file']
    output_filename = request.form['output_file']

    if input_file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)

    if not output_filename:
        flash('Please specify an output file name.', 'error')
        return redirect(url_for('index'))

    try:
        # Save the output file in the uploads folder
        output_path = Path(app.config['CSV_FOLDER']) / secure_filename(output_filename)
        # Process the input file directly from memory
        convert_bpmn_to_csv(input_file, output_path)
        flash(f'Conversion completed. CSV saved to {output_path}', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')

    return redirect(url_for('index'))

@app.route('/send_to_chatgpt', methods=['POST'])
def send_to_chatgpt_route():
    csv_file = request.files['csv_file']
    output_txt_filename = request.form['output_txt_file']

    if csv_file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)

    if not output_txt_filename:
        flash('Please specify an output file name.', 'error')
        return redirect(url_for('index'))

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            csv_filename = secure_filename(csv_file.filename)
            csv_path = temp_dir_path / csv_filename
            csv_file.save(csv_path)
        
        # Call the send_csv_to_chatgpt function directly
            analysis = send_csv_to_chatgpt(csv_path)

            if analysis:
                # Save the analysis to a text file
                output_path = Path(app.config['RESPONSE_FOLDER']) / secure_filename(output_txt_filename)
                with open(output_path, 'w') as f:
                    f.write(analysis)
            
                flash(f'ChatGPT API Response saved as {output_txt_filename}', 'success')
            else:
                flash('Failed to get a response from ChatGPT.', 'error')

    except Exception as e:
        flash(f'An error occurred: {e}', 'error')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context=('/app/cert.pem', '/app/key.pem'))
