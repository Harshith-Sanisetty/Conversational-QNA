import random
import pandas as pd
from memory import MemoryManager
from nlp_processor import NLPProcessor
from config import Config

class ConversationalBot:
    def __init__(self, response_file='responses.csv'):
        self.memory = MemoryManager()
        self.nlp = NLPProcessor()
        self.name = Config.BOT_NAME
        self.responses = self._load_responses(response_file)

    def _load_responses(self, file_path):
        
        try:
            df = pd.read_csv(file_path)
            response_map = {}
            for topic, topic_group in df.groupby('topic'):
                response_map[topic] = {}
                for sentiment, sent_group in topic_group.groupby('sentiment'):
                    response_map[topic][sentiment] = sent_group['response_text'].tolist()
            return response_map
        except FileNotFoundError:
            print(f"Error: ")
           
            return {'general': {'neutral': ["I see. Please check the response file path."]}}

    def generate_response(self, message, session_id):
        chat_history = self.memory.get_recent_chats(session_id, Config.CONTEXT_WINDOW)
        analysis = self.nlp.analyze_message(message, chat_history)
        response = self._get_base_response(analysis)

        if analysis['context_matches'] and analysis['context_score'] > Config.SIMILARITY_THRESHOLD:
            response = self._add_context(response, analysis)

        self.memory.save_chat(
            session_id=session_id,
            user_msg=message,
            bot_reply=response,
            topic=analysis['topic'],
            mood=analysis['sentiment'],
            keywords=','.join(analysis['keywords']),
            context_score=analysis['context_score']
        )
        return response, analysis

    def _get_base_response(self, analysis):
        topic = analysis.get('topic', 'general')
        sentiment = analysis.get('sentiment', 'neutral')

        topic_responses = self.responses.get(topic, self.responses.get('general', {}))
        response_options = topic_responses.get(sentiment, topic_responses.get('neutral', ["Tell me more."]))
        
        base_response = random.choice(response_options)

        if analysis.get('entities'):
            entity = analysis['entities'][0]
            base_response = f"{base_response} I noticed you mentioned {entity}."
        
        return base_response

    def _add_context(self, response, analysis):
        best_match = analysis['context_matches'][0]
        overlap_keywords = best_match.get('overlap', [])
        
        if overlap_keywords and random.random() > 0.5:
            context_templates = self.responses.get('context', {}).get('neutral', [])
            if context_templates:
                context_template = random.choice(context_templates)
                context_ref = overlap_keywords[0]
                context_addition = context_template.format(
                    topic=analysis['topic'],
                    context=context_ref
                )
                response = f"{response} {context_addition}"
        
        return response

    def start_conversation(self, user_name="User"):
        session_id = self.memory.create_session(user_name)
        greeting = f"Hi {user_name}! I'm {self.name}, your conversational assistant. How can I help you today?"
        
        self.memory.save_chat(
            session_id=session_id,
            user_msg="[SESSION_START]",
            bot_reply=greeting,
            topic="greeting",
            mood="positive"
        )
        return session_id, greeting

    def get_conversation_summary(self, session_id):
        stats = self.memory.get_session_stats(session_id)
        recent_chats = self.memory.get_recent_chats(session_id, 10)
        
        if not recent_chats:
            return "No conversation history yet."

        topic_counts = {}
        for chat in recent_chats:
            topic = chat['topic']
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        main_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        summary = f"We've exchanged {len(recent_chats)} messages. "
        if main_topics:
            topics_str = ", ".join([f"{topic} ({count})" for topic, count in main_topics])
            summary += f"Main topics: {topics_str}. "
        
        return summary

    def search_past_conversations(self, session_id, query):
        keywords = self.nlp.extract_keywords(query)
        if not keywords:
            return "Please provide more specific search terms."
        
        results = self.memory.search_memory(session_id, keywords, limit=3)
        
        if not results:
            return f"I couldn't find any past conversations about '{query}'."

        response = f"I found {len(results)} relevant past conversations about '{query}':\n\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. You said: \"{result['user_msg'][:50]}...\"\n"
            response += f"   I replied: \"{result['bot_reply'][:50]}...\"\n\n"
            
        return response