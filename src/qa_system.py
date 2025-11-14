import os
import re
import httpx
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import google.generativeai as genai
import logging
from itertools import cycle
from pathlib import Path

# Get project root directory (needed for logging setup)
PROJECT_ROOT = Path(__file__).parent.parent

# Configure logging level from environment or default to INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Set up logging to both console and file
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Create file handler for logs
log_file = LOGS_DIR / "qa_system.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file: {log_file}")
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Set cache directories to use project data folder
MODELS_DIR = DATA_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Set environment variables to store models locally
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(MODELS_DIR)
os.environ["TRANSFORMERS_CACHE"] = str(MODELS_DIR)
os.environ["HF_HOME"] = str(MODELS_DIR)
os.environ["TORCH_HOME"] = str(MODELS_DIR)


LOCATION_KEYWORDS = {
    "london", "paris", "tokyo", "new york", "santorini", "thailand", "bangkok", "rome",
    "madrid", "berlin", "amsterdam", "dubai", "singapore", "sydney", "mumbai", "beijing",
    "seoul", "vienna", "prague", "istanbul", "cairo", "moscow", "athens", "lisbon", "oslo",
    "stockholm", "copenhagen", "helsinki", "dublin", "edinburgh", "glasgow", "manchester",
    "birmingham", "liverpool", "bristol", "leeds", "sheffield", "newcastle", "cardiff",
    "belfast", "cannes", "thailand", "bali", "aspen", "gstaad", "ibiza", "capri", "miami",
    "los angeles", "san francisco", "san diego", "vegas", "chicago", "bahamas", "hawaii",
    "doha", "abu dhabi", "kuwait", "qatar", "nice", "porto", "seville", "naples", "florence",
    "venice", "zurich", "geneva", "montreal", "vancouver", "rio", "sao paulo", "cancun",
    "puerto rico", "tulum", "mykonos", "santorini", "crete", "rhodes", "capetown", "cape town"
}

MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]

ORDINAL_KEYWORDS = {"first", "second", "third", "fourth", "fifth", "last", "early", "mid", "late"}
TIME_UNITS = {"week", "weekend", "month", "quarter", "day", "evening"}

REQUEST_VERBS = {
    "book", "secure", "arrange", "reserve", "schedule", "organize", "plan",
    "confirm", "find", "set", "obtain", "prepare", "coordinate", "ensure", "lock"
}

PREFERENCE_KEYWORDS = {"prefer", "like", "love", "enjoy", "favorite", "favourite", "always", "usually"}
THANKS_KEYWORDS = {"thank", "thanks", "appreciate", "gratitude"}
TRAVEL_KEYWORDS = {
    "trip", "travel", "traveling", "travelling", "vacation", "holiday", "itinerary",
    "flight", "journey", "stay", "villa", "resort", "hotel", "booking", "reservation",
    "festival", "retreat", "getaway", "visit", "tour", "excursion"
}

KNOWN_RESTAURANTS = {
    "le bernardin", "alinea", "eleven madison park", "noma", "osteria francescana",
    "per se", "the french laundry", "atelier crenn", "blue hill", "petto", "nobu",
    "sukiyabashi jiro", "the fat duck"
}

RESTAURANT_HINT_KEYWORDS = {"restaurant", "dinner", "lunch", "brunch", "tasting", "chef", "table", "reservation"}

MONTH_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"(?:\s+\d{1,2}(?:st|nd|rd|th)?)?(?:,\s*\d{4})?\b",
    re.IGNORECASE,
)
WEEK_RANGE_PATTERN = re.compile(
    r"\b(?:first|second|third|fourth|fifth|last|early|mid|late)\s+(?:week|weekend|part)\s+of\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\b",
    re.IGNORECASE,
)
RELATIVE_TIME_PATTERN = re.compile(
    r"\b(?:this|next)\s+(?:week|weekend|month|summer|winter|spring|fall|autumn)\b",
    re.IGNORECASE,
)
RESTAURANT_RESERVATION_PATTERN = re.compile(
    r"(?:reservation|dinner|lunch|brunch|meal|chef['’]?s table)\s+at\s+([A-Z][\w&'’.-]*(?:\s+[A-Z][\w&'’.-]*){0,3})"
)
RESTAURANT_AT_PATTERN = re.compile(
    r"\bat\s+([A-Z][\w&'’.-]*(?:\s+[A-Z][\w&'’.-]*){0,3})"
)

class GeminiKeyRotator:
    """Manages multiple Gemini API keys with round-robin rotation"""
    
    def __init__(self):
        self.keys = []
        self.current_key_index = 0
        self.key_cycle = None
        self._load_keys()
    
    def _load_keys(self):
        """Load all Gemini API keys from environment"""
        # Support both comma-separated and numbered env vars
        env_keys = os.getenv("GEMINI_API_KEYS", "").split(",")
        env_keys = [k.strip() for k in env_keys if k.strip()]
        
        # Also support GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
        index = 1
        while True:
            key = os.getenv(f"GEMINI_API_KEY_{index}")
            if not key:
                break
            env_keys.append(key)
            index += 1
        
        if not env_keys:
            logger.warning("No Gemini API keys found. Set GEMINI_API_KEYS or GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.")
            logger.warning("System will start but question answering will fail without API keys.")
            # Allow system to start without keys for testing/model loading
            self.keys = []
            self.key_cycle = None
        else:
            self.keys = env_keys
            self.key_cycle = cycle(self.keys)
            logger.info(f"Loaded {len(self.keys)} Gemini API keys")
    
    def get_next_key(self) -> str:
        """Get next API key in rotation"""
        if not self.key_cycle:
            raise ValueError("No API keys available. Please set GEMINI_API_KEYS environment variable.")
        return next(self.key_cycle)
    
    def get_current_key(self) -> str:
        """Get current API key"""
        if not self.keys:
            raise ValueError("No API keys available. Please set GEMINI_API_KEYS environment variable.")
        return self.keys[self.current_key_index % len(self.keys)]


class QuestionAnsweringSystem:
    def __init__(self):
        self.api_url = "https://november7-730026606190.europe-west1.run.app/messages"
        self.messages = []
        self.embeddings = None
        self.index = None
        self.embedding_model = None
        self.num_messages = 0
        self.message_texts = []
        self.key_rotator = None
        self.index_path = DATA_DIR / "faiss_index.bin"
    
    async def initialize(self):
        """Initialize the QA system"""
        try:
            # Initialize key rotator
            logger.info("Initializing Gemini API key rotator...")
            self.key_rotator = GeminiKeyRotator()
            
            # 1. Load embedding model (will be stored in data/models/)
            logger.info(f"Loading embedding model (storing in {MODELS_DIR})...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=str(MODELS_DIR))
            
            # 2. Fetch messages from API
            logger.info("Fetching messages from API...")
            # Try without trailing slash first, then with if needed
            api_urls_to_try = [
                self.api_url.rstrip('/'),  # Without trailing slash
                self.api_url,  # Original
                self.api_url + '/' if not self.api_url.endswith('/') else self.api_url  # With trailing slash
            ]
            
            api_data = None
            last_error = None
            
            for url in api_urls_to_try:
                try:
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                        response = await client.get(url)
                        response.raise_for_status()
                        api_data = response.json()
                        logger.info(f"Successfully fetched data from {url}")
                        break
                except Exception as e:
                    last_error = e
                    logger.debug(f"Failed to fetch from {url}: {str(e)}")
                    continue
            
            if api_data is None:
                raise Exception(f"Failed to fetch messages from API after trying multiple URLs: {last_error}")
            
            # Handle different API response formats
            if isinstance(api_data, dict):
                # API returns {"total": X, "items": [...]}
                if "items" in api_data:
                    self.messages = api_data["items"]
                elif "messages" in api_data:
                    self.messages = api_data["messages"]
                else:
                    # Assume the dict itself contains message data
                    self.messages = [api_data] if api_data else []
            elif isinstance(api_data, list):
                # API returns list directly
                self.messages = api_data
            else:
                logger.warning(f"Unexpected API response format: {type(api_data)}")
                self.messages = []
            
            self.num_messages = len(self.messages)
            logger.info(f"Loaded {self.num_messages} messages")
            
            # 3. Create searchable text from messages with better semantic structure
            self.message_texts = []
            for msg in self.messages:
                # Handle both dict and string formats
                if isinstance(msg, str):
                    # If message is a string, use it directly
                    self.message_texts.append(msg)
                    continue
                
                if not isinstance(msg, dict):
                    logger.warning(f"Skipping invalid message format: {type(msg)}")
                    continue
                
                # Support both field name formats
                member_name = msg.get("member_name") or msg.get("user_name") or msg.get("name")
                content = msg.get("content") or msg.get("message") or msg.get("text")
                timestamp = msg.get("timestamp") or msg.get("time") or msg.get("created_at")
                
                # Create semantic-rich text: prioritize content, then member, then timestamp
                # This helps embeddings capture the actual meaning better
                text_parts = []
                if content:
                    # Content is most important for semantic matching
                    text_parts.append(content)
                if member_name:
                    text_parts.append(member_name)
                if timestamp:
                    # Extract date information for time-based queries
                    text_parts.append(timestamp)
                
                if text_parts:
                    # Join with space for better semantic flow
                    self.message_texts.append(" ".join(text_parts))
                else:
                    # Fallback: use string representation
                    self.message_texts.append(str(msg))
            
            # 4. Generate embeddings
            logger.info("Generating embeddings...")
            if not self.message_texts:
                raise Exception("No message texts to encode. Check API data loading.")
            
            self.embeddings = self.embedding_model.encode(
                self.message_texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Validate embeddings shape
            if len(self.embeddings.shape) < 2:
                raise Exception(f"Invalid embeddings shape: {self.embeddings.shape}. Expected 2D array.")
            
            # 5. Build FAISS index
            logger.info("Building FAISS index...")
            dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(self.embeddings.astype('float32'))
            
            # Save index to disk
            faiss.write_index(self.index, str(self.index_path))
            logger.info(f"FAISS index saved to {self.index_path}")
            
            logger.info("Initialization complete!")
        
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise
    
    async def answer_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Answer a question using RAG with Gemini"""
        try:
            logger.info(f"=== Processing question: '{question}' ===")
            
            # 1. Embed the question
            logger.debug("Step 1: Generating question embedding...")
            question_embedding = self.embedding_model.encode(
                [question],
                convert_to_numpy=True
            )
            logger.debug(f"Question embedding shape: {question_embedding.shape}")
            
            # 2. Search for similar messages with larger top_k to filter later
            search_k = min(top_k * 3, len(self.messages))  # Get more candidates for filtering
            logger.debug(f"Step 2: Searching FAISS index with search_k={search_k}, top_k={top_k}")
            distances, indices = self.index.search(
                question_embedding.astype('float32'),
                search_k
            )
            logger.info(f"FAISS search returned {len(indices[0])} candidate messages")
            logger.debug(f"Top 5 distances: {distances[0][:5].tolist()}")
            
            # 3. Extract key entities from question for relevance checking FIRST
            logger.debug("Step 3: Extracting keywords and critical entities from question...")
            
            # IMPORTANT: Extract proper nouns BEFORE lowercasing
            question_words_original = question.split()
            proper_nouns = set()
            proper_noun_originals: Dict[str, str] = {}
            question_subjects: List[str] = []
            question_subjects_lower = set()
            for word in question_words_original:
                clean_word = word.strip(".,!?;:'\"()[]{}")
                if len(clean_word) > 2 and clean_word[0].isupper():
                    # Common capitalized words that are NOT proper nouns
                    common_caps = {"The", "A", "An", "And", "Or", "But", "In", "On", "At", "To", "For", "Of", "With", "By", 
                                  "What", "When", "Where", "Who", "Which", "How", "Does", "Do", "Did", "Will", "Would", 
                                  "Can", "Could", "Should", "May", "Might", "Tell", "Have", "Has", "Had", "Are", "Is", "Was", "Were"}
                    if clean_word not in common_caps:
                        base_word = clean_word.rstrip("'s").rstrip("'")
                        base_lower = base_word.lower()
                        proper_nouns.add(base_lower)
                        proper_noun_originals.setdefault(base_lower, base_word)
                        if base_lower not in LOCATION_KEYWORDS and base_lower not in question_subjects_lower:
                            question_subjects.append(base_word)
                            question_subjects_lower.add(base_lower)
                        logger.debug(f"Found proper noun: {clean_word} -> {base_lower}")
            
            question_lower = question.lower()
            question_type = self._detect_question_type(question_lower)
            question_words = set(question_lower.split())
            # Remove common stop words (expanded list to include common verbs and prepositions)
            stop_words = {"is", "are", "was", "were", "be", "been", "being", "the", "a", "an", "and", "or", "but", 
                         "in", "on", "at", "to", "for", "of", "with", "by", "from", "about", "into", "onto", 
                         "what", "when", "where", "who", "which", "how", "does", "do", "did", "will", "would", 
                         "can", "could", "should", "may", "might", "must", "shall", "tell", "me", "about", 
                         "planning", "her", "his", "their", "my", "your", "our", "its", "it", "they", "them", 
                         "we", "us", "have", "has", "had", "having", "s", "'s", "this", "that", "these", "those",
                         "both", "mentioned", "mention", "mentioned", "information", "have", "has"}
            question_keywords = question_words - stop_words
            # Clean punctuation from keywords
            question_keywords = {kw.rstrip(".,!?;:'\"()[]{}") for kw in question_keywords}
            logger.debug(f"Question keywords (after stop word removal): {question_keywords}")
            
            # Identify critical keywords that MUST be present (locations, specific entities, etc.)
            # Common location names and important entities
            critical_keywords = set()
            question_locations: List[str] = []
            
            # Filter out common verbs/words from proper nouns before adding to critical keywords
            # Only keep actual proper nouns (names, places) and filter out verbs that were capitalized
            common_verb_words = {"tell", "me", "about", "have", "has", "had", "are", "is", "was", "were", "planning", "mentioned", "mention"}
            filtered_proper_nouns = {pn for pn in proper_nouns if pn not in common_verb_words}
            
            # Add proper nouns as critical keywords (after filtering)
            critical_keywords.update(filtered_proper_nouns)
            
            # Extract locations from question
            for keyword in question_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in LOCATION_KEYWORDS:
                    critical_keywords.add(keyword_lower)
                    if keyword_lower not in question_locations:
                        question_locations.append(keyword_lower)
                    logger.debug(f"Found location keyword: {keyword_lower}")
            
            # Also check for multi-word locations in the question
            question_words_list = question_lower.split()
            for i in range(len(question_words_list) - 1):
                two_word = f"{question_words_list[i]} {question_words_list[i+1]}"
                if two_word in LOCATION_KEYWORDS:
                    critical_keywords.add(two_word)
                    if two_word not in question_locations:
                        question_locations.append(two_word)
                    logger.debug(f"Found multi-word location: {two_word}")

            for pn in proper_nouns:
                if pn in LOCATION_KEYWORDS and pn not in question_locations:
                    question_locations.append(pn)

            question_topics = set()
            if any(word in question_lower for word in ["restaurant", "restaurants", "dining", "dinner", "lunch", "chef", "table"]):
                question_topics.add("restaurants")
            if any(word in question_lower for word in ["trip", "travel", "vacation", "holiday", "flight", "itinerary", "journey", "stay"]):
                question_topics.add("travel")
            if any(word in question_lower for word in ["preference", "favorite", "favourite"]):
                question_topics.add("preference")

            question_profile = {
                "type": question_type,
                "subjects": question_subjects,
                "subject_display": question_subjects[0] if question_subjects else None,
                "locations": question_locations,
                "topics": question_topics,
                "keywords": question_keywords,
                "question": question,
                "question_lower": question_lower,
                "proper_nouns": proper_noun_originals
            }
            
            if critical_keywords:
                logger.info(f"Critical keywords identified (must be in messages): {critical_keywords}")
            else:
                logger.info("No critical keywords identified - will match based on semantic similarity and keyword ratio")
            
            # Set adaptive distance threshold based on whether we have critical keywords
            # Adaptive threshold: more lenient if we have critical keywords (they'll filter), stricter otherwise
            # For general questions without critical keywords, be more lenient since we rely on semantic similarity
            if critical_keywords:
                MAX_DISTANCE_THRESHOLD = 1.3  # Slightly more lenient when we have critical keywords to filter
            else:
                MAX_DISTANCE_THRESHOLD = 1.5  # More lenient for general questions (increased from 1.2 to 1.5)
            
            logger.debug(f"Step 4: Filtering messages (distance threshold: {MAX_DISTANCE_THRESHOLD}, adaptive keyword match)")
            relevant_messages = []
            skipped_distance = 0
            skipped_critical = 0
            skipped_keyword = 0
            
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.messages):
                    continue
                
                distance = float(distances[0][i])
                
                # Only include messages below distance threshold
                if distance > MAX_DISTANCE_THRESHOLD:
                    skipped_distance += 1
                    logger.debug(f"  [SKIP] Message {idx}: distance {distance:.3f} > threshold {MAX_DISTANCE_THRESHOLD}")
                    continue
                
                msg_data = self.messages[idx]
                # Ensure msg_data is a dict for consistent handling
                if isinstance(msg_data, str):
                    msg_data = {"content": msg_data}
                elif not isinstance(msg_data, dict):
                    msg_data = {"data": str(msg_data)}
                
                # Check keyword relevance - if question has specific keywords, message should contain at least some
                msg_text = self.message_texts[idx] if idx < len(self.message_texts) else str(msg_data)
                msg_text_lower = msg_text.lower()
                
                # Get message content for logging
                msg_content = msg_data.get("message") or msg_data.get("content") or msg_data.get("text") or str(msg_data)[:100]
                
                # Get user/member name for matching
                user_name = (msg_data.get("user_name") or msg_data.get("member_name") or msg_data.get("name") or "").lower()
                
                # CRITICAL: If question has critical keywords (locations, proper nouns), they SHOULD be in the message
                # For proper nouns (names), also check user_name/member_name fields
                # More lenient: require at least 50% of critical keywords to match (or at least 1 if only 1-2 keywords)
                if critical_keywords:
                    matched_critical = []
                    missing_critical = []
                    for ck in critical_keywords:
                        matched = False
                        match_location = None
                        
                        # Check in message text (case-insensitive) - split into words for better matching
                        msg_words = msg_text_lower.split()
                        ck_words = ck.split()
                        
                        # Check if all words of keyword are in message (better for multi-word keywords like "new york")
                        if all(any(ckw in word or word in ckw or ckw in word[:len(ckw)+2] for word in msg_words) for ckw in ck_words):
                            matched_critical.append(ck)
                            matched = True
                            match_location = "message text"
                            logger.debug(f"  Found critical keyword '{ck}' in message text")
                        
                        # Also check in user_name (case-insensitive) - check as whole name or word match
                        if not matched and user_name:
                            user_name_words = user_name.split()
                            # Check if keyword matches user_name (exact or partial)
                            # For names: "amira" should match "amira van den berg"
                            if ck in user_name:
                                matched_critical.append(ck)
                                matched = True
                                match_location = f"user_name ({user_name})"
                                logger.debug(f"  Found critical keyword '{ck}' in user_name: {user_name}")
                            # Check word-by-word matching
                            elif any(ckw in user_name_words for ckw in ck_words):
                                matched_critical.append(ck)
                                matched = True
                                match_location = f"user_name words ({user_name})"
                                logger.debug(f"  Found critical keyword '{ck}' as word in user_name: {user_name}")
                        
                        if not matched:
                            missing_critical.append(ck)
                    
                    # More lenient filtering: require at least 50% match, or at least 1 keyword if only 1-2 keywords total
                    total_critical = len(critical_keywords)
                    min_required = max(1, int(total_critical * 0.5)) if total_critical > 2 else 1
                    
                    if len(matched_critical) < min_required:
                        skipped_critical += 1
                        logger.debug(f"  [SKIP] Message {idx}: matched {len(matched_critical)}/{total_critical} critical keywords (need {min_required}). Matched: {matched_critical}, Missing: {missing_critical}. User: {user_name}, Content: {msg_content[:80]}...")
                        continue
                    else:
                        logger.info(f"  [PASS] Message {idx}: matched {len(matched_critical)}/{total_critical} critical keywords: {matched_critical}. User: {user_name}")
                
                # Count matching keywords (also check for partial matches and synonyms)
                matching_keywords = 0
                for keyword in question_keywords:
                    keyword_clean = keyword.lower().rstrip(".,!?;:'\"()[]{}")
                    # Direct match
                    if keyword_clean in msg_text_lower:
                        matching_keywords += 1
                    # Check for related terms (e.g., "restaurant" matches "restaurants", "restaurant's")
                    elif keyword_clean.endswith('s') and keyword_clean[:-1] in msg_text_lower:
                        matching_keywords += 0.8  # Partial credit for plural/singular
                    elif not keyword_clean.endswith('s') and (keyword_clean + 's') in msg_text_lower:
                        matching_keywords += 0.8
                    # Check for possessive forms
                    elif keyword_clean + "'s" in msg_text_lower or keyword_clean + "'" in msg_text_lower:
                        matching_keywords += 0.9
                
                keyword_match_ratio = matching_keywords / len(question_keywords) if question_keywords else 1.0
                
                # Adaptive threshold: if we have critical keywords, we can be more lenient on general keyword match
                # If no critical keywords, require better keyword match
                if critical_keywords:
                    min_keyword_match = 0.15  # Very lenient when critical keywords are enforced (they ensure relevance)
                else:
                    min_keyword_match = 0.3   # Standard threshold
                
                # Require minimum keyword match for questions with specific keywords
                # BUT: If we already passed critical keyword check, be very lenient on general keyword match
                # Critical keywords already ensure relevance
                if len(question_keywords) > 2 and keyword_match_ratio < min_keyword_match:
                    # If we have critical keywords and they already matched (we passed that check), skip keyword match check
                    if critical_keywords:
                        # We already passed critical keyword check above, so allow through
                        # This prevents double-filtering: if critical keywords matched, trust that
                        logger.debug(f"  [KEEP] Message {idx}: critical keywords already matched, allowing despite low keyword match {keyword_match_ratio:.2f}")
                    else:
                        skipped_keyword += 1
                        logger.debug(f"  [SKIP] Message {idx}: keyword match {keyword_match_ratio:.2f} < {min_keyword_match}. Content: {msg_content[:80]}...")
                        continue
                
                relevant_messages.append({
                    "text": msg_text,
                    "data": msg_data,
                    "distance": distance,
                    "keyword_match": keyword_match_ratio
                })
                logger.debug(f"  [KEEP] Message {idx}: distance={distance:.3f}, keyword_match={keyword_match_ratio:.2f}, content: {msg_content[:80]}...")
                
                # Stop once we have enough relevant messages
                if len(relevant_messages) >= top_k:
                    break
            
            logger.info(f"Filtering results: {len(relevant_messages)} relevant messages found (skipped: {skipped_distance} by distance, {skipped_critical} by critical keywords, {skipped_keyword} by keyword match)")
            
            # If no relevant messages found, return early
            if not relevant_messages:
                logger.warning(f"No relevant messages found for question: '{question}'")
                return {
                    "answer": "I don't have enough information to answer this question.",
                    "confidence": 0.0,
                    "sources": []
                }
            
            # 4. Build context for LLM and extract key information
            logger.debug("Step 5: Building context from relevant messages...")
            context_parts = []
            for idx, msg in enumerate(relevant_messages):
                msg_data = msg["data"]
                if isinstance(msg_data, dict):
                    member = msg_data.get("user_name") or msg_data.get("member_name") or msg_data.get("name") or "Unknown"
                    content = msg_data.get("message") or msg_data.get("content") or msg_data.get("text") or ""
                    context_parts.append(f"{member}: {content}")
                    logger.debug(f"  Context[{idx}]: {member}: {content[:100]}...")
                else:
                    context_parts.append(str(msg_data))
            
            context = "\n".join(context_parts)
            logger.debug(f"Total context length: {len(context)} characters")
            
            # 5. Generate answer using Gemini or format context-based answer
            # Track which messages were actually used for the answer
            answer_messages = relevant_messages  # Default to all relevant messages
            
            logger.debug(f"Step 6: Generating answer (API keys available: {bool(self.key_rotator and self.key_rotator.keys)})")
            
            if not self.key_rotator or not self.key_rotator.keys:
                logger.warning("No Gemini API keys available - using fallback answer generation")
                # Format a clean answer from context when API keys are missing
                if relevant_messages:
                    matching_messages = relevant_messages
                    answer_messages = matching_messages
                    fallback_answer, selected_messages = self._build_structured_answer(
                        question_profile=question_profile,
                        matching_messages=matching_messages
                    )
                    if selected_messages:
                        answer_messages = selected_messages
                    if fallback_answer:
                        answer = fallback_answer
                        logger.info(f"Fallback answer (structured): {answer[:150]}...")
                    else:
                        answer = "I don't have enough information to answer this question."
                else:
                    answer = "I don't have enough information to answer this question."
                    logger.warning("Fallback: No relevant messages available")
            else:
                try:
                    api_key = self.key_rotator.get_next_key()
                    logger.debug(f"Using Gemini API key (rotating through {len(self.key_rotator.keys)} keys)")
                    genai.configure(api_key=api_key)
                    # Improved system prompt for direct, concise answers
                    # Use previously detected question type to guide the answer
                    logger.debug(f"Question type detected: {question_type}")
                    
                    prompt = f"""Answer the question directly and concisely using ONLY the information provided in the context.

CRITICAL RULES:
1. Do NOT start with phrases like "Based on the available information", "According to the context", or "Based on the context"
2. Answer ONLY what is asked - if asked "when", provide time/date; if asked "where", provide location; if asked "what", provide the thing
3. Do NOT include information that doesn't directly answer the question
4. If the question asks about a specific location, person, or entity, ONLY answer if that specific location/person/entity is mentioned in the context
5. If asked about "preferences", extract preference-related information, not specific booking instructions
6. If the answer is not in the context or doesn't match the question, say "I don't have enough information to answer this question."

Question type: {question_type}
Question asked: {question}

Context from member messages:
{context}

IMPORTANT: Verify that your answer directly addresses the question "{question}". If the context doesn't contain information that answers this specific question, respond with "I don't have enough information to answer this question."

Answer directly (just the answer, no extra text):"""
                    
                    # Use only gemini-2.0-flash-exp model (latest experimental version)
                    model_name = None
                    answer = None
                    
                    # Use only gemini-2.0-flash-exp model (correct name - 2.5 doesn't exist yet)
                    model_option = 'gemini-2.0-flash-exp'
                    
                    logger.debug(f"Using Gemini model: {model_option}")
                    try:
                        model = genai.GenerativeModel(model_option)
                        response = model.generate_content(
                            prompt,
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.2,
                                max_output_tokens=150,
                                top_p=0.8,
                            )
                        )
                        answer = response.text.strip()
                        model_name = model_option
                        logger.info(f"✓ Successfully used Gemini model: {model_option}")
                        logger.debug(f"Raw Gemini response: {answer[:200]}...")
                    except Exception as model_error:
                        logger.error(f"✗ Model {model_option} failed: {str(model_error)}")
                        raise Exception(f"Gemini model {model_option} failed: {str(model_error)}")
                    
                    if not answer:
                        raise Exception(f"Gemini model {model_option} returned empty response")
                    
                    # Clean up the answer - remove common prefixes
                    answer = answer.strip()
                    prefixes_to_remove = [
                        "Based on the available information,",
                        "According to the context,",
                        "Based on the context,",
                        "From the information provided,",
                        "Based on the provided context,",
                        "Based on available information,",
                        "According to available information,"
                    ]
                    for prefix in prefixes_to_remove:
                        if answer.lower().startswith(prefix.lower()):
                            answer = answer[len(prefix):].strip()
                            # Remove leading comma, colon, or space if present
                            answer = answer.lstrip(',: ')
                            break
                except Exception as e:
                    logger.error(f"Error calling Gemini API: {str(e)}", exc_info=True)
                    logger.info("Falling back to context-based answer generation")
                    # Fallback: Try to extract answer from context intelligently
                    if relevant_messages:
                        matching_messages = relevant_messages
                        answer_messages = matching_messages
                        fallback_answer, selected_messages = self._build_structured_answer(
                            question_profile=question_profile,
                            matching_messages=matching_messages
                        )
                        if selected_messages:
                            answer_messages = selected_messages
                        if fallback_answer:
                            answer = fallback_answer
                            logger.info(f"Fallback answer (structured): {answer[:150]}...")
                        else:
                            answer = "I don't have enough information to answer this question."
                            logger.warning("Fallback: Structured formatter returned no answer")
                    else:
                        answer = "I don't have enough information to answer this question."
                        logger.warning("Fallback: No relevant messages available")
            
            # Calculate confidence based on distance from actually used messages
            logger.debug("Step 7: Calculating confidence and formatting sources...")
            if answer_messages:
                min_distance = min(msg.get("distance", 10.0) for msg in answer_messages)
                logger.debug(f"Using minimum distance from {len(answer_messages)} answer messages: {min_distance:.3f}")
            else:
                min_distance = float(distances[0][0]) if len(distances[0]) > 0 else 10.0
                logger.debug(f"Using minimum distance from raw search results: {min_distance:.3f}")
            confidence = max(0, 1.0 - (min_distance / 10.0))
            logger.info(f"Confidence calculated: {confidence:.2f} (based on distance {min_distance:.3f})")
            
            # Format sources with proper member names (use answer_messages if available)
            formatted_sources = []
            sources_to_use = answer_messages if answer_messages else relevant_messages
            logger.debug(f"Formatting {min(len(sources_to_use), 3)} sources from {len(sources_to_use)} available messages")
            for msg in sources_to_use[:3]:
                msg_data = msg["data"]
                if isinstance(msg_data, dict):
                    # Ensure member_name is set for frontend display
                    source = dict(msg_data)  # Copy to avoid modifying original
                    if "member_name" not in source:
                        source["member_name"] = source.get("user_name") or source.get("name") or "Unknown"
                    formatted_sources.append(source)
                else:
                    formatted_sources.append({"member_name": "Unknown", "content": str(msg_data)})
            
            logger.info(f"=== Final Answer: '{answer[:100]}...' (confidence: {confidence:.2f}, sources: {len(formatted_sources)}) ===")
            
            return {
                "answer": answer,
                "confidence": round(confidence, 2),
                "sources": formatted_sources
            }
        
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}", exc_info=True)
            raise
    
    def _detect_question_type(self, question_lower: str) -> str:
        """Rudimentary question type detection for formatting answers."""
        lowered = question_lower or ""
        if any(phrase in lowered for phrase in ["when", "what time", "what date"]):
            return "time"
        if any(phrase in lowered for phrase in ["where", "location", "place"]):
            return "location"
        if any(phrase in lowered for phrase in ["who", "which person"]):
            return "person"
        if any(phrase in lowered for phrase in ["what", "which"]):
            return "thing"
        return "general"

    def _build_structured_answer(
        self,
        question_profile: Dict[str, Any],
        matching_messages: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        if not matching_messages:
            return None, []
        
        fact_wrappers = []
        for msg in matching_messages:
            msg_data = msg.get("data")
            if not isinstance(msg_data, dict):
                msg_data = {"message": str(msg.get("data", ""))}
            fact = self._extract_message_fact(msg_data)
            if not fact["content"]:
                continue
            fact_wrappers.append({"fact": fact, "message": msg})
        
        if not fact_wrappers:
            return None, []
        
        subject_names_lower = [s.lower() for s in question_profile.get("subjects", []) if s]
        filtered_subject, subject_match = self._filter_facts_by_subject(fact_wrappers, subject_names_lower)
        if subject_names_lower and not subject_match:
            subject_candidates = question_profile.get("subjects") or []
            subject_display = question_profile.get("subject_display") or (subject_candidates[0] if subject_candidates else "this member")
            logger.debug(f"Structured formatter: no facts matched subject {subject_names_lower}")
            return f"I couldn't find any recent updates from {subject_display} about that.", []
        
        filtered_location, location_match = self._filter_facts_by_location(
            filtered_subject,
            question_profile.get("locations") or []
        )
        if question_profile.get("locations") and not location_match:
            location_phrase = self._format_list([loc.title() for loc in question_profile["locations"]])
            subject_display = question_profile.get("subject_display")
            if subject_display:
                note = f"{subject_display} hasn't mentioned {location_phrase} yet."
            else:
                note = f"I couldn't find any mention of {location_phrase} in the available messages."
            logger.debug("Structured formatter: location constraint not satisfied")
            return note, []
        
        usable_wrappers = filtered_location
        facts = [fw["fact"] for fw in usable_wrappers]
        if not facts:
            return None, []
        
        answer_text = self._compose_answer_from_facts(question_profile, facts)
        selected_messages = [fw["message"] for fw in usable_wrappers] if answer_text else []
        return answer_text, selected_messages

    def _extract_message_fact(self, msg_data: Dict[str, Any]) -> Dict[str, Any]:
        member = msg_data.get("user_name") or msg_data.get("member_name") or msg_data.get("name") or "Unknown member"
        content = (msg_data.get("message") or msg_data.get("content") or msg_data.get("text") or "").strip()
        content_lower = content.lower()
        
        locations = self._extract_locations_from_text(content)
        restaurants = self._extract_restaurant_mentions(content)
        time_phrases = self._extract_time_phrases(content)
        
        is_request = self._is_request_sentence(content_lower)
        is_preference = any(word in content_lower for word in PREFERENCE_KEYWORDS)
        is_gratitude = any(word in content_lower for word in THANKS_KEYWORDS)
        topics = set()
        if restaurants:
            topics.add("restaurants")
        if any(word in content_lower for word in TRAVEL_KEYWORDS) or locations:
            topics.add("travel")
        if is_preference:
            topics.add("preference")
        
        if is_request:
            action_type = "request"
        elif is_preference:
            action_type = "preference"
        elif is_gratitude:
            action_type = "gratitude"
        else:
            action_type = "statement"
        
        return {
            "member": member,
            "member_lower": member.lower(),
            "content": content,
            "content_lower": content_lower,
            "locations": locations,
            "locations_lower": [loc.lower() for loc in locations],
            "restaurants": restaurants,
            "time_phrases": time_phrases,
            "is_request": is_request,
            "is_preference": is_preference,
            "is_gratitude": is_gratitude,
            "topics": topics,
            "action_type": action_type,
        }

    def _extract_locations_from_text(self, text: str) -> List[str]:
        locations = []
        text_lower = text.lower()
        for loc in LOCATION_KEYWORDS:
            if loc in text_lower:
                original = self._get_original_span(text, text_lower, loc)
                if original and original not in locations:
                    locations.append(original)
        return locations

    def _get_original_span(self, original_text: str, lowered_text: str, keyword_lower: str) -> str:
        idx = lowered_text.find(keyword_lower)
        if idx == -1:
            return keyword_lower.title()
        return original_text[idx: idx + len(keyword_lower)]

    def _extract_time_phrases(self, text: str) -> List[str]:
        phrases = []
        for pattern in (WEEK_RANGE_PATTERN, MONTH_PATTERN, RELATIVE_TIME_PATTERN):
            for match in pattern.finditer(text):
                snippet = match.group(0).strip(" ,.")
                if snippet:
                    phrases.append(snippet)
        return self._unique_preserve_order(phrases)

    def _extract_restaurant_mentions(self, text: str) -> List[str]:
        if not text:
            return []
        matches = []
        normalized_text = text.replace("’", "'")
        text_lower = normalized_text.lower()
        
        for pattern in (RESTAURANT_RESERVATION_PATTERN,):
            for match in pattern.finditer(normalized_text):
                candidate = match.group(1).strip(" ,.")
                candidate_lower = candidate.lower()
                if self._looks_like_restaurant_name(candidate_lower):
                    matches.append(candidate)
        
        if any(keyword in text_lower for keyword in RESTAURANT_HINT_KEYWORDS):
            for match in RESTAURANT_AT_PATTERN.finditer(normalized_text):
                candidate = match.group(1).strip(" ,.")
                candidate_lower = candidate.lower()
                if candidate_lower in KNOWN_RESTAURANTS or self._looks_like_restaurant_name(candidate_lower):
                    matches.append(candidate)
        
        for known in KNOWN_RESTAURANTS:
            if known in text_lower:
                matches.append(self._get_original_span(normalized_text, text_lower, known))
        
        return self._unique_preserve_order(matches)

    def _looks_like_restaurant_name(self, candidate_lower: str) -> bool:
        if not candidate_lower:
            return False
        disallowed = {"table", "tables", "villa", "festival", "arrangements", "week", "weeks", "family"}
        tokens = candidate_lower.replace("’", "'").split()
        return not any(token in disallowed for token in tokens)

    def _is_request_sentence(self, content_lower: str) -> bool:
        if not content_lower:
            return False
        first_word = content_lower.split()[0]
        if first_word in REQUEST_VERBS:
            return True
        if content_lower.startswith("please "):
            return True
        if content_lower.startswith("could you") or content_lower.startswith("can you"):
            return True
        if content_lower.startswith("need to"):
            return True
        return False

    def _filter_facts_by_subject(
        self,
        fact_wrappers: List[Dict[str, Any]],
        subject_names_lower: List[str]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        if not subject_names_lower:
            return fact_wrappers, True
        filtered = [
            fw for fw in fact_wrappers
            if any(name in fw["fact"]["member_lower"] for name in subject_names_lower)
        ]
        if filtered:
            return filtered, True
        return fact_wrappers, False

    def _filter_facts_by_location(
        self,
        fact_wrappers: List[Dict[str, Any]],
        location_terms: List[str]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        if not location_terms:
            return fact_wrappers, True
        location_terms_lower = [loc.lower() for loc in location_terms]
        filtered = []
        for fw in fact_wrappers:
            fact = fw["fact"]
            match = False
            for loc in location_terms_lower:
                if any(loc == loc_value for loc_value in fact["locations_lower"]):
                    match = True
                    break
                if loc in fact["content_lower"]:
                    match = True
                    break
            if match:
                filtered.append(fw)
        if filtered:
            return filtered, True
        return fact_wrappers, False

    def _compose_answer_from_facts(self, question_profile: Dict[str, Any], facts: List[Dict[str, Any]]) -> str:
        if not facts:
            return None
        
        question_type = question_profile.get("type", "general")
        topics = question_profile.get("topics") or set()
        question_lower = question_profile.get("question_lower") or ""
        
        subject_display = question_profile.get("subject_display")
        if not subject_display and facts:
            subject_display = facts[0]["member"].split()[0] if facts[0]["member"] else None
        subject_phrase = subject_display or "They"
        
        # Check for unsupported question types (how many, how much, etc.)
        if any(phrase in question_lower for phrase in ["how many", "how much", "count", "number of"]):
            # Can't answer counting questions from unstructured data
            return None
        
        # Handle restaurant-related questions with conversational phrasing
        if "restaurants" in topics or "restaurant" in question_lower:
            restaurant_names = self._unique_preserve_order([name for fact in facts for name in fact["restaurants"]])
            if restaurant_names:
                rest_phrase = self._format_list(restaurant_names)
                # Check if asking about favorites/preferences
                if any(word in question_lower for word in ["favorite", "favourite", "prefer"]):
                    return f"{subject_phrase} has mentioned dining at {rest_phrase}."
                # Check if asking what was mentioned
                elif any(word in question_lower for word in ["mentioned", "has", "did"]):
                    return f"{subject_phrase} has mentioned {rest_phrase}."
                else:
                    # Generic restaurant answer
                    return f"{subject_phrase} has requested reservations at {rest_phrase}."
        
        # Handle time-related questions conversationally
        if question_type == "time":
            time_phrases = self._unique_preserve_order([tp for fact in facts for tp in fact["time_phrases"]])
            if time_phrases:
                time_phrase = time_phrases[0]
                location_phrase = None
                if question_profile.get("locations"):
                    location_phrase = question_profile["locations"][0].title()
                else:
                    for fact in facts:
                        if fact["locations"]:
                            location_phrase = fact["locations"][0]
                            break
                if location_phrase:
                    return f"{subject_phrase} has planned a trip to {location_phrase} for {time_phrase}."
                return f"{subject_phrase} has planned it for {time_phrase}."
        
        # Handle location/where questions conversationally
        if question_type == "location":
            location_mentions = self._unique_preserve_order([loc for fact in facts for loc in fact["locations"]])
            if location_mentions:
                loc_phrase = self._format_list(location_mentions)
                # Check if asking "where is X going"
                if "going" in question_lower or "travel" in question_lower:
                    return f"{subject_phrase} is planning to visit {loc_phrase}."
                else:
                    return f"{subject_phrase} has mentioned {loc_phrase}."
        
        # Handle general travel topics
        if "travel" in topics:
            travel_locations = self._unique_preserve_order([loc for fact in facts for loc in fact["locations"]])
            if travel_locations:
                loc_phrase = self._format_list(travel_locations)
                return f"{subject_phrase} is planning trips to {loc_phrase}."
        
        # Fallback: Generate conversational sentences from facts
        sentences = []
        for fact in facts[:3]:  # Try up to 3 facts
            sentence = self._generate_fact_sentence(subject_display, fact)
            if sentence:
                sentences.append(sentence)
        return " ".join(sentences) if sentences else None

    def _unique_preserve_order(self, items: List[str]) -> List[str]:
        seen = set()
        ordered = []
        for item in items:
            if not item:
                continue
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(item)
        return ordered

    def _format_list(self, items: List[str]) -> str:
        items = [item for item in items if item]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"

    def _lowercase_first(self, text: str) -> str:
        if not text:
            return text
        stripped = text.strip()
        return stripped[0].lower() + stripped[1:] if len(stripped) > 1 else stripped.lower()

    def _normalize_command(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.strip().rstrip(".")
        if not cleaned:
            return ""
        return cleaned[0].lower() + cleaned[1:]

    def _clean_thanks_phrase(self, text: str) -> str:
        if not text:
            return ""
        stripped = text.strip().rstrip(".")
        lowered = stripped.lower()
        if lowered.startswith("thank you for"):
            return stripped[12:].strip()
        if lowered.startswith("thank you"):
            return stripped[9:].strip()
        return stripped

    def _generate_fact_sentence(self, subject_display: str, fact: Dict[str, Any]) -> str:
        subject_phrase = subject_display or fact.get("member") or "They"
        content = fact.get("content") or ""
        if not content:
            return ""
        
        # For requests, rephrase conversationally
        if fact.get("is_request"):
            # Extract key information for natural rephrasing
            if fact.get("restaurants"):
                rest_phrase = self._format_list(fact["restaurants"])
                return f"{subject_phrase} has requested a reservation at {rest_phrase}."
            elif fact.get("locations"):
                loc_phrase = self._format_list(fact["locations"])
                if fact.get("time_phrases"):
                    time_phrase = fact["time_phrases"][0]
                    return f"{subject_phrase} has planned a trip to {loc_phrase} for {time_phrase}."
                return f"{subject_phrase} has planned to visit {loc_phrase}."
            # Don't return generic request if no structured info found
        
        # For preferences, make it conversational
        if fact.get("is_preference"):
            statement = self._lowercase_first(content)
            return f"{subject_phrase} prefers {statement}."
        
        # For gratitude, skip it unless it has useful location info
        if fact.get("is_gratitude"):
            if fact.get("locations"):
                loc_phrase = self._format_list(fact["locations"])
                return f"{subject_phrase} visited {loc_phrase}."
            # Don't include generic gratitude messages
            return ""
        
        # Default: extract key info rather than quoting directly
        if fact.get("restaurants"):
            rest_phrase = self._format_list(fact["restaurants"])
            return f"{subject_phrase} mentioned {rest_phrase}."
        elif fact.get("locations"):
            loc_phrase = self._format_list(fact["locations"])
            return f"{subject_phrase} mentioned {loc_phrase}."
        
        # If no structured info and it's not a clear statement, don't use it
        return ""

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "total_messages": self.num_messages,
            "embedding_dimension": self.embeddings.shape[1] if self.embeddings is not None else 0,
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_db": "FAISS",
            "llm_model": "Gemini Pro",
            "api_keys_loaded": len(self.key_rotator.keys) if self.key_rotator else 0,
            "status": "ready" if self.index else "not_initialized",
            "models_dir": str(MODELS_DIR),
            "data_dir": str(DATA_DIR)
        }

