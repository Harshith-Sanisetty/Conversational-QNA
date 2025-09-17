import nltk
import re
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import Config


class Nlp:
    def __init__(self):
        self.stops = set(nltk.corpus.stopwords.words('english'))
        self.vec = TfidfVectorizer(stop_words='english', max_features=100)
        

    def clean(self, txt):
        txt = re.sub(r'[^\w\s]', '', txt.lower())
        return ' '.join(txt.split())

    def get_kws(self, txt, lim=5):
        blob = TextBlob(txt)
        kws = []
        for w, t in blob.tags:
            if t in ['NN', 'NNS', 'NNP', 'JJ'] and w.lower() not in self.stops and len(w) > 2:
                kws.append(w.lower())
        return list(set(kws))[:lim]

    def get_mood(self, txt):
        pol = TextBlob(txt).sentiment.polarity
        if pol > 0.1: return 'positive'
        if pol < -0.1: return 'negative'
        return 'neutral'

    def get_topic(self, txt):
        txt_low = txt.lower()
        scores = {}
        for topic, kws in self.topics.items():
            score = sum(1 for kw in kws if kw in txt_low)
            if score > 0:
                scores[topic] = score
        if scores:
            return max(scores, key=scores.get)
        return 'general'

    def sim(self, txt1, txt2):
        try:
            mat = self.vec.fit_transform([txt1, txt2])
            s_val = cosine_similarity(mat[0:1], mat[1:2])
            return float(s_val[0][0])
        except:
            return 0.0

    def get_ents(self, txt):
        blob = TextBlob(txt)
        return [w for w, t in blob.tags if t in ['NNP', 'NNPS']]

    def find_ctx(self, msg, hist):
        if not hist: return []
        msg_kws = set(self.get_kws(msg))
        matches = []
        for c in hist[:5]:
            hist_kws = set(self.get_kws(c['u'] + ' ' + c['b']))
            olap = msg_kws.intersection(hist_kws)
            if olap:
                s_score = self.sim(msg, c['u'])
                matches.append({'c': c, 'olap': list(olap), 'sim': s_score})
        matches.sort(key=lambda x: x['sim'], reverse=True)
        return matches[:3]

    def mk_prompt(self, msg, matches):
        p = f"User said: '{msg}'\n"
        if matches:
            p += "\nContext from past chat:\n"
            for m in matches[:2]:
                c = m['c']
                olap = ', '.join(m['olap'])
                p += f"- About: {olap} | User: '{c['u']}' Bot: '{c['b']}'\n"
        return p

    def run(self, msg, hist=None):
        res = {
            'clean': self.clean(msg),
            'kws': self.get_kws(msg),
            'mood': self.get_mood(msg),
            'topic': self.get_topic(msg),
            'ents': self.get_ents(msg),
            'matches': [],
            'score': 0.0
        }
        if hist:
            res['matches'] = self.find_ctx(msg, hist)
            if res['matches']:
                res['score'] = max([m['sim'] for m in res['matches']])
        return res