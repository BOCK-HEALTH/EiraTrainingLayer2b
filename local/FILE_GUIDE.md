# 📂 BOCK Scraper - Complete File Guide

**Comprehensive guide to every file in the project and what it does.**

---

## 🚀 Core Application Files

### `web_server.py` ⭐ **MAIN ENTRY POINT**
**Lines:** ~1000  
**Purpose:** Flask backend server - this is what you run with `python web_server.py`

**What it does:**
- Serves the web interface at http://localhost:5000
- Handles all API endpoints for scraping, conversion, and AI
- Manages background threads for processing
- Handles S3 integration (optional cloud mode)
- Real-time log streaming and progress tracking

**Key Functions:**
- `start_scraping()` - Initiates scraping jobs
- `convert_to_text()` - Converts JSON to readable text
- `generate_summaries()` - Runs AI summarization
- `get_status()` - Returns current progress
- `list_bucket()` - S3 bucket browser

**Configuration (Lines 31-43):**
- EC2 connection details
- S3 bucket names
- AWS credentials

---

### `index.html` ⭐ **WEB INTERFACE**
**Lines:** ~1400  
**Purpose:** Beautiful web UI that users interact with

**What it contains:**
- Modern gradient design with responsive layout
- Three main tabs:
  - **Tab 1**: Scrape Articles (form + progress)
  - **Tab 2**: Convert to Text (session selection)
  - **Tab 3**: AI Summarization (AI controls)
- Real-time statistics dashboard
- Color-coded log viewer
- S3 bucket browser modal
- JavaScript for AJAX polling and UI updates

**Key Features:**
- Progress bars with percentages
- Live log streaming
- Tab switching
- Form validation
- File download functionality

---

### `Health Text-01.png` 🎨 **LOGO**
**Purpose:** BOCK Scraper logo displayed in the web interface header

---

## 🕷️ Scraping Engine Files

### `ec2_files/ultimate_scraper_v2.py` ⭐ **SCRAPER ENGINE**
**Lines:** ~1050  
**Purpose:** The core scraping logic - discovers articles and downloads images

**What it does:**
- Uses Scrapy CrawlerProcess to discover article URLs
- Extracts article content with trafilatura
- Downloads and processes images
- Applies intelligent filtering to avoid category pages
- Saves articles as JSON with metadata
- Converts images to optimized JPG format

**Key Classes:**
- `UltimateScraperV2` - Main orchestrator
- `ProvenScrapyArticleExtractor` - Article discovery
- `ProvenImageScraperPipeline` - Image processing

**Output Format:**
```
Article_Title_With_Underscores/
├── article.json  (full article data)
└── image.jpg     (hero image)
```

**Command-line Usage:**
```bash
python ec2_files/ultimate_scraper_v2.py "https://www.bbc.com/news" --max-articles 10 --output scraping_output/session_XXX
```

---

### `ec2_files/requirements.txt` 📦 **SCRAPER DEPENDENCIES**
**Purpose:** Python packages needed for the scraping engine

**Key Dependencies:**
- `scrapy>=2.11.0` - Web crawling framework
- `trafilatura>=1.6.0` - Content extraction
- `newspaper3k>=0.2.8` - Article parsing
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=4.9.0` - XML/HTML processing
- `Pillow>=10.0.0` - Image processing
- `aiohttp>=3.9.0` - Async HTTP
- `requests>=2.31.0` - HTTP library

---

## 🤖 AI Summarization Files

### `summary/bocksummarizer-main/summarize_all.py` ⭐ **AI PROCESSING**
**Lines:** ~425  
**Purpose:** Text summarization + image captioning using AI models

**What it does:**
- Loads Hugging Face transformers models
- Processes JSON files for text summarization
- Processes images for AI captioning
- Handles S3 or local file operations
- Implements fallback strategies for errors

**Key Functions:**
- `summarize_text_content(text, model)` - Generate text summary
- `caption_image(path, model)` - Generate image caption
- `list_folders(bucket, prefix)` - List S3/local folders
- `download_file(bucket, key, path)` - Download files
- `upload_bytes(bucket, key, bytes)` - Upload results

**AI Models Used:**
- Text: `facebook/bart-large-cnn` (BART model)
- Images: `nlpconnect/vit-gpt2-image-captioning` (ViT-GPT2)

---

### `summary/bocksummarizer-main/summarize_text.py` 📝 **TEXT-ONLY AI**
**Lines:** ~345  
**Purpose:** Simplified version for text summarization only (no image captioning)

**Use case:** When you only need text summaries without image processing

---

### `summary/bocksummarizer-main/requirements.txt` 📦 **AI DEPENDENCIES**
**Purpose:** AI model dependencies

**Key Dependencies:**
- `transformers>=4.44.0` - Hugging Face transformers
- `torch>=2.3.0` - PyTorch deep learning framework
- `accelerate>=0.33.0` - Model optimization
- `Pillow>=10.0.0` - Image processing
- `boto3>=1.34.0` - AWS SDK (for S3 operations)

**Note:** These are large packages (~3GB total with models)

---

### `summary/bocksummarizer-main/README.md` 📖 **AI MODULE DOCS**
**Purpose:** Documentation specifically for the AI summarization component

---

## 🔧 Configuration Files

### `requirements.txt` 📦 **WEB SERVER DEPENDENCIES**
**Lines:** 21  
**Purpose:** Python packages for Flask web server and AWS integration

**Key Dependencies:**
- `Flask>=2.3.0` - Web framework
- `flask-cors>=4.0.0` - CORS support
- `paramiko>=3.3.0` - SSH client (for EC2)
- `boto3>=1.28.0` - AWS S3 SDK
- `botocore>=1.31.0` - AWS core
- `pathlib2>=2.3.0` - Path utilities

---

### `s3_config.example.env` 🔐 **CONFIGURATION TEMPLATE**
**Lines:** 35  
**Purpose:** Example environment configuration for S3/AWS setup

**Contains:**
- S3 bucket configuration
- AWS credentials format
- Region settings
- Usage instructions

**Note:** This is a template - actual credentials go in `.env` (gitignored)

---

### `.gitignore` 🚫 **GIT IGNORE RULES**
**Purpose:** Tells Git which files NOT to commit

**Ignores:**
- `web_venv/` - Virtual environment
- `scraping_output/` - User data
- `text_output/` - User data  
- `summary_output/` - User data
- `tmp/` - Temporary files
- `*.log` - Log files
- `*.pem` - SSH keys
- `.env` - Credentials
- `__pycache__/` - Python cache

---

## 📚 Documentation Files

### `README.md` 📖 **MAIN DOCUMENTATION**
**Purpose:** Project overview, features, quick start guide (you're reading it!)

### `SETUP_GUIDE.md` 🛠️ **DETAILED SETUP**
**Purpose:** Step-by-step installation and configuration instructions

**Covers:**
- System requirements
- Installation steps
- First run tutorial
- Troubleshooting
- Performance tips

### `FEATURES.md` ✨ **FEATURE DOCUMENTATION**
**Purpose:** Comprehensive list of all capabilities

**Covers:**
- Scraping features
- AI features
- UI features
- Technical features
- Supported websites

### `ARCHITECTURE.md` 🏗️ **TECHNICAL DOCS**
**Purpose:** System architecture and technical design

**Covers:**
- System architecture diagram
- Component breakdown
- Data flow
- API design
- Threading model
- Performance optimization

### `QUICK_START.md` ⚡ **5-MINUTE GUIDE**
**Purpose:** Get running in 5 minutes

**Covers:**
- Minimal installation steps
- First scraping job
- Common issues

### `CONTRIBUTING.md` 🤝 **CONTRIBUTION GUIDE**
**Purpose:** Guidelines for contributors

**Covers:**
- Code of conduct
- How to contribute
- Coding standards
- Pull request process

### `DEPLOYMENT_GUIDE.md` 🌍 **CLOUD DEPLOYMENT** (Legacy)
**Purpose:** Guide for EC2/S3 cloud deployment

**Note:** This is for advanced cloud setup. Most users can ignore this.

### `LICENSE` 📄 **MIT LICENSE**
**Purpose:** Open source license (MIT)

---

## 📦 Output Directories

### `scraping_output/` 🕷️ **SCRAPED DATA**
**Created by:** Web scraper  
**Structure:**
```
scraping_output/
└── session_1760105226/
    ├── Article_Title_1/
    │   ├── article.json  (full article + metadata)
    │   └── image.jpg     (article image)
    ├── Article_Title_2/
    └── ...
```

**File Contents:**
- `article.json` - Full article text, metadata, extraction info
- `image.jpg` - Optimized article image (converted to JPG)

---

### `text_output/` 📄 **TEXT CONVERSIONS**
**Created by:** Text converter  
**Structure:**
```
text_output/
└── session_1760105226/
    ├── Article_Title_1/
    │   ├── article.txt   (readable text file)
    │   └── image.jpg     (copied from scraping_output)
    └── ...
```

**File Contents:**
- `article.txt` - Human-readable article with title, date, url, content
- `image.jpg` - Copy of the article image

---

### `summary_output/` 🤖 **AI SUMMARIES**
**Created by:** AI summarization  
**Structure:**
```
summary_output/
└── session_1760105226/
    ├── Article_Title_1/
    │   ├── article_text_summary.json   (AI summary of text)
    │   └── image_summary.json          (AI caption of image)
    └── ...
```

**File Contents:**
- `article_text_summary.json` - AI-generated concise summary
- `image_summary.json` - AI-generated image description

---

### `tmp/` 🗑️ **TEMPORARY FILES**
**Created by:** AI processing  
**Purpose:** Temporary storage during AI processing

**Contents:**
- Downloaded files from S3 (if using cloud mode)
- Temporary processing files
- Auto-deleted after processing

**Note:** This folder is automatically cleaned up

---

## 📊 Generated Files

### `ultimate_scraper_v2.log` 📋 **SCRAPER LOG**
**Created by:** Running scraper directly  
**Purpose:** Detailed scraping logs

**Contains:**
- Timestamp for each operation
- Articles discovered and saved
- Images processed
- Errors and warnings
- Performance metrics

---

### `ultimate_scraper_v2_summary.json` 📊 **SCRAPING SUMMARY**
**Created by:** Scraper after completion  
**Purpose:** Session performance summary

**Contains:**
```json
{
  "ultimate_scraper_v2_session": {
    "homepage_url": "https://...",
    "timestamp": "2025-10-10 19:38:55",
    "total_time_seconds": 107.11
  },
  "performance_metrics": {
    "articles_with_images": 23,
    "success_rate": "100.0%",
    "processing_speed": "0.21 articles/second"
  }
}
```

---

## 🔧 Utility Files

### `copy_from_ec2.py` 🔄 **EC2 FILE COPIER**
**Purpose:** Copy files from EC2 instance to local machine

**Use case:** 
- Debugging EC2 setup
- Downloading scraper scripts from EC2
- Backup purposes

**Note:** Only needed if using EC2 mode

---

## ❌ Unused/Legacy Files

### `ultimate_scraper_v2.py` (Root folder)
**Status:** ⚠️ NOT USED in current setup  
**Note:** Uses hardcoded path `E:\BOCK\image\images` - ignore this file  
**Use instead:** `ec2_files/ultimate_scraper_v2.py`

### `local_index.html` 
**Status:** ⚠️ NOT USED  
**Note:** Separate UI for local mode, but `index.html` is used instead

### `local_web_server.py`
**Status:** ❌ DELETED  
**Note:** Was alternative local-only server, integrated into web_server.py

---

## 🎯 Quick Reference

### "Which file should I edit for..."

**Change UI appearance?**
→ `index.html` (CSS styles at top)

**Change scraping logic?**
→ `ec2_files/ultimate_scraper_v2.py`

**Change AI models?**
→ `web_server.py` (lines 632-633) or `summary/bocksummarizer-main/summarize_all.py`

**Change API endpoints?**
→ `web_server.py` (search for `@app.route`)

**Change output folders?**
→ `web_server.py` (lines 29-32 if using local mode)

**Add new dependencies?**
→ Update respective `requirements.txt` files

---

## 📊 File Size Reference

| File | Size | Purpose |
|------|------|---------|
| `web_server.py` | ~50KB | Backend logic |
| `index.html` | ~50KB | Frontend UI |
| `ec2_files/ultimate_scraper_v2.py` | ~45KB | Scraping engine |
| `summary/.../summarize_all.py` | ~15KB | AI processing |
| `requirements.txt` | ~1KB | Dependencies list |

**Total Project Size:** ~200KB (code only)  
**With Dependencies:** ~3GB (includes AI models)  
**With Sample Data:** Variable (depends on usage)

---

## 🔄 File Dependencies

```
web_server.py
├── Imports: Flask, boto3, paramiko, threading
├── Serves: index.html
├── Uses: summary/bocksummarizer-main/summarize_all.py
└── Creates: scraping_output/, text_output/, summary_output/

index.html
├── Loaded by: web_server.py
├── Calls APIs: /start_scraping, /get_status, etc.
└── Displays: Health Text-01.png

ec2_files/ultimate_scraper_v2.py
├── Imports: scrapy, trafilatura, newspaper, BeautifulSoup
├── Called by: web_server.py (via subprocess)
└── Creates: scraping_output/session_XXX/

summary/bocksummarizer-main/summarize_all.py
├── Imports: transformers, torch, PIL, boto3
├── Called by: web_server.py (imported in _run_summarization)
└── Creates: summary_output/session_XXX/
```

---

## 🎯 File Checklist for GitHub

### ✅ Include in Repository
- ✅ `web_server.py` - Core application
- ✅ `index.html` - UI
- ✅ `Health Text-01.png` - Logo
- ✅ All `requirements.txt` files - Dependencies
- ✅ `ec2_files/ultimate_scraper_v2.py` - Scraper
- ✅ `summary/bocksummarizer-main/` - AI code
- ✅ All documentation (README, SETUP_GUIDE, etc.)
- ✅ `.gitignore` - Git ignore rules
- ✅ `LICENSE` - License file
- ✅ `s3_config.example.env` - Config template

### ❌ Exclude from Repository (.gitignore)
- ❌ `web_venv/` - Virtual environment (recreate with pip)
- ❌ `scraping_output/` - User data
- ❌ `text_output/` - User data
- ❌ `summary_output/` - User data
- ❌ `tmp/` - Temporary files
- ❌ `*.log` - Log files
- ❌ `*.pem` - SSH keys (sensitive!)
- ❌ `.env` - Credentials (sensitive!)
- ❌ `__pycache__/` - Python cache
- ❌ `ultimate_scraper_v2_summary.json` - Session file

---

## 📋 File Manifest

### Production Files (Keep These)
```
✅ web_server.py                 Main backend
✅ index.html                    Main UI
✅ Health Text-01.png            Logo
✅ requirements.txt              Web deps
✅ ec2_files/ultimate_scraper_v2.py   Scraper
✅ ec2_files/requirements.txt    Scraper deps
✅ summary/bocksummarizer-main/  AI code
✅ .gitignore                    Git rules
✅ LICENSE                       License
✅ README.md                     Main docs
✅ SETUP_GUIDE.md               Setup docs
✅ FEATURES.md                   Feature list
✅ ARCHITECTURE.md               Tech docs
✅ QUICK_START.md               Quick guide
✅ CONTRIBUTING.md               Contrib guide
✅ FILE_GUIDE.md                This file
```

### Development Files (Optional)
```
⚠️ DEPLOYMENT_GUIDE.md          EC2/S3 deployment (advanced)
⚠️ copy_from_ec2.py             EC2 utility (advanced)
⚠️ s3_config.example.env        Config template
```

### Legacy/Unused Files (Can Delete)
```
❌ ultimate_scraper_v2.py       (Root - uses wrong paths)
❌ local_index.html             (Replaced by index.html)
❌ local_web_server.py          (Deleted - integrated into web_server.py)
```

---

## 🎓 Learning Path

### For New Users
1. Read: `README.md` - Overview
2. Follow: `QUICK_START.md` - Get running
3. Use: Web interface - Hands-on learning

### For Developers
1. Read: `ARCHITECTURE.md` - Understand design
2. Study: `web_server.py` - Backend logic
3. Study: `ec2_files/ultimate_scraper_v2.py` - Scraping logic
4. Read: `CONTRIBUTING.md` - Contribution guide

### For Advanced Users
1. Read: `FEATURES.md` - All capabilities
2. Study: `summary/bocksummarizer-main/` - AI code
3. Read: `DEPLOYMENT_GUIDE.md` - Cloud deployment

---

## 🔍 Quick File Lookup

**"Where is the scraping logic?"**  
→ `ec2_files/ultimate_scraper_v2.py`

**"Where is the AI code?"**  
→ `summary/bocksummarizer-main/summarize_all.py`

**"Where are scraped articles saved?"**  
→ `scraping_output/session_XXXXX/`

**"How do I change the UI?"**  
→ Edit `index.html`

**"How do I add a new API endpoint?"**  
→ Add to `web_server.py`

**"Where are AI models stored?"**  
→ `~/.cache/huggingface/hub/` (auto-downloaded)

**"How do I configure S3?"**  
→ `web_server.py` lines 31-43

---

**💡 Need help? Check the relevant documentation file or open an issue on GitHub!**

