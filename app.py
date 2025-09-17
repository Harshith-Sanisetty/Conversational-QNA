from flask import Flask, render_template, request, jsonify, session
from chat_bot import ConversationalBot
from config import Config
import os

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
bot = ConversationalBot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    d = request.get_json()
    uname = d.get('uname', 'User')
    sid, greet = bot.start_conversation(uname)
    session['sid'] = sid
    session['uname'] = uname
    return jsonify({'ok': True, 'sid': sid, 'msg': greet})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        d = request.get_json()
        msg = d.get('msg', '').strip()
        if not msg:
            return jsonify({'ok': False, 'err': 'Empty message'})
        
        sid = session.get('sid')
        if not sid:
            return jsonify({'ok': False, 'err': 'No active session'})

        if msg.lower().startswith('/search '):
            q = msg[8:]
            resp = bot.search_past_conversations(sid, q)
            return jsonify({'ok': True, 'msg': resp, 'type': 'search'})
        
        elif msg.lower() == '/summary':
            resp = bot.get_conversation_summary(sid)
            return jsonify({'ok': True, 'msg': resp, 'type': 'summary'})

        resp, an = bot.generate_response(msg, sid)
        return jsonify({
            'ok': True,
            'msg': resp,
            'an': {
                'topic': an['topic'],
                'mood': an['sentiment'],
                'kws': an['keywords'],
                'score': an['context_score']
            }
        })
    except Exception as e:
        return jsonify({'ok': False, 'err': str(e)})

@app.route('/info', methods=['GET'])
def info():
    sid = session.get('sid')
    uname = session.get('uname', 'User')
    if not sid:
        return jsonify({'ok': False, 'err': 'No active session'})
    
    summ = bot.get_conversation_summary(sid)
    return jsonify({
        'ok': True, 
        'sid': sid, 
        'uname': uname, 
        'summ': summ
    })

@app.route('/clear', methods=['POST'])
def clear():
    session.clear()
    return jsonify({'ok': True, 'msg': 'Session cleared'})

@app.errorhandler(404)
def err404(e):
    return jsonify({'ok': False, 'err': 'Endpoint not found'}), 404

@app.errorhandler(500)
def err500(e):
    return jsonify({'ok': False, 'err': 'Internal server error'}), 500

if __name__ == '__main__':
    os.makedirs('database', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print(f"Starting {Config.BOT_NAME}...")
    print(f"URL: http://localhost:{Config.PORT}")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )