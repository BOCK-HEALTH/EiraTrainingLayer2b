#!/usr/bin/env python3
"""
Local Web Server for BOCK Scraper
Runs everything locally without EC2/S3 dependencies
"""

import os
import sys
import json
import time
import threading
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global error handler to return JSON for API errors
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/') or request.path.startswith('/start_') or request.path.startswith('/stop_') or request.path.startswith('/get_') or request.path.startswith('/convert_') or request.path.startswith('/generate_') or request.path.startswith('/list_') or request.path.startswith('/download_'):
        return jsonify({'error': 'Not found'}), 404
    return error

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

# Local Configuration
SCRAPER_PATH = "ultimate_scraper_v2.py"
SCRAPING_OUTPUT_DIR = "scraping_output"
TEXT_OUTPUT_DIR = "text_output"
SUMMARY_OUTPUT_DIR = "summary_output"

# Ensure output directories exist
for dir_path in [SCRAPING_OUTPUT_DIR, TEXT_OUTPUT_DIR, SUMMARY_OUTPUT_DIR]:
    Path(dir_path).mkdir(exist_ok=True)

# Global state for scraping
scraping_active = False
current_job = None
all_logs = []
scraping_stats = {
    'articlesFound': 0,
    'articlesSaved': 0,
    'imagesFound': 0,
    'progress': 0,
    'completed': False,
    'sessionId': None
}

# Global state for conversion
conversion_active = False
conversion_logs = []
conversion_stats = {
    'completed': False,
    'error': None,
    'targetFolder': None
}

# Global state for AI summarization
summarization_active = False
summarization_logs = []
summarization_stats = {
    'completed': False,
    'error': None,
    'targetFolder': SUMMARY_OUTPUT_DIR,
    'textSummaries': 0,
    'imageSummaries': 0,
    'totalFolders': 0
}

def add_log(message, log_type="info"):
    """Add a log message to the global log list"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'type': log_type
    }
    all_logs.append(log_entry)
    logger.info(f"[{log_type}] {message}")
    
    # Keep only last 500 log entries
    if len(all_logs) > 500:
        all_logs.pop(0)

def add_conversion_log(message, log_type="info"):
    """Add a log message to the conversion log list"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'type': log_type
    }
    conversion_logs.append(log_entry)
    logger.info(f"[CONVERT][{log_type}] {message}")
    
    # Keep only last 200 log entries
    if len(conversion_logs) > 200:
        conversion_logs.pop(0)

def add_summarization_log(message, log_type="info"):
    """Add a log message to the summarization log list"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'message': message,
        'type': log_type
    }
    summarization_logs.append(log_entry)
    logger.info(f"[SUMMARIZE][{log_type}] {message}")
    
    # Keep only last 300 log entries
    if len(summarization_logs) > 300:
        summarization_logs.pop(0)

class LocalScrapingJob:
    def __init__(self, url, max_articles):
        self.url = url
        self.max_articles = max_articles
        self.start_time = time.time()
        self.process = None
        self.process_thread = None
        self.is_running = False
        self.session_id = f"session_{int(time.time())}"
        
    def start(self):
        """Start the scraping job locally"""
        self.is_running = True
        self.process_thread = threading.Thread(target=self._run_scraping)
        self.process_thread.start()
        
    def stop(self):
        """Stop the scraping job"""
        self.is_running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping scraping: {e}")
                try:
                    self.process.kill()
                except:
                    pass
        
    def _run_scraping(self):
        """Run the scraping process locally"""
        global scraping_active, scraping_stats
        
        try:
            # Create session output directory
            session_output = Path(SCRAPING_OUTPUT_DIR) / self.session_id
            session_output.mkdir(parents=True, exist_ok=True)
            
            add_log("Starting local scraping process...", "info")
            scraping_stats['progress'] = 5
            scraping_stats['sessionId'] = self.session_id
            
            # Build command to run scraper locally
            # Use the same Python interpreter as the web server
            python_exe = sys.executable
            
            # If running from venv, use venv Python, otherwise use system Python
            if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                # We're in a virtual environment
                venv_python = python_exe
            else:
                # Try to find venv Python in web_venv folder
                venv_python_path = Path('web_venv/Scripts/python.exe')
                if venv_python_path.exists():
                    venv_python = str(venv_python_path.absolute())
                else:
                    venv_python = python_exe
            
            command = [
                venv_python,
                SCRAPER_PATH,
                self.url,
                "--max-articles", str(self.max_articles),
                "--output", str(session_output)
            ]
            
            add_log(f"Using Python: {venv_python}", "info")
            
            add_log(f"Starting scraper for {self.max_articles} articles", "info")
            add_log(f"Target URL: {self.url}", "info")
            add_log(f"Session ID: {self.session_id}", "info")
            scraping_stats['progress'] = 10
            
            # Execute command
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output in real-time
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_running:
                    break
                    
                line = line.strip()
                if line:
                    # Parse and categorize log lines
                    log_type = self._classify_log_line(line)
                    add_log(line, log_type)
                    
                    # Update statistics based on log content
                    self._update_stats_from_log(line)
            
            # Wait for completion
            exit_status = self.process.wait()
            
            if exit_status == 0 and self.is_running:
                add_log("Scraping completed successfully!", "success")
                add_log(f"Files saved to: {session_output}", "success")
                scraping_stats['progress'] = 100
                scraping_stats['completed'] = True
            else:
                add_log("Scraping encountered an error or was stopped", "error")
                scraping_stats['progress'] = 0
                
        except Exception as e:
            error_msg = f"Error during scraping: {str(e)}"
            add_log(error_msg, "error")
            scraping_stats['progress'] = 0
            
        finally:
            self.is_running = False
            scraping_active = False
            
    def _classify_log_line(self, line):
        """Classify log lines by type for styling"""
        line_lower = line.lower()
        if any(word in line_lower for word in ['error', 'failed', 'exception']):
            return 'error'
        elif any(word in line_lower for word in ['success', 'saved', 'complete', 'downloaded']):
            return 'success'
        elif any(word in line_lower for word in ['warning', 'filtered']):
            return 'warning'
        else:
            return 'info'
    
    def _update_stats_from_log(self, line):
        """Update statistics based on log line content"""
        global scraping_stats
        
        # Count articles found
        if "VERIFIED ARTICLE" in line or ("Article" in line and ":" in line):
            scraping_stats['articlesFound'] = scraping_stats.get('articlesFound', 0) + 1
            progress = min(15 + (scraping_stats['articlesFound'] / self.max_articles) * 60, 75)
            scraping_stats['progress'] = int(progress)
            
        # Count articles saved
        if "SAVED:" in line or "SUCCESS: Saved" in line or "article.json" in line:
            scraping_stats['articlesSaved'] = scraping_stats.get('articlesSaved', 0) + 1
            
        # Count images saved
        if "image.jpg" in line and ("SUCCESS" in line or "Saved" in line or "Downloaded" in line):
            scraping_stats['imagesFound'] = scraping_stats.get('imagesFound', 0) + 1
            progress = min(75 + (scraping_stats['imagesFound'] / max(scraping_stats['articlesFound'], 1)) * 15, 90)
            scraping_stats['progress'] = int(progress)
            
        # Check for completion indicators
        if "COMPLETE" in line.upper() or "completed successfully" in line:
            scraping_stats['progress'] = 95

@app.route('/')
def index():
    """Serve the main interface"""
    return send_from_directory('.', 'index.html')

@app.route('/Health Text-01.png')
def serve_logo():
    """Serve the logo image"""
    return send_from_directory('.', 'Health Text-01.png')

@app.route('/api/test', methods=['GET', 'POST'])
def test_api():
    """Test endpoint to verify API is working"""
    return jsonify({
        'status': 'ok',
        'message': 'API is working',
        'method': request.method,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start a new scraping job"""
    global scraping_active, current_job, all_logs, scraping_stats
    
    logger.info(f"Received scraping request: {request.method} {request.path}")
    logger.info(f"Content-Type: {request.content_type}")
    
    if scraping_active:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    try:
        data = request.get_json()
        if data is None:
            logger.error("No JSON data in request")
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        url = data.get('url')
        max_articles = data.get('maxArticles', 10)
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Reset global state
        all_logs = []
        scraping_stats = {
            'articlesFound': 0,
            'articlesSaved': 0,
            'imagesFound': 0,
            'progress': 0,
            'completed': False,
            'sessionId': None
        }
        
        # Create and start job
        current_job = LocalScrapingJob(url, max_articles)
        current_job.start()
        scraping_active = True
        
        add_log(f"Scraping job started for {url}", "success")
        
        return jsonify({
            'message': 'Scraping started successfully',
            'sessionId': current_job.session_id
        })
        
    except Exception as e:
        error_msg = f"Error starting scraping: {str(e)}"
        add_log(error_msg, "error")
        return jsonify({'error': error_msg}), 500

@app.route('/stop_scraping', methods=['POST'])
def stop_scraping():
    """Stop the current scraping job"""
    global scraping_active, current_job
    
    if not scraping_active or not current_job:
        return jsonify({'error': 'No active scraping job'}), 400
    
    try:
        current_job.stop()
        scraping_active = False
        add_log("Scraping stopped by user", "warning")
        
        return jsonify({'message': 'Scraping stopped successfully'})
        
    except Exception as e:
        error_msg = f"Error stopping scraping: {str(e)}"
        add_log(error_msg, "error")
        return jsonify({'error': error_msg}), 500

@app.route('/get_status', methods=['GET'])
def get_status():
    """Get current scraping status and logs"""
    global all_logs, scraping_stats, scraping_active
    
    response_data = {
        'articlesFound': scraping_stats.get('articlesFound', 0),
        'articlesSaved': scraping_stats.get('articlesSaved', 0),
        'imagesFound': scraping_stats.get('imagesFound', 0),
        'progress': scraping_stats.get('progress', 0),
        'completed': scraping_stats.get('completed', False),
        'sessionId': scraping_stats.get('sessionId'),
        'logs': all_logs,
        'isActive': scraping_active
    }
    
    return jsonify(response_data)

@app.route('/convert_to_text', methods=['POST'])
def convert_to_text():
    """Convert JSON files to text and save locally"""
    global conversion_active, conversion_logs, conversion_stats
    
    if conversion_active:
        return jsonify({'error': 'Conversion already in progress'}), 400
    
    try:
        data = request.json
        source_session = data.get('sourceSession')
        
        if not source_session:
            return jsonify({'error': 'Source session is required'}), 400
        
        # Reset conversion state
        conversion_logs = []
        conversion_stats = {
            'completed': False,
            'error': None,
            'targetFolder': TEXT_OUTPUT_DIR
        }
        conversion_active = True
        
        # Start conversion in a separate thread
        thread = threading.Thread(
            target=_run_conversion,
            args=(source_session,)
        )
        thread.start()
        
        return jsonify({'message': 'Conversion started successfully'})
        
    except Exception as e:
        error_msg = f"Error starting conversion: {str(e)}"
        add_conversion_log(error_msg, "error")
        return jsonify({'error': error_msg}), 500

def _run_conversion(source_session):
    """Run the conversion process locally"""
    global conversion_active, conversion_stats
    
    try:
        add_conversion_log(f"Starting conversion for session: {source_session}", "info")
        
        source_dir = Path(SCRAPING_OUTPUT_DIR) / source_session
        target_dir = Path(TEXT_OUTPUT_DIR) / source_session
        
        if not source_dir.exists():
            add_conversion_log(f"Source directory not found: {source_dir}", "error")
            conversion_stats['error'] = "Source directory not found"
            conversion_active = False
            return
        
        target_dir.mkdir(parents=True, exist_ok=True)
        add_conversion_log(f"Target directory: {target_dir}", "info")
        
        # Find all JSON files
        json_files = list(source_dir.rglob("*.json"))
        add_conversion_log(f"Found {len(json_files)} JSON files", "info")
        
        converted = 0
        for json_path in json_files:
            try:
                relative_path = json_path.relative_to(source_dir)
                add_conversion_log(f"Processing: {relative_path}", "info")
                
                # Read JSON
                with open(json_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                
                # Create text content
                text_content = f"""Title: {article_data.get('title', 'N/A')}
Author: {article_data.get('author', 'N/A')}
Date: {article_data.get('date', 'N/A')}

Content:
{article_data.get('content', 'N/A')}
"""
                
                # Write text file in same structure
                txt_path = target_dir / relative_path.parent / relative_path.stem
                txt_path.parent.mkdir(parents=True, exist_ok=True)
                txt_path = txt_path.with_suffix('.txt')
                
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                converted += 1
                add_conversion_log(f"Converted: {relative_path.parent}/{relative_path.stem}.txt", "success")
                
            except Exception as e:
                add_conversion_log(f"Error: {str(e)}", "error")
                continue
        
        add_conversion_log(f"Conversion completed! {converted} files converted", "success")
        add_conversion_log(f"Text files saved to: {target_dir}", "info")
        conversion_stats['completed'] = True
        
    except Exception as e:
        error_msg = f"Conversion error: {str(e)}"
        add_conversion_log(error_msg, "error")
        conversion_stats['error'] = str(e)
    
    finally:
        conversion_active = False

@app.route('/conversion_status', methods=['GET'])
def conversion_status():
    """Get conversion status and logs"""
    global conversion_logs, conversion_stats
    
    response_data = {
        'logs': conversion_logs,
        'completed': conversion_stats.get('completed', False),
        'error': conversion_stats.get('error'),
        'targetFolder': conversion_stats.get('targetFolder')
    }
    
    return jsonify(response_data)

@app.route('/generate_summaries', methods=['POST'])
def generate_summaries():
    """Generate AI summaries for articles and images"""
    global summarization_active, summarization_logs, summarization_stats
    
    if summarization_active:
        return jsonify({'error': 'Summarization already in progress'}), 400
    
    try:
        data = request.json
        source_session = data.get('sourceSession')
        
        if not source_session:
            return jsonify({'error': 'Source session is required'}), 400
        
        # Reset summarization state
        summarization_logs = []
        summarization_stats = {
            'completed': False,
            'error': None,
            'targetFolder': SUMMARY_OUTPUT_DIR,
            'textSummaries': 0,
            'imageSummaries': 0,
            'totalFolders': 0
        }
        summarization_active = True
        
        # Start summarization in a separate thread
        thread = threading.Thread(
            target=_run_summarization,
            args=(source_session,)
        )
        thread.start()
        
        return jsonify({'message': 'Summarization started successfully'})
        
    except Exception as e:
        error_msg = f"Error starting summarization: {str(e)}"
        add_summarization_log(error_msg, "error")
        return jsonify({'error': error_msg}), 500

def _run_summarization(source_session):
    """Run the AI summarization locally"""
    global summarization_active, summarization_stats
    
    try:
        add_summarization_log(f"Starting AI summarization for session: {source_session}", "info")
        
        source_dir = Path(SCRAPING_OUTPUT_DIR) / source_session
        target_dir = Path(SUMMARY_OUTPUT_DIR) / source_session
        
        if not source_dir.exists():
            add_summarization_log(f"Source directory not found: {source_dir}", "error")
            summarization_stats['error'] = "Source directory not found"
            summarization_active = False
            return
        
        target_dir.mkdir(parents=True, exist_ok=True)
        add_summarization_log(f"Target directory: {target_dir}", "info")
        add_summarization_log("Loading AI models (this may take a while)...", "warning")
        
        # Import summarization modules
        sys.path.insert(0, str(Path('summary/bocksummarizer-main')))
        
        try:
            from summarize_all import (
                _load_text_from_json, summarize_text_content, caption_image,
                _derive_text_output_key, _derive_image_output_key
            )
        except ImportError as e:
            add_summarization_log(f"Cannot import summarization module: {e}", "error")
            summarization_stats['error'] = str(e)
            summarization_active = False
            sys.path.pop(0)
            return
        
        # Find all article folders
        folders = [d for d in source_dir.iterdir() if d.is_dir()]
        add_summarization_log(f"Found {len(folders)} article folders", "info")
        
        text_count = 0
        image_count = 0
        
        # Models to use
        text_model = "facebook/bart-large-cnn"
        image_model = "nlpconnect/vit-gpt2-image-captioning"
        
        for idx, folder in enumerate(folders, 1):
            try:
                folder_name = folder.name
                add_summarization_log(f"Processing folder {idx}/{len(folders)}: {folder_name}", "info")
                summarization_stats['totalFolders'] = idx
                
                # Create target folder
                target_folder = target_dir / folder_name
                target_folder.mkdir(parents=True, exist_ok=True)
                
                # Process JSON files
                json_files = list(folder.glob("*.json"))
                json_files = [f for f in json_files if not f.name.endswith(("_summary.json", "_text_summary.json"))]
                
                for json_file in json_files:
                    try:
                        add_summarization_log(f"  Processing JSON: {json_file.name}", "info")
                        
                        text = _load_text_from_json(str(json_file))
                        if not text:
                            add_summarization_log(f"  Skipped {json_file.name} (empty)", "warning")
                            continue
                        
                        add_summarization_log(f"  Generating summary...", "info")
                        summary = summarize_text_content(text, text_model)
                        
                        out_doc = {
                            "filename": json_file.name,
                            "summary_type": "text",
                            "summary": summary,
                        }
                        
                        out_path = target_folder / "article_text_summary.json"
                        with open(out_path, 'w', encoding='utf-8') as f:
                            json.dump(out_doc, f, ensure_ascii=False, indent=2)
                        
                        text_count += 1
                        summarization_stats['textSummaries'] = text_count
                        add_summarization_log(f"  ✓ Text summary saved", "success")
                        
                    except Exception as e:
                        add_summarization_log(f"  ✗ Error: {e}", "error")
                
                # Process image files
                image_files = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
                multiple_images = len(image_files) > 1
                
                for image_file in image_files:
                    try:
                        add_summarization_log(f"  Processing image: {image_file.name}", "info")
                        
                        caption = caption_image(str(image_file), image_model)
                        
                        out_doc = {
                            "filename": image_file.name,
                            "summary_type": "image",
                            "summary": caption,
                        }
                        
                        if multiple_images:
                            out_path = target_folder / f"{image_file.stem}_image_summary.json"
                        else:
                            out_path = target_folder / "image_summary.json"
                        
                        with open(out_path, 'w', encoding='utf-8') as f:
                            json.dump(out_doc, f, ensure_ascii=False, indent=2)
                        
                        image_count += 1
                        summarization_stats['imageSummaries'] = image_count
                        add_summarization_log(f"  ✓ Image caption saved", "success")
                        
                    except Exception as e:
                        add_summarization_log(f"  ✗ Error: {e}", "error")
                
            except Exception as e:
                add_summarization_log(f"Error processing folder: {e}", "error")
        
        add_summarization_log("✅ AI summarization completed successfully!", "success")
        add_summarization_log(f"Text summaries: {text_count}", "success")
        add_summarization_log(f"Image summaries: {image_count}", "success")
        add_summarization_log(f"Summaries saved to: {target_dir}", "info")
        summarization_stats['completed'] = True
        
        sys.path.pop(0)
        
    except Exception as e:
        error_msg = f"Summarization error: {str(e)}"
        add_summarization_log(error_msg, "error")
        summarization_stats['error'] = str(e)
        if str(Path('summary/bocksummarizer-main')) in sys.path:
            sys.path.remove(str(Path('summary/bocksummarizer-main')))
    
    finally:
        summarization_active = False

@app.route('/summarization_status', methods=['GET'])
def summarization_status():
    """Get summarization status and logs"""
    global summarization_logs, summarization_stats
    
    response_data = {
        'logs': summarization_logs,
        'completed': summarization_stats.get('completed', False),
        'error': summarization_stats.get('error'),
        'targetBucket': summarization_stats.get('targetFolder'),
        'textSummaries': summarization_stats.get('textSummaries', 0),
        'imageSummaries': summarization_stats.get('imageSummaries', 0),
        'totalFolders': summarization_stats.get('totalFolders', 0)
    }
    
    return jsonify(response_data)

@app.route('/list_bucket', methods=['POST'])
def list_bucket():
    """List files and folders in local directory"""
    try:
        data = request.json
        bucket_name = data.get('bucket')
        prefix = data.get('prefix', '')
        
        if not bucket_name:
            return jsonify({'error': 'Bucket name is required'}), 400
        
        # Map bucket names to local directories
        bucket_map = {
            'bockscraper': SCRAPING_OUTPUT_DIR,
            'bockscraper1': TEXT_OUTPUT_DIR,
            'bockscraper2': SUMMARY_OUTPUT_DIR
        }
        
        base_dir = Path(bucket_map.get(bucket_name, SCRAPING_OUTPUT_DIR))
        
        if prefix:
            current_dir = base_dir / prefix
        else:
            current_dir = base_dir
        
        if not current_dir.exists():
            return jsonify({'folders': [], 'files': []})
        
        folders = []
        files = []
        
        # List directories and files
        for item in current_dir.iterdir():
            if item.is_dir():
                folders.append({
                    'name': item.name,
                    'prefix': str(item.relative_to(base_dir))
                })
            elif item.is_file():
                stat = item.stat()
                files.append({
                    'name': item.name,
                    'key': str(item.relative_to(base_dir)),
                    'size': stat.st_size,
                    'lastModified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return jsonify({
            'folders': sorted(folders, key=lambda x: x['name']),
            'files': sorted(files, key=lambda x: x['name'])
        })
        
    except Exception as e:
        logger.error(f"Error listing directory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_file', methods=['POST'])
def download_file():
    """Download a file from local directory"""
    try:
        data = request.json
        bucket_name = data.get('bucket')
        file_key = data.get('key')
        
        if not bucket_name or not file_key:
            return jsonify({'error': 'Bucket and key are required'}), 400
        
        # Map bucket names to local directories
        bucket_map = {
            'bockscraper': SCRAPING_OUTPUT_DIR,
            'bockscraper1': TEXT_OUTPUT_DIR,
            'bockscraper2': SUMMARY_OUTPUT_DIR
        }
        
        base_dir = Path(bucket_map.get(bucket_name, SCRAPING_OUTPUT_DIR))
        file_path = base_dir / file_key
        
        if not file_path.exists() or not file_path.is_file():
            return jsonify({'error': 'File not found'}), 404
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Determine content type
        if file_path.suffix.lower() in ['.json']:
            content_type = 'application/json'
        elif file_path.suffix.lower() in ['.txt']:
            content_type = 'text/plain'
        elif file_path.suffix.lower() in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif file_path.suffix.lower() == '.png':
            content_type = 'image/png'
        else:
            content_type = 'application/octet-stream'
        
        # Create response with file
        return Response(
            file_content,
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{file_path.name}"'
            }
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize logs
    add_log("Local web server starting...", "info")
    add_log("BOCK Scraper Web Interface Ready", "success")
    add_log(f"Scraping output: {SCRAPING_OUTPUT_DIR}", "info")
    add_log(f"Text output: {TEXT_OUTPUT_DIR}", "info")
    add_log(f"Summary output: {SUMMARY_OUTPUT_DIR}", "info")
    
    print("=" * 80)
    print("BOCK SCRAPER - LOCAL WEB INTERFACE")
    print("=" * 80)
    print(f"Open your browser and go to: http://localhost:5000")
    print(f"Scraping output: {SCRAPING_OUTPUT_DIR}")
    print(f"Text output: {TEXT_OUTPUT_DIR}")
    print(f"Summary output: {SUMMARY_OUTPUT_DIR}")
    print("=" * 80)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        if current_job and scraping_active:
            current_job.stop()
    except Exception as e:
        print(f"\nServer error: {e}")

