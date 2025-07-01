from flask import Flask, jsonify, request
from flask_cors import CORS
import json, os
from datetime import datetime
import pytz
import requests

app = Flask(__name__)
CORS(app)

TRIVIA_FILE = 'trivia_store.json'
SUBMIT_FILE = 'submissions.json'
CST = pytz.timezone('America/Chicago')

def get_today_date():
    return datetime.now(CST).strftime('%Y-%m-%d')

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, 'r') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def fetch_daily_questions():
    trivia_data = load_json(TRIVIA_FILE)
    today = get_today_date()

    if today not in trivia_data:
        response = requests.get('https://opentdb.com/api.php?amount=10&type=multiple&difficulty=easy,medium')
        if response.status_code == 200:
            trivia_data[today] = response.json().get('results', [])
            save_json(TRIVIA_FILE, trivia_data)

    return trivia_data[today]

@app.route('/daily-questions/<username>', methods=['GET'])
def get_questions(username):
    today = get_today_date()
    submissions = load_json(SUBMIT_FILE)

    if username in submissions.get(today, []):
        return jsonify({'error': 'You have already played today.'}), 403

    questions = fetch_daily_questions()
    return jsonify({'date': today, 'questions': questions})

@app.route('/submit-score', methods=['POST'])
def submit_score():
    today = get_today_date()
    data = request.get_json()
    username = data.get('username')
    score = data.get('score')

    if not username or not isinstance(score, int):
        return jsonify({'error': 'Username and numeric score are required.'}), 400

    submissions = load_json(SUBMIT_FILE)
    if today not in submissions:
        submissions[today] = []

    if username in submissions[today]:
        return jsonify({'error': 'Already submitted today.'}), 403

    submissions[today].append(username)
    save_json(SUBMIT_FILE, submissions)

    return jsonify({'message': 'Score recorded successfully.'})

@app.route('/check-username/<username>', methods=['GET'])
def check_username(username):
    today = get_today_date()
    submissions = load_json(SUBMIT_FILE)
    used_today = username in submissions.get(today, [])
    return jsonify({'available': not used_today})

@app.route('/')
def home():
    return 'Trivia Flask server is running!'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
