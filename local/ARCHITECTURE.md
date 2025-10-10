# 🏗️ BOCK Scraper - Architecture Documentation

Technical architecture and design documentation for developers.

---

## 📐 System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────┐
│                 Web Browser (Client)                 │
│                  http://localhost:5000               │
└───────────────────────┬─────────────────────────────┘
                        │
                        │ HTTP/REST API
                        ▼
┌─────────────────────────────────────────────────────┐
│              Flask Web Server (Backend)              │
│                   web_server.py                      │
├──────────────────┬──────────────┬───────────────────┤
│   Scraping       │  Conversion  │  AI Processing    │
│   Management     │  Pipeline    │  Engine           │
└──────────────────┴──────────────┴───────────────────┘
         │                 │                │
         ▼                 ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│   Scrapy    │  │    File     │  │  Transformers│
│   Engine    │  │  Converter  │  │  AI Models   │
└─────────────┘  └─────────────┘  └──────────────┘
         │                 │                │
         ▼                 ▼                ▼
┌─────────────────────────────────────────────────────┐
│              Local File System Storage               │
│  scraping_output/ | text_output/ | summary_output/  │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Component Breakdown

### 1. Frontend (index.html)

**Technology:** HTML5, CSS3, Vanilla JavaScript

**Key Components:**
- **Tab Navigation**: Three main sections (Scrape, Convert, AI)
- **Form Handling**: Input validation and submission
- **Real-Time Updates**: AJAX polling for status
- **Progress Visualization**: Dynamic progress bars
- **Log Streaming**: Color-coded, auto-scrolling logs

**API Endpoints Used:**
```javascript
POST /start_scraping        // Start scraping job
POST /stop_scraping         // Cancel scraping
GET  /get_status            // Poll scraping progress
POST /convert_to_text       // Start text conversion
GET  /conversion_status     // Poll conversion progress
POST /generate_summaries    // Start AI summarization
GET  /summarization_status  // Poll summarization progress
POST /list_bucket           // Browse S3 buckets
POST /download_file         // Download from S3
```

---

### 2. Backend Server (web_server.py)

**Technology:** Flask 2.3+, Threading

#### Core Classes

**`ScrapingJob`** (Lines 125-267)
```python
class ScrapingJob:
    - Manages SSH connection to EC2
    - Executes remote scraping commands
    - Streams logs in real-time
    - Handles job lifecycle
```

**Global State Variables:**
```python
scraping_active = False        # Scraping job running?
conversion_active = False      # Conversion running?
summarization_active = False   # AI processing running?
all_logs = []                  # Scraping logs
conversion_logs = []           # Conversion logs
summarization_logs = []        # AI logs
scraping_stats = {...}         # Statistics
```

#### Threading Model

**Scraping Thread:**
```python
# Created in ScrapingJob.start()
process_thread = threading.Thread(target=self._run_scraping)
- Connects to EC2 via SSH
- Streams stdout in real-time
- Updates global statistics
- Cleans up on completion
```

**Conversion Thread:**
```python
# Created in convert_to_text endpoint
thread = threading.Thread(
    target=_run_conversion,
    args=(source_session, target_bucket),
    daemon=True
)
```

**Summarization Thread:**
```python
# Created in generate_summaries endpoint
thread = threading.Thread(
    target=_run_summarization,
    args=(source_session, input_bucket, output_bucket),
    daemon=True
)
```

---

### 3. Scraping Engine (ec2_files/ultimate_scraper_v2.py)

**Architecture:** Multi-stage pipeline

#### Stage 1: Article Discovery (Lines 443-725)

**`ProvenScrapyArticleExtractor`**
```python
Uses Scrapy CrawlerProcess with custom spider:
1. Crawl homepage
2. Extract all links
3. Filter article URLs using heuristics
4. Request each article page
5. Extract content with trafilatura
6. Apply advanced filtering
7. Save verified articles as JSON
```

**Article Filtering Logic:**
```python
def is_article_page(url, title, content):
    # 1. URL Pattern Analysis
    article_patterns = ['/article/', '/news/', '/story/', ...]
    
    # 2. Title Analysis
    category_patterns = ['latest news', 'breaking news', ...]
    
    # 3. Content Analysis
    word_count = len(content.split())
    list_ratio = calculate_list_ratio(content)
    
    # 4. Scoring System
    article_score = calculate_score(url, title, content)
    
    # 5. Threshold Decision
    return article_score >= 40
```

#### Stage 2: Image Processing (Lines 62-441)

**`ProvenImageScraperPipeline`**
```python
Multi-fallback image extraction:
1. Try trafilatura.metadata.image (highest priority)
2. Try newspaper3k.top_image
3. Try BeautifulSoup with OpenGraph/Twitter Card
4. Score all found images (0-100)
5. Validate image dimensions
6. Download best image
7. Convert to optimized JPG
```

**Image Scoring Algorithm:**
```python
score = 50  # Base score

# Source bonuses
if source == "trafilatura_main": score += 30
if source == "newspaper_top": score += 25

# URL analysis
if "featured" in url: score += 20
if "logo" in url: score -= 25

# Final: max(0, min(100, score))
```

---

### 4. AI Summarization (summary/bocksummarizer-main/)

#### Text Summarization Pipeline

**`summarize_text.py`** - Core text processing
```python
def summarize_text(text, model_name):
    1. Load text from JSON
    2. Clean and normalize (remove extra whitespace)
    3. Chunk into 900-word segments
    4. Summarize each chunk (max_length=220)
    5. If multiple chunks, summarize the summaries
    6. Return final concise summary
```

**Model:** facebook/bart-large-cnn
- **Input**: Article text (any length)
- **Output**: 2-3 sentence summary
- **Processing**: Transformer-based seq2seq

#### Image Captioning Pipeline

**`summarize_all.py`** - Image caption generation
```python
def caption_image(image_path, model_name):
    1. Open image with PIL
    2. Convert to RGB format
    3. Pass through vision transformer
    4. Generate natural language caption
    5. Return generated text
```

**Model:** nlpconnect/vit-gpt2-image-captioning
- **Input**: JPG/PNG image
- **Output**: Natural language description
- **Processing**: Vision Transformer + GPT-2 decoder

---

## 🔄 Data Flow

### Scraping Workflow

```
User Input (URL + max_articles)
        ↓
    web_server.py
        ↓
    ScrapingJob.start()
        ↓
    SSH to EC2 / Local execution
        ↓
    ultimate_scraper_v2.py
        ↓
    ┌──────────────────┐
    │ Scrapy Discovery │ → Find article URLs
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │ Content Extract  │ → Trafilatura extraction
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │ Image Processing │ → Multi-source image fetch
    └────────┬─────────┘
             ↓
    Save to: scraping_output/session_XXXXX/
    - Article_Name/article.json
    - Article_Name/image.jpg
```

### Conversion Workflow

```
User Input (session_id)
        ↓
    convert_to_text endpoint
        ↓
    _run_conversion thread
        ↓
    For each JSON file:
        1. Read article.json
        2. Extract: title, content, url, date
        3. Format as plain text
        4. Write article.txt
        5. Copy image.jpg
        ↓
    Save to: text_output/session_XXXXX/
```

### AI Summarization Workflow

```
User Input (session_id)
        ↓
    generate_summaries endpoint
        ↓
    _run_summarization thread
        ↓
    Import summary modules
        ↓
    For each article folder:
        ├─ Process JSON:
        │   1. Read article.json
        │   2. Extract content
        │   3. Call summarize_text_content()
        │   4. Save article_text_summary.json
        │
        └─ Process Image:
            1. Read image.jpg
            2. Call caption_image()
            3. Save image_summary.json
        ↓
    Save to: summary_output/session_XXXXX/
```

---

## 📡 API Design

### RESTful Endpoints

#### Scraping
```python
POST /start_scraping
{
    "url": "https://example.com",
    "maxArticles": 10
}
→ Returns: {"message": "Scraping started", "sessionId": "session_XXX"}

GET /get_status
→ Returns: {
    "articlesFound": 5,
    "articlesSaved": 5,
    "imagesFound": 4,
    "progress": 75,
    "completed": false,
    "logs": [...]
}
```

#### Conversion
```python
POST /convert_to_text
{
    "sourceSession": "session_XXX"
}
→ Returns: {"message": "Conversion started successfully"}

GET /conversion_status
→ Returns: {
    "logs": [...],
    "isActive": true,
    "completed": false,
    "progress": 50
}
```

#### AI Summarization
```python
POST /generate_summaries
{
    "sourceSession": "session_XXX"
}
→ Returns: {"message": "Summarization started successfully"}

GET /summarization_status
→ Returns: {
    "textSummaries": 5,
    "imageSummaries": 5,
    "totalFolders": 5,
    "progress": 50,
    "completed": false
}
```

---

## 🔐 Security Considerations

### Input Validation
- URL validation before scraping
- Session ID sanitization
- File path validation
- Prevent directory traversal

### Credential Management
- SSH keys stored securely
- AWS credentials in environment variables
- Never commit credentials to git

### Resource Protection
- Thread daemon mode prevents hanging
- Timeout limits on HTTP requests
- Maximum file size limits
- Log size limits (500 entries max)

---

## 🎯 Design Patterns

### Observer Pattern
```python
# Real-time log updates
def add_log(message, log_type):
    all_logs.append(log_entry)  # Update global state
    # Frontend polls /get_status to observe changes
```

### Strategy Pattern
```python
# Multiple image extraction strategies
class ProvenImageScraperPipeline:
    def extract_images_trafilatura()  # Strategy 1
    def extract_images_newspaper()    # Strategy 2
    def extract_images_beautifulsoup()  # Strategy 3
```

### Template Method Pattern
```python
# Common scraping flow with customizable steps
def run_ultimate_scraping_v2():
    # Phase 1: Article extraction (customizable)
    articles = self.run_proven_article_extraction()
    
    # Phase 2: Image processing (customizable)
    successful = self.run_proven_image_processing(articles)
    
    # Phase 3: Summary generation (fixed)
    self.create_ultimate_summary_v2(successful)
```

---

## 🧩 Module Dependencies

```
web_server.py
├── Flask (web framework)
├── paramiko (SSH for EC2)
├── boto3 (AWS S3 integration)
├── threading (async processing)
└── summary/bocksummarizer-main/
    ├── transformers (AI models)
    ├── torch (deep learning)
    └── PIL (image processing)

ec2_files/ultimate_scraper_v2.py
├── scrapy (web crawling)
├── trafilatura (content extraction)
├── newspaper3k (article parsing)
├── beautifulsoup4 (HTML parsing)
├── lxml (XML processing)
└── Pillow (image processing)
```

---

## 📊 State Management

### Global State Variables

**Scraping State:**
```python
scraping_active: bool          # Is scraping running?
current_job: ScrapingJob      # Active job object
all_logs: List[dict]          # Log entries
scraping_stats: dict          # Progress metrics
```

**Conversion State:**
```python
conversion_active: bool        # Is conversion running?
conversion_logs: List[dict]   # Log entries
conversion_stats: dict        # Status and progress
```

**Summarization State:**
```python
summarization_active: bool     # Is AI running?
summarization_logs: List[dict] # Log entries
summarization_stats: dict      # Metrics
```

### Thread Safety

**Current Approach:** Single-threaded Flask with background threads
- Main thread handles HTTP requests
- Background threads for long-running operations
- Global state protected by GIL (Global Interpreter Lock)

**Limitations:**
- Only one scraping job at a time
- Only one conversion at a time
- Only one AI job at a time

**Future Enhancement:** Queue-based task system with worker pool

---

## 🔧 Configuration System

### Static Configuration (web_server.py)
```python
Lines 31-43: EC2 and S3 configuration
- EC2_HOST: Remote server IP
- EC2_KEY_PATH: SSH key location
- S3_BUCKET_NAME: Storage buckets
- AWS credentials
```

### Dynamic Configuration (Runtime)
```python
# Output directories
LOCAL_OUTPUT_DIR = os.path.join(...)
LOCAL_TEXT_OUTPUT_DIR = os.path.join(...)
LOCAL_SUMMARY_OUTPUT_DIR = os.path.join(...)

# Created on server startup
os.makedirs(LOCAL_OUTPUT_DIR, exist_ok=True)
```

---

## 🎨 Frontend Architecture

### Component Structure

```
index.html
├── Header Section
│   ├── Logo display
│   ├── S3 Bucket dropdown
│   └── Bucket browser modal
│
├── Tab Navigation
│   ├── Tab 1: Scrape Articles
│   ├── Tab 2: Convert to Text
│   └── Tab 3: AI Summarization
│
├── Tab Content Areas
│   ├── Forms (input controls)
│   ├── Statistics (real-time metrics)
│   ├── Progress bars
│   └── Log containers
│
└── Modal Dialogs
    └── S3 File Browser
```

### State Management (JavaScript)

```javascript
// Global state
let scrapingActive = false;
let startTime = null;
let timerInterval = null;
let logPollingInterval = null;
let lastLogIndex = 0;

// Polling mechanism
function startLogPolling() {
    logPollingInterval = setInterval(async () => {
        const data = await fetch('/get_status').then(r => r.json());
        updateUI(data);
    }, 2000);  // Poll every 2 seconds
}
```

---

## 🗃️ Data Models

### Article Model (JSON)
```python
{
    "url": str,                    # Source URL
    "title": str,                  # Article title
    "content": str,                # Full text content
    "author": str | None,          # Author name
    "date": str | None,            # Publication date
    "description": str | None,     # Meta description
    "extraction_method": str,      # How it was extracted
    "scraped_timestamp": float,    # When scraped
    "word_count": int,             # Content length
    "is_verified_article": bool,   # Passed filtering?
    "image_path": str | None,      # Path to image
    "image_saved": bool,           # Image downloaded?
    "image_info": {                # Image metadata
        "url": str,
        "score": int,
        "source": str
    }
}
```

### Statistics Model
```python
scraping_stats = {
    "articlesFound": int,      # Articles discovered
    "articlesSaved": int,      # Articles saved
    "imagesFound": int,        # Images downloaded
    "progress": int,           # 0-100%
    "completed": bool,         # Job finished?
    "sessionId": str | None    # Session identifier
}
```

---

## 🔄 Processing Pipelines

### Scraping Pipeline

```
1. URL Input
   ↓
2. Scrapy Crawler
   - Parse homepage HTML
   - Extract all <a> links
   - Filter by article patterns
   - Create Request objects
   ↓
3. Article Processing
   - Download article HTML
   - Extract with trafilatura
   - Parse metadata
   - Validate content length
   - Apply article detection
   ↓
4. Image Extraction
   - Try trafilatura.metadata.image
   - Try newspaper3k.top_image
   - Try BeautifulSoup extraction
   - Score all candidates
   - Select best image
   - Validate size
   - Download and convert
   ↓
5. Save Output
   - Create folder: Article_Title/
   - Save: article.json
   - Save: image.jpg
```

### AI Processing Pipeline

```
1. Session Input
   ↓
2. Folder Iteration
   For each article folder:
   ↓
3. Text Processing
   - Read article.json
   - Extract content field
   - Check word count
   - Chunk if needed (900 words/chunk)
   - Summarize with BART
   - Save article_text_summary.json
   ↓
4. Image Processing
   - Read image.jpg
   - Convert to RGB
   - Pass through ViT-GPT2
   - Extract generated_text
   - Save image_summary.json
   ↓
5. Statistics Update
   - Increment counters
   - Update progress
   - Log completion
```

---

## 🔍 Error Handling Strategy

### Hierarchical Error Handling

**Level 1: Try-Except Blocks**
```python
try:
    risky_operation()
except SpecificError as e:
    log_error(e)
    use_fallback()
```

**Level 2: Fallback Mechanisms**
```python
# Image extraction
images = extract_trafilatura(url)
if not images:
    images = extract_newspaper(url)  # Fallback 1
if not images:
    images = extract_beautifulsoup(url)  # Fallback 2
```

**Level 3: Graceful Degradation**
```python
# AI summarization
try:
    summary = ai_model(text)
except:
    summary = text[:500] + "..."  # Excerpt fallback
```

---

## 📈 Performance Optimization

### Caching Strategy
- **HTTP Connection Pooling**: Reuse connections
- **Retry Strategy**: 3 retries with exponential backoff
- **Model Caching**: Load AI models once, reuse multiple times

### Concurrent Processing
```python
# Scrapy settings
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 0.5
RANDOMIZE_DOWNLOAD_DELAY = True
```

### Memory Management
```python
# Log rotation
if len(all_logs) > 500:
    all_logs.pop(0)  # Remove oldest

# Temporary file cleanup
finally:
    if temp_file and os.path.exists(temp_file):
        os.unlink(temp_file)
```

---

## 🧪 Testing Approach

### Manual Testing
- Start server → check startup
- Scrape 3 articles → verify output
- Convert to text → check text files
- Run AI → verify summaries

### Edge Cases Handled
- Empty articles → filtered out
- No images found → graceful skip
- Very short text → excerpt fallback
- Model errors → fallback summaries
- Network errors → retry mechanism
- Invalid JSON → error logging

---

## 🚀 Deployment Considerations

### Local Deployment
- **Pros**: Simple, no cloud costs, full control
- **Cons**: Limited to one machine, no high availability

### Production Hardening
- Use production WSGI server (Gunicorn/uWSGI)
- Set debug=False in Flask
- Implement proper logging
- Add authentication
- Use reverse proxy (nginx)
- SSL/TLS certificates

---

## 🔮 Future Architecture Plans

### Potential Improvements
1. **Queue System**: RabbitMQ/Celery for job management
2. **Database**: PostgreSQL for metadata storage
3. **Caching**: Redis for session data
4. **Microservices**: Separate scraper/AI services
5. **Load Balancing**: Multiple worker instances
6. **API Gateway**: Standardized API layer

---

## 📝 Code Organization

### File Responsibilities

| File | Responsibility | Lines |
|------|----------------|-------|
| `web_server.py` | Flask app, API endpoints, threading | ~1000 |
| `index.html` | UI, user interactions, AJAX | ~1400 |
| `ec2_files/ultimate_scraper_v2.py` | Scraping logic | ~1050 |
| `summary/.../summarize_all.py` | AI text+image processing | ~425 |
| `summary/.../summarize_text.py` | AI text-only processing | ~345 |

### Key Functions

**Web Server:**
- `start_scraping()` - Initiate scraping job
- `get_status()` - Return current status
- `_run_conversion()` - Convert JSON to text
- `_run_summarization()` - Run AI processing

**Scraper:**
- `run_ultimate_scraping_v2()` - Main entry point
- `run_proven_article_extraction()` - Discover articles
- `run_proven_image_processing()` - Download images
- `is_article_page()` - Filter non-articles

**AI:**
- `summarize_text_content()` - Text summarization
- `caption_image()` - Image captioning
- `list_folders()` - S3/local folder listing
- `download_file()` - File retrieval

---

## 🎓 Learning Resources

### Understanding the Codebase
1. Start with `web_server.py` - entry point
2. Trace a scraping request through the code
3. Examine `ultimate_scraper_v2.py` - core logic
4. Review `summarize_all.py` - AI integration

### External Documentation
- [Flask Quickstart](https://flask.palletsprojects.com/en/latest/quickstart/)
- [Scrapy Tutorial](https://docs.scrapy.org/en/latest/intro/tutorial.html)
- [Transformers Pipeline](https://huggingface.co/docs/transformers/main_classes/pipelines)
- [Trafilatura Usage](https://trafilatura.readthedocs.io/)

---

**📘 For more details, see the inline code comments!**

