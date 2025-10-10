# 🚀 BOCK Scraper - Complete Setup Guide

**Step-by-step guide to get BOCK Scraper running on your local machine.**

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [First Run](#first-run)
4. [Workflow Tutorial](#workflow-tutorial)
5. [File Locations](#file-locations)
6. [Common Issues](#common-issues)

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux, or macOS
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended for AI models)
- **Storage**: 10GB free space (for AI models and data)
- **Internet**: Required for initial setup and model downloads

### Recommended Setup
- **RAM**: 16GB+
- **CPU**: Multi-core processor (4+ cores)
- **SSD**: For faster processing
- **Internet**: Broadband connection (for model downloads)

---

## 🔧 Installation Steps

### Step 1: Install Python

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer and **check "Add Python to PATH"**
3. Verify installation:
   ```bash
   python --version
   ```

**Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS:**
```bash
brew install python3
```

---

### Step 2: Clone or Download the Project

**Option A: Using Git**
```bash
git clone https://github.com/your-username/bock-scraper.git
cd bock-scraper
```

**Option B: Download ZIP**
1. Download the project ZIP file
2. Extract to your desired location
3. Open terminal/command prompt in the extracted folder

---

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python -m venv web_venv

# Activate it
# Windows:
web_venv\Scripts\activate

# Linux/Mac:
source web_venv/bin/activate
```

**You should see `(web_venv)` in your terminal prompt.**

---

### Step 4: Install All Dependencies

**Install in this order:**

```bash
# 1. Web server dependencies (Flask, etc.)
pip install -r requirements.txt

# 2. Scraper dependencies (Scrapy, etc.)
pip install -r ec2_files/requirements.txt

# 3. AI dependencies (transformers, torch)
pip install -r summary/bocksummarizer-main/requirements.txt
```

**This will take 5-10 minutes** depending on your internet speed.

---

### Step 5: Create Output Directories

The server creates these automatically, but you can create them manually:

```bash
mkdir scraping_output
mkdir text_output
mkdir summary_output
mkdir tmp
```

---

## 🎮 First Run

### Start the Web Server

**With virtual environment activated:**
```bash
python web_server.py
```

**You should see:**
```
================================================================================
BOCK SCRAPER - WEB INTERFACE
================================================================================
Open your browser and go to: http://localhost:5000
EC2 Instance: 54.82.140.246
S3 Bucket: bockscraper
================================================================================
```

**Open your browser to:**
```
http://localhost:5000
```

---

## 📚 Workflow Tutorial

### Example: Scraping BBC News

**1. Start Scraping**
- URL: `https://www.bbc.com/news`
- Max Articles: `10`
- Click: **"Start Scraping"**

**Expected Time:** ~2-3 minutes for 10 articles

**Output Location:**
```
scraping_output/session_1760105226/
├── Article_1/
│   ├── article.json  (full article data)
│   └── image.jpg     (article image)
├── Article_2/
│   ├── article.json
│   └── image.jpg
└── ...
```

**2. Convert to Text** (Optional)
- Session ID: `session_1760105226` (from step 1)
- Click: **"Convert to Text"**

**Expected Time:** ~10-30 seconds

**Output Location:**
```
text_output/session_1760105226/
├── Article_1/
│   ├── article.txt   (readable text)
│   └── image.jpg     (copied)
└── ...
```

**3. Generate AI Summaries** (Optional)
- Session ID: `session_1760105226` (from step 1)
- Click: **"Generate AI Summaries"**

**Expected Time:**
- First run: 5-10 minutes (downloads models)
- Subsequent runs: 2-5 minutes

**Output Location:**
```
summary_output/session_1760105226/
├── Article_1/
│   ├── article_text_summary.json  (AI summary)
│   └── image_summary.json         (AI caption)
└── ...
```

---

## 📁 File Locations

### Where Everything is Saved

**All files are saved in the project directory:**

```
C:\Your\Project\Path\bock-scraper\
│
├── scraping_output\              ← 📦 Scraped articles
│   └── session_1760105226\
│       └── Article_Name\
│           ├── article.json
│           └── image.jpg
│
├── text_output\                  ← 📄 Text conversions
│   └── session_1760105226\
│       └── Article_Name\
│           └── article.txt
│
├── summary_output\               ← 🤖 AI summaries
│   └── session_1760105226\
│       └── Article_Name\
│           ├── article_text_summary.json
│           └── image_summary.json
│
└── tmp\                          ← 🗑️ Temporary files (auto-deleted)
```

**Session IDs** are timestamps (e.g., `session_1760105226` = scraped at timestamp 1760105226)

---

## 🐛 Common Issues

### Issue 1: "Python not found"
**Solution:**
- Make sure Python is installed
- Check it's added to PATH
- Restart your terminal

### Issue 2: "Port 5000 already in use"
**Solution:**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID [PID_NUMBER] /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9

# Or change port in web_server.py (line 1015):
app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
```

### Issue 3: "Module not found" errors
**Solution:**
Make sure virtual environment is activated and all dependencies installed:
```bash
# Activate venv
web_venv\Scripts\activate  # Windows
source web_venv/bin/activate  # Linux/Mac

# Install all dependencies again
pip install -r requirements.txt
pip install -r ec2_files/requirements.txt
pip install -r summary/bocksummarizer-main/requirements.txt
```

### Issue 4: AI models download very slowly
**Solution:**
- First run downloads ~2GB of models (one-time only)
- Models are cached in `~/.cache/huggingface/`
- Ensure stable internet connection
- Be patient - it only happens once!

### Issue 5: "index out of range in self" during summarization
**Solution:**
- This happens with very short articles
- System now automatically uses excerpt fallbacks
- No action needed - summaries still generated

### Issue 6: Scraping returns no articles
**Solution:**
- Some websites block scrapers
- Try a different news website
- Check if the website is accessible in your browser
- Some sites require JavaScript (not supported)

---

## 🔍 Testing

### Quick Test

**1. Test the scraper (small batch):**
```bash
python web_server.py
# In browser: Scrape 3-5 articles from https://www.bbc.com/news
```

**2. Test conversion:**
```bash
# Use the session ID from step 1
# Click "Convert to Text"
# Check text_output/ folder
```

**3. Test AI (first run will download models):**
```bash
# Use the session ID from step 1
# Click "Generate AI Summaries"
# Wait 5-10 minutes for model downloads
# Check summary_output/ folder
```

---

## 🚀 Production Deployment

### For Long-Running Use

**Option 1: Use screen/tmux (Linux)**
```bash
screen -S bock-scraper
python web_server.py
# Press Ctrl+A then D to detach
```

**Option 2: Use nohup (Linux/Mac)**
```bash
nohup python web_server.py > server.log 2>&1 &
```

**Option 3: Windows Service**
Use [NSSM](https://nssm.cc/) to create a Windows service

**Option 4: Docker** (Advanced)
Create a Dockerfile for containerized deployment

---

## 🎨 Customization

### Change Output Directories

Edit `web_server.py` (if using local setup, edit `local_web_server.py`):
```python
LOCAL_OUTPUT_DIR = "C:/path/to/your/output"
LOCAL_TEXT_OUTPUT_DIR = "C:/path/to/text"
LOCAL_SUMMARY_OUTPUT_DIR = "C:/path/to/summaries"
```

### Change AI Models

Edit in `web_server.py` or the summarization functions:
```python
text_model = "facebook/bart-large-cnn"     # Or "t5-base", "google/pegasus-xsum"
image_model = "nlpconnect/vit-gpt2-image-captioning"  # Or other vision models
```

### Adjust Scraping Limits

In the web interface:
- Max articles: 1-500
- Default concurrent requests: 50 (configured in scraper)

---

## 📊 Monitoring

### View Logs

**Real-time logs:**
- Visible in the web interface log panel
- Color-coded by severity (info, success, warning, error)

**File logs:**
```
ultimate_scraper_v2.log  (created when running scraper directly)
```

### Check Storage Usage

```bash
# Windows
dir scraping_output /s

# Linux/Mac
du -sh scraping_output/
```

---

## ⚡ Performance Tips

1. **Close other applications** when running AI summarization
2. **Use SSD** for faster file operations
3. **Increase max articles gradually** - start with 10-20, then scale up
4. **Process one session at a time** for AI summarization
5. **Clear old sessions** periodically to free up space

---

## 🔄 Updates

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
pip install --upgrade -r ec2_files/requirements.txt
pip install --upgrade -r summary/bocksummarizer-main/requirements.txt
```

### Update Models
```bash
# Clear model cache to force re-download
rm -rf ~/.cache/huggingface/hub/
# Models will re-download on next AI run
```

---

## 💾 Backup

### What to Backup
```
scraping_output/   ← Your scraped data
text_output/       ← Converted text files
summary_output/    ← AI summaries
```

### What NOT to Backup
```
web_venv/          ← Virtual environment (recreate with pip)
tmp/               ← Temporary files
__pycache__/       ← Python cache
*.log              ← Log files
```

---

## 🎯 Next Steps

After successful setup:

1. ✅ Test with a small batch (3-5 articles)
2. ✅ Verify all three tabs work (Scrape, Convert, AI)
3. ✅ Check output folders contain files
4. ✅ Try different news websites
5. ✅ Experiment with larger batches (20-50 articles)

---

**🎉 You're ready to scrape! Happy data collecting!**

