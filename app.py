from flask import Flask, render_template, request, redirect, url_for
import os
import pypdf
import google.generativeai as genai
import json
import re # Import the regular expression module

app = Flask(__name__)

# Configure the Gemini API with your key
GEMINI_API_KEY = "AIzaSyBBJpcCMBiV4CrIhLew_w2_6ZkdWPR3ZSE"
genai.configure(api_key=GEMINI_API_KEY)

# In-memory storage for quiz data (for simplicity, replace with a database in a real application)
quiz_data_storage = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdfFile' not in request.files or request.files['pdfFile'].filename == '':
        return render_template('info.html', message='❗ Please select a PDF file before creating a quiz!')
    file = request.files['pdfFile']
    filepath = file.filename
    file.save(filepath)
    pdf_text = ""
    try:
        with open(filepath, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                pdf_text += page.extract_text()
    except Exception as e:
        os.remove(filepath)
        return render_template('info.html', message=f'❗ Error reading PDF: {e}')
    os.remove(filepath)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Extract multiple choice questions from the following text:\n\n{pdf_text}\n\nFormat the output as a JSON array of objects, where each object has 'question', 'options' (an array of strings), and 'answer' (the correct option string). If no MCQs are found, return an empty JSON array. Ensure the output is valid JSON and nothing else."
        response = model.generate_content(prompt)
        json_match = re.search(r'```json\n(.*?)```', response.text, re.DOTALL)
        json_string = response.text
        if json_match:
            json_string = json_match.group(1)
        try:
            quiz_data = json.loads(json_string)
            if not quiz_data:
                return render_template('info.html', message='😕 The uploaded PDF does not contain any MCQ questions.')
            quiz_id = "quiz_1"
            quiz_data_storage[quiz_id] = quiz_data
            return redirect(url_for('start_quiz', quiz_id=quiz_id))
        except json.JSONDecodeError:
            try:
                quiz_data = json.loads(response.text)
                if not quiz_data:
                    return render_template('info.html', message='😕 The uploaded PDF does not contain any MCQ questions.')
                quiz_id = "quiz_1"
                quiz_data_storage[quiz_id] = quiz_data
                return redirect(url_for('start_quiz', quiz_id=quiz_id))
            except json.JSONDecodeError:
                return render_template('info.html', message='❗ Error parsing Gemini API response as JSON.')
        except Exception as e:
            return render_template('info.html', message=f'❗ An error occurred while processing the API response: {e}')
    except Exception as e:
        return render_template('info.html', message=f'❗ Error communicating with Gemini API: {e}')

@app.route('/quiz/<quiz_id>')
def start_quiz(quiz_id):
    if quiz_id in quiz_data_storage:
        quiz_data = quiz_data_storage[quiz_id]
        return render_template('quiz.html', quiz_data=quiz_data)
    else:
        return render_template('info.html', message='❗ Quiz not found.')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', debug=True) 