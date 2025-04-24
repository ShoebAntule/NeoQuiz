import requests
import json
import time
from django.conf import settings

# Rate limiting - max 5 calls per minute
LAST_CALL_TIME = 0
CALL_COUNT = 0

def rate_limited():
    global LAST_CALL_TIME, CALL_COUNT
    now = time.time()
    if now - LAST_CALL_TIME > 60:  # Reset counter if >1 minute passed
        CALL_COUNT = 0
        LAST_CALL_TIME = now
    
    if CALL_COUNT >= 5:  # Max 5 calls per minute
        time.sleep(60 - (now - LAST_CALL_TIME))
        CALL_COUNT = 0
        LAST_CALL_TIME = time.time()
    
    CALL_COUNT += 1

def generate_question(topic):
    """Generate quiz questions with enhanced error handling and fallbacks"""
    # Local question bank as final fallback
    local_questions = {
        "Computer Networks": [
            {
                "question": "What protocol is used for secure web browsing?",
                "options": ["A) HTTP", "B) FTP", "C) HTTPS", "D) SMTP"],
                "answer": "C"
            },
            {
                "question": "What does TCP stand for?",
                "options": ["A) Transmission Control Protocol", "B) Transfer Control Protocol", "C) Transmission Check Protocol", "D) Transfer Check Protocol"],
                "answer": "A"
            }
        ],
        "Programming": {
            "question": "Which language uses 'print' for output?",
            "options": ["A) Java", "B) C++", "C) Python", "D) JavaScript"],
            "answer": "C"
        },
        "Databases": {
            "question": "Which SQL clause filters results?",
            "options": ["A) SELECT", "B) FROM", "C) WHERE", "D) JOIN"],
            "answer": "C"
        },
        "Algorithms": {
            "question": "Which sort has O(n log n) complexity?",
            "options": ["A) Bubble", "B) Merge", "C) Insertion", "D) Selection"],
            "answer": "B"
        },
        "Operating Systems": {
            "question": "What manages memory allocation?",
            "options": ["A) Kernel", "B) Shell", "C) Compiler", "D) Scheduler"],
            "answer": "A"
        },
        "Security": [
            {
                "question": "Which is a symmetric encryption algorithm?",
                "options": ["A) RSA", "B) AES", "C) ECC", "D) SHA"],
                "answer": "B"
            },
            {
                "question": "What does SSL stand for?",
                "options": ["A) Secure Socket Layer", "B) System Security Layer", "C) Server Side Language", "D) Secure System Login"],
                "answer": "A"
            },
            {
                "question": "Which attack involves database injection?",
                "options": ["A) XSS", "B) CSRF", "C) SQLi", "D) DDoS"],
                "answer": "C"
            },
            {
                "question": "What is the purpose of a firewall?",
                "options": ["A) Encrypt data", "B) Filter network traffic", "C) Store passwords", "D) Scan for viruses"],
                "answer": "B"
            }
        ],
        "Web Development": {
            "question": "Which HTML tag creates a paragraph?",
            "options": ["A) <div>", "B) <span>", "C) <p>", "D) <text>"],
            "answer": "C"
        },
        "Data Structures": {
            "question": "Which structure uses LIFO principle?",
            "options": ["A) Queue", "B) Stack", "C) Array", "D) Tree"],
            "answer": "B"
        }
    }
    
    # Try configured providers first
    providers = [settings.AI_PROVIDER] if settings.AI_PROVIDER else ['deepseek', 'openai']
    prompt = f"""..."""  # (keep your existing prompt format)

    for provider in providers:
        try:
            rate_limited()  # Enforce rate limiting
            if provider == 'azure':
                client = OpenAI(
                    base_url=settings.AI_API_URLS[provider],
                    api_key=settings.AI_API_KEYS[provider],
                )
                try:
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=settings.AI_MODEL,
                        temperature=0.7
                    )
                    content = response.choices[0].message.content
                    try:
                        return json.loads(content)
                    except ValueError:
                        return {
                            'question': content,
                            'options': ["1) Option 1", "2) Option 2", "3) Option 3", "4) Option 4"],
                            'answer': "1"
                        }
                except Exception as e:
                    print(f"Azure API Error: {str(e)}")
                    continue
            else:
                headers = {
                    'Authorization': f'Bearer {settings.AI_API_KEYS[provider]}',
                    'Content-Type': 'application/json'
                }
                data = {
                    "model": settings.AI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            
            print(f"Attempting API call to {provider}...")
            print(f"URL: {settings.AI_API_URLS[provider]}")
            print(f"Headers: {headers}")
            print(f"Data: {data}")
            
            response = requests.post(
                settings.AI_API_URLS[provider],
                headers=headers,
                data=json.dumps(data),
                timeout=10
            )
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text[:200]}")  # Print first 200 chars
            response.raise_for_status()
            json_response = response.json()
            if 'choices' in json_response:
                content = json_response['choices'][0]['message']['content']
                try:
                    # Try to parse as JSON if possible
                    return json.loads(content)
                except ValueError:
                    # If not JSON, return as text
                    return {
                        'question': content,
                        'options': ["1) Option 1", "2) Option 2", "3) Option 3", "4) Option 4"],
                        'answer': "1"
                    }
            return {
                'error': "Invalid response format from API",
                'question': "",
                'options': [],
                'answer': ""
            }
        except requests.exceptions.HTTPError as e:
            print(f"API Error ({provider}): {str(e)}")
            if e.response.status_code == 429:
                continue  # Try next provider if quota exceeded
            else:
                continue
        except Exception as e:
            print(f"General Error ({provider}): {str(e)}")
            continue
    
    # Final fallback to local questions
    if topic in local_questions:
        try:
            import random
            # Get questions for topic (could be single question or list)
            questions = local_questions[topic]
            # If it's a list, pick random question, otherwise use single question
            q = random.choice(questions) if isinstance(questions, list) else questions
            # Shuffle options but keep track of correct answer
            options = q['options'].copy()
            correct_option = options[ord(q['answer'].lower()) - ord('a')]
            random.shuffle(options)
            # Format options with numbers (1, 2, 3...)
            formatted_options = [f"{i+1}) {opt.split(') ')[1]}" for i, opt in enumerate(options)]
            return {
                'question': q['question'],
                'options': formatted_options,
                'answer': str(options.index(correct_option) + 1)  # Return answer as number
            }
        except Exception as e:
            print(f"Error processing local question: {str(e)}")
            return {
                'error': f"Error processing question: {str(e)}",
                'question': q['question'] if 'q' in locals() else "Unknown question",
                'options': [],
                'answer': ""
            }
    
    return {
        'error': "Could not generate question (all providers failed)",
        'question': "",
        'options': [],
        'answer': ""
    }
