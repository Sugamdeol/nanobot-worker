import os
import io
import base64
import json
import requests
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import PyPDF2
from PIL import Image

app = Flask(__name__)

# Environment variables
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
POLLINATIONS_API_KEY = os.environ.get('POLLINATIONS_API_KEY')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'nanobot-worker'}), 200

@app.route('/solve-pdf', methods=['POST'])
def solve_pdf():
    if not GEMINI_API_KEY:
        return jsonify({'error': 'GEMINI_API_KEY not configured'}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No PDF file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Read PDF in memory-efficient way
        pdf_stream = io.BytesIO(file.read())
        reader = PyPDF2.PdfReader(pdf_stream)
        
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        
        pdf_stream.close()
        
        # Call Gemini API
        gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}'
        
        payload = {
            'contents': [{
                'parts': [{
                    'text': f'Solve these JEE questions. Provide step-by-step solutions with final answers:\n\n{text}'
                }]
            }]
        }
        
        response = requests.post(gemini_url, json=payload, timeout=60)
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            solution = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({'solution': solution, 'status': 'success'}), 200
        else:
            return jsonify({'error': 'Failed to get solution from Gemini'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/screenshot', methods=['POST'])
def capture_screenshot():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL not provided'}), 400
        
        url = data['url']
        width = data.get('width', 1280)
        height = data.get('height', 720)
        full_page = data.get('full_page', False)
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': width, 'height': height})
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            if full_page:
                screenshot = page.screenshot(full_page=True)
            else:
                screenshot = page.screenshot()
            
            browser.close()
        
        # Convert to base64
        img_base64 = base64.b64encode(screenshot).decode('utf-8')
        
        return jsonify({
            'screenshot': img_base64,
            'format': 'png',
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image():
    if not POLLINATIONS_API_KEY:
        return jsonify({'error': 'POLLINATIONS_API_KEY not configured'}), 500
    
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Prompt not provided'}), 400
        
        prompt = data['prompt']
        width = data.get('width', 1024)
        height = data.get('height', 1024)
        seed = data.get('seed', 42)
        
        # Call Pollinations AI API
        pollinations_url = f'https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width={width}&height={height}&seed={seed}&nologo=true'
        
        headers = {}
        if POLLINATIONS_API_KEY:
            headers['Authorization'] = f'Bearer {POLLINATIONS_API_KEY}'
        
        response = requests.get(pollinations_url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            img_base64 = base64.b64encode(response.content).decode('utf-8')
            return jsonify({
                'image': img_base64,
                'format': 'png',
                'status': 'success'
            }), 200
        else:
            return jsonify({'error': f'Image generation failed: {response.status_code}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/voiceover', methods=['POST'])
def generate_voiceover():
    if not POLLINATIONS_API_KEY:
        return jsonify({'error': 'POLLINATIONS_API_KEY not configured'}), 500
    
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text not provided'}), 400
        
        text = data['text']
        voice = data.get('voice', 'alloy')
        
        # Call Pollinations TTS API
        pollinations_url = f'https://text.pollinations.ai/{requests.utils.quote(text)}?voice={voice}'
        
        headers = {}
        if POLLINATIONS_API_KEY:
            headers['Authorization'] = f'Bearer {POLLINATIONS_API_KEY}'
        
        response = requests.get(pollinations_url, headers=headers, timeout=60)
        
        if response.status_code == 200:
            audio_base64 = base64.b64encode(response.content).decode('utf-8')
            return jsonify({
                'audio': audio_base64,
                'format': 'mp3',
                'status': 'success'
            }), 200
        else:
            return jsonify({'error': f'Voice generation failed: {response.status_code}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
