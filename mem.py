import sqlite3
import uuid
from datetime import datetime, timedelta
from config import Config
import os

class Mem:
    def __init__(self):
        self.db = Config.DB_PATH
        self.setup()

    def setup(self):
        os.makedirs(os.path.dirname(self.db), exist_ok=True)
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY, session_id TEXT, u_msg TEXT, 
                b_rep TEXT, ts DATETIME, topic TEXT, mood TEXT, 
                kws TEXT, score REAL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                sid TEXT PRIMARY KEY, created_at DATETIME, last_active DATETIME, 
                uname TEXT, total_msgs INTEGER DEFAULT 0
            )
        ''')
        con.commit()
        con.close()

    def new_sess(self, uname="User"):
        sid = str(uuid.uuid4())
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        now = datetime.now()
        cur.execute('''
            INSERT INTO sessions (sid, created_at, last_active, uname) 
            VALUES (?, ?, ?, ?)
        ''', (sid, now, now, uname))
        con.commit()
        con.close()
        return sid

    def save(self, sid, u_msg, b_rep, topic="general", mood="neutral", kws="", score=0.0):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cid = str(uuid.uuid4())
        now = datetime.now()
        cur.execute('''
            INSERT INTO chats (id, session_id, u_msg, b_rep, ts, topic, mood, kws, score) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cid, sid, u_msg, b_rep, now, topic, mood, kws, score))
        cur.execute('''
            UPDATE sessions SET last_active = ?, total_msgs = total_msgs + 1 
            WHERE sid = ?
        ''', (now, sid))
        con.commit()
        con.close()

    def recent(self, sid, lim=5):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cur.execute('''
            SELECT u_msg, b_rep, topic, mood, ts FROM chats 
            WHERE session_id = ? ORDER BY ts DESC LIMIT ?
        ''', (sid, lim))
        res = cur.fetchall()
        con.close()
        return [{'u': r[0], 'b': r[1], 'topic': r[2], 'mood': r[3], 'time': r[4]} for r in res]

    def find(self, sid, kws, lim=3):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        term = f"%{kws[0]}%" if kws else "%"
        cur.execute('''
            SELECT u_msg, b_rep, topic, ts, score FROM chats 
            WHERE session_id = ? AND (u_msg LIKE ? OR b_rep LIKE ? OR kws LIKE ? OR topic LIKE ?) 
            ORDER BY score DESC, ts DESC LIMIT ?
        ''', (sid, term, term, term, term, lim))
        res = cur.fetchall()
        con.close()
        return [{'u': r[0], 'b': r[1], 'topic': r[2], 'time': r[3], 'score': r[4]} for r in res]

    def stats(self, sid):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cur.execute('SELECT * FROM sessions WHERE sid = ?', (sid,))
        sess = cur.fetchone()
        cur.execute('''
            SELECT topic, COUNT(*) as count FROM chats 
            WHERE session_id = ? GROUP BY topic ORDER BY count DESC
        ''', (sid,))
        topics = cur.fetchall()
        con.close()
        return {'sess': sess, 'topics': topics}

    def cleanup(self, days=30):
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        cut = datetime.now() - timedelta(days=days)
        cur.execute('SELECT sid FROM sessions WHERE last_active < ?', (cut,))
        old = cur.fetchall()
        for sess in old:
            cur.execute('DELETE FROM chats WHERE session_id = ?', (sess[0],))
        cur.execute('DELETE FROM sessions WHERE last_active < ?', (cut,))
        con.commit()
        con.close()
        return len(old)