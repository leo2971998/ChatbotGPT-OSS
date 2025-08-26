from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama',
)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    try:
        response = client.chat.completions.create(
            model='gpt-oss:20b',
            messages=[{'role': 'user', 'content': user_message}],
        )
        return jsonify({'reply': response.choices[0].message['content']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
