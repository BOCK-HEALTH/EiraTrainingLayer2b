# BOCK Scraper - Local Setup Guide

This guide will help you set up and run the BOCK Scraper system completely locally on your machine.

## Overview

The system has three main components:
1. **Web Scraper** - Scrapes articles and images from news websites
2. **Text Converter** - Converts JSON files to plain text format
3. **AI Summarizer** - Generates AI summaries for text and image captions

Everything runs locally and saves to local folders:
- `scraping_output/` - Scraped articles and images
- `text_output/` - Converted text files
- `summary_output/` - AI-generated summaries

## Prerequisites

- Python 3.8 or higher
- At least 4GB of free disk space (for AI models)
- Internet connection (for downloading AI models on first run)

## Installation

### Step 1: Install Dependencies

Open a terminal/command prompt in the project folder and run:

```bash
pip install -r requirements.txt
```

**Note:** This may take several minutes as it downloads all required packages including the AI/ML libraries.

### Step 2: Verify Installation

Check that all components are installed:

```bash
python -c "import flask, transformers, scrapy, PIL; print('All packages installed successfully!')"
```

## Running the System

### Start the Web Server

Run the local web server:

```bash
python web_server_local.py
```

You should see:
```
================================================================================
BOCK SCRAPER - LOCAL WEB INTERFACE
================================================================================
Open your browser and go to: http://localhost:5000
Scraping output: scraping_output
Text output: text_output
Summary output: summary_output
================================================================================
```

### Open the Web Interface

1. Open your web browser
2. Go to: `http://localhost:5000`
3. You'll see the BOCK Scraper control panel

## Using the Interface

### Tab 1: Scrape Articles

1. Enter a website URL (e.g., `https://www.bbc.com/news`)
2. Set the number of articles to scrape (default: 10)
3. Click "Start Scraping"
4. Watch the real-time logs and progress
5. When complete, note the Session ID (e.g., `session_1234567890`)

**Output:** Files are saved to `scraping_output/session_XXXXX/Article_Title/`
- `article.json` - Article content and metadata
- `image.jpg` - Main article image

### Tab 2: Convert to Text

1. Enter the Session ID from scraping (e.g., `session_1234567890`)
2. Click "Convert to Text"
3. Watch the conversion progress

**Output:** Text files are saved to `text_output/session_XXXXX/Article_Title/`
- `article.txt` - Plain text version of the article

### Tab 3: AI Summarization

1. Enter the Session ID from scraping
2. Click "Generate AI Summaries"
3. **Important:** First run will download AI models (~2GB) - this may take 10-20 minutes
4. Subsequent runs will be much faster

**Output:** Summaries are saved to `summary_output/session_XXXXX/Article_Title/`
- `article_text_summary.json` - AI-generated text summary
- `image_summary.json` - AI-generated image caption

### View Files

Click the "📁 View Bucket" button in the top-right to browse:
- **bockscraper** - Scraped articles (scraping_output/)
- **bockscraper1** - Text files (text_output/)
- **bockscraper2** - AI summaries (summary_output/)

You can download any file directly from the interface.

## Output Structure

After scraping a session, your folder structure will look like this:

```
scraping_output/
└── session_1234567890/
    ├── Article_Title_1/
    │   ├── article.json
    │   └── image.jpg
    ├── Article_Title_2/
    │   ├── article.json
    │   └── image.jpg
    └── ...

text_output/
└── session_1234567890/
    ├── Article_Title_1/
    │   └── article.txt
    └── ...

summary_output/
└── session_1234567890/
    ├── Article_Title_1/
    │   ├── article_text_summary.json
    │   └── image_summary.json
    └── ...
```

## File Formats

### article.json
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "content": "Full article text...",
  "author": "Author Name",
  "date": "2025-01-01",
  "image_path": "path/to/image.jpg",
  "word_count": 500
}
```

### article.txt
```
Title: Article Title
Author: Author Name
Date: 2025-01-01

Content:
Full article text...
```

### article_text_summary.json
```json
{
  "filename": "article.json",
  "summary_type": "text",
  "summary": "AI-generated summary of the article..."
}
```

### image_summary.json
```json
{
  "filename": "image.jpg",
  "summary_type": "image",
  "summary": "AI-generated description of the image..."
}
```

## Troubleshooting

### "Module not found" errors
Make sure you installed all requirements:
```bash
pip install -r requirements.txt
```

### AI Summarization is slow
- First run downloads models (~2GB) - this is normal
- Subsequent runs are much faster
- AI processing is CPU-intensive, expect 5-10 seconds per article

### Scraper finds no articles
- Try a different news website
- Some websites may block scraping
- Increase the number of articles to find more matches

### Port 5000 is already in use
Stop other applications using port 5000, or edit `web_server_local.py` and change:
```python
app.run(host='0.0.0.0', port=5000, ...)
```
to use a different port (e.g., 5001, 8080, etc.)

### Memory errors during summarization
- AI models require significant RAM (~4GB)
- Close other applications
- Process fewer articles at once

## Advanced Usage

### Running the Scraper Directly

You can run the scraper from the command line:

```bash
python ultimate_scraper_v2.py "https://www.bbc.com/news" --max-articles 20 --output scraping_output/custom_session
```

### Customizing Output Folders

Edit `web_server_local.py` to change output folders:

```python
SCRAPING_OUTPUT_DIR = "my_scraping_folder"
TEXT_OUTPUT_DIR = "my_text_folder"
SUMMARY_OUTPUT_DIR = "my_summary_folder"
```

### Using Different AI Models

Edit the summarization section in `web_server_local.py`:

```python
text_model = "facebook/bart-large-cnn"  # Change to "t5-base" for faster but less accurate
image_model = "nlpconnect/vit-gpt2-image-captioning"
```

## System Requirements

### Minimum
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB free
- Internet: For downloading models

### Recommended
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 20GB+ free
- SSD for better performance

## Notes

- **First AI run:** Downloads models, takes 10-20 minutes
- **Scraping speed:** Depends on website and network
- **Article quality:** Some websites work better than others
- **Local only:** No cloud dependencies, everything runs on your machine
- **Privacy:** All data stays on your computer

## Support

If you encounter issues:
1. Check the console/terminal for error messages
2. Look at the logs in the web interface
3. Ensure all requirements are installed
4. Try restarting the web server

## Comparison with Cloud Version

| Feature | Local Version | Cloud Version (Original) |
|---------|--------------|--------------------------|
| Setup | Install Python packages | Configure EC2, S3, AWS credentials |
| Speed | Good (depends on CPU) | Faster (EC2 optimized) |
| Cost | Free | AWS charges apply |
| Storage | Local folders | S3 buckets |
| Maintenance | None | Manage EC2 instance |
| Privacy | Fully private | Data in cloud |
| Internet | Only for models | Always required |

## Tips for Best Results

1. **Choose good websites:** News sites with clear article structures work best
2. **Start small:** Test with 5-10 articles first
3. **Session IDs:** Write them down or copy from the interface
4. **Disk space:** Each article with image takes ~200KB-2MB
5. **AI models:** Downloaded once, reused forever
6. **Patience:** First AI run takes time, but it's worth it!

Enjoy using BOCK Scraper! 🚀

