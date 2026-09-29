from flask import Flask, render_template, request, jsonify
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text')
    src_lang = data.get('src') # 'hi', 'ta', or 'ml'
    
    # Translate to English
    translated = translator.translate(text, src=src_lang, dest='en')
    return jsonify({'translated_text': translated.text})

if __name__ == '__main__':
    app.run(debug=True)