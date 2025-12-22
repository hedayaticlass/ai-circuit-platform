from flask import Flask, render_template, request, jsonify, send_from_directory
from api_client import analyze_text, transcribe_audio
from drawer import render_schematic
import os
import base64
import json
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key' # Replace with a strong, random key in production
SCHEM_PATH = "schematic.png"
SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Helper to save/load chat sessions
def _get_session_file_path(session_id):
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")

def _load_session(session_id):
    path = _get_session_file_path(session_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"messages": [], "displayName": "چت جدید", "lastMessage": time.time()}

def _save_session(session_id, session_data):
    path = _get_session_file_path(session_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/chat/message', methods=['POST'])
def handle_chat_message():
    data = request.json
    user_message = data.get('message')
    session_id = data.get('sessionId', 'default')
    llm_base_url = data.get('llmBaseUrl')
    llm_model = data.get('llmModel')
    llm_api_key = data.get('llmApiKey')

    session_data = _load_session(session_id)
    session_data['messages'].append({"role": "user", "content": user_message})
    session_data['lastMessage'] = time.time()

    if session_id == 'default' and not session_data.get('displayName'):
        session_data['displayName'] = user_message[:30] + '...' if len(user_message) > 30 else user_message
    
    try:
        # Call the existing backend logic
        out = analyze_text(user_message, llm_base_url, llm_model, llm_api_key)
        spice_code = out.get("spice", "")
        components = out.get("components", [])

        image_base64 = None
        if components:
            try:
                img_path = render_schematic(components, save_path=SCHEM_PATH)
                with open(img_path, "rb") as f:
                    image_base64 = "data:image/png;base64," + base64.b64encode(f.read()).decode('utf-8')
                os.remove(img_path)  # Clean up the generated image file
            except Exception as e:
                print(f"Error generating schematic: {e}")

        assistant_response_content = {
            "modelOutput": out.get("model_output"),  # Assuming model_output might be a key from analyze_text
            "pythonCode": spice_code,  # Using spice as pythonCode
            "spiceCode": spice_code,
            "components": components,
            "imageBase64": image_base64
        }

        session_data['messages'].append({"role": "assistant", "content": assistant_response_content})
        _save_session(session_id, session_data)

        return jsonify({"message": assistant_response_content})

    except Exception as e:
        error_message = f"Error: {e}"
        session_data['messages'].append({"role": "assistant", "content": {"modelOutput": error_message}})
        _save_session(session_id, session_data)
        return jsonify({"error": error_message}), 500

@app.route('/api/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    session_data = _load_session(session_id)
    return jsonify(session_data)

@app.route('/api/chat/history/<session_id>', methods=['DELETE'])
def delete_chat_history(session_id):
    if session_id == 'default':
        # Clear messages for default session instead of deleting the file
        session_data = _load_session(session_id)
        session_data['messages'] = []
        session_data['displayName'] = 'چت جدید'
        session_data['lastMessage'] = time.time()
        _save_session(session_id, session_data)
        return jsonify({"success": True, "message": "Default chat history cleared."})

    session_file = _get_session_file_path(session_id)
    if os.path.exists(session_file):
        os.remove(session_file)
        return jsonify({"success": True, "message": "Session deleted."})
    return jsonify({"success": False, "message": "Session not found."}), 404

@app.route('/api/chat/history/<session_id>/rename', methods=['PUT'])
def rename_chat_session(session_id):
    data = request.json
    new_name = data.get('name')
    if not new_name:
        return jsonify({"success": False, "error": "New name is required."}), 400

    session_data = _load_session(session_id)
    if session_data:
        session_data['displayName'] = new_name
        _save_session(session_id, session_data)
        return jsonify({"success": True, "displayName": new_name})
    return jsonify({"success": False, "message": "Session not found."}), 404

@app.route('/api/chat/sessions', methods=['GET'])
def list_chat_sessions():
    sessions = []
    for filename in os.listdir(SESSIONS_DIR):
        if filename.endswith('.json'):
            session_id = os.path.splitext(filename)[0]
            session_data = _load_session(session_id)
            sessions.append({
                "sessionId": session_id,
                "displayName": session_data.get('displayName', session_id),
                "lastMessage": session_data.get('lastMessage', 0),
                "lastMessageType": session_data['messages'][-1]['role'] if session_data['messages'] else None
            })
    sessions.sort(key=lambda x: x['lastMessage'], reverse=True)
    return jsonify({"sessions": sessions})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)