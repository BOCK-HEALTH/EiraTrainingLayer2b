#!/usr/bin/env python3
"""
Ultimate Scraper V2 - Web Interface Backend
Flask server for managing EC2 scraping jobs with S3 integration
"""

import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import paramiko
import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

#copy paste this from config.txt



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
    'targetBucket': None
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

class ScrapingJob:
    def __init__(self, url, max_articles):
        self.url = url
        self.max_articles = max_articles
        self.start_time = time.time()
        self.ssh_client = None
        self.process_thread = None
        self.is_running = False
        self.session_id = f"session_{int(time.time())}"
        
    def start(self):
        """Start the scraping job on EC2"""
        self.is_running = True
        self.process_thread = threading.Thread(target=self._run_scraping)
        self.process_thread.start()
        
    def stop(self):
        """Stop the scraping job"""
        self.is_running = False
        if self.ssh_client:
            try:
                self.ssh_client.exec_command("pkill -f ultimate_scraper_v2.py")
                self.ssh_client.close()
            except Exception as e:
                logger.error(f"Error stopping scraping: {e}")
        
    def _run_scraping(self):
        """Run the scraping process on EC2 and stream logs"""
        global scraping_active, scraping_stats
        
        try:
            # Connect to EC2
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            add_log("Connecting to EC2 instance...", "info")
            scraping_stats['progress'] = 5
            
            self.ssh_client.connect(
                hostname=EC2_HOST,
                username=EC2_USER,
                key_filename=EC2_KEY_PATH,
                timeout=30
            )
            
            add_log("Connected to EC2 successfully!", "success")
            scraping_stats['progress'] = 10
            
            # Prepare remote output path
            remote_output_path = f"/home/ec2-user/scraping_output_{self.session_id}"
            
            # Build command to run scraper and upload to S3
            command = f"""
source {EC2_ENV_PATH} && \
mkdir -p {remote_output_path} && \
python {EC2_SCRAPER_PATH} "{self.url}" --max-articles {self.max_articles} --output {remote_output_path} && \
aws s3 sync {remote_output_path}/ s3://{S3_BUCKET_NAME}/{self.session_id}/ && \
rm -rf {remote_output_path}
"""
            
            add_log(f"Starting scraper for {self.max_articles} articles", "info")
            add_log(f"Target URL: {self.url}", "info")
            add_log(f"Session ID: {self.session_id}", "info")
            scraping_stats['progress'] = 15
            scraping_stats['sessionId'] = self.session_id
            
            # Execute command
            stdin, stdout, stderr = self.ssh_client.exec_command(command, get_pty=True)
            
            # Stream output in real-time
            while self.is_running:
                line = stdout.readline()
                if not line:
                    break
                    
                line = line.strip()
                if line:
                    # Parse and categorize log lines
                    log_type = self._classify_log_line(line)
                    add_log(line, log_type)
                    
                    # Update statistics based on log content
                    self._update_stats_from_log(line)
            
            # Wait for completion
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0 and self.is_running:
                add_log("Scraping completed successfully!", "success")
                add_log(f"All files uploaded to S3 bucket: {S3_BUCKET_NAME}/{self.session_id}", "success")
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
            if self.ssh_client:
                self.ssh_client.close()
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
        if "VERIFIED ARTICLE" in line or "Article" in line and ":" in line:
            scraping_stats['articlesFound'] = scraping_stats.get('articlesFound', 0) + 1
            progress = min(15 + (scraping_stats['articlesFound'] / self.max_articles) * 60, 75)
            scraping_stats['progress'] = int(progress)
            
        # Count articles saved
        if "SAVED:" in line or "SUCCESS: Saved" in line:
            scraping_stats['articlesSaved'] = scraping_stats.get('articlesSaved', 0) + 1
            
        # Count images saved
        if "image.jpg" in line and ("SUCCESS" in line or "Saved" in line):
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

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start a new scraping job"""
    global scraping_active, current_job, all_logs, scraping_stats
    
    if scraping_active:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    try:
        data = request.json
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
        current_job = ScrapingJob(url, max_articles)
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
    """Convert JSON files to text and save to bockscraper1 S3 bucket"""
    global conversion_active, conversion_logs, conversion_stats
    
    if conversion_active:
        return jsonify({'error': 'Conversion already in progress'}), 400
    
    try:
        data = request.json
        source_session = data.get('sourceSession')
        
        if not source_session:
            return jsonify({'error': 'Source session is required'}), 400
        
        # Use hard-coded target bucket
        target_bucket = S3_TEXT_BUCKET_NAME
        
        # Reset conversion state
        conversion_logs = []
        conversion_stats = {
            'completed': False,
            'error': None,
            'targetBucket': target_bucket
        }
        conversion_active = True
        
        # Start conversion in a separate thread
        thread = threading.Thread(
            target=_run_conversion,
            args=(source_session, target_bucket)
        )
        thread.start()
        
        return jsonify({'message': 'Conversion started successfully'})
        
    except Exception as e:
        error_msg = f"Error starting conversion: {str(e)}"
        add_conversion_log(error_msg, "error")
        return jsonify({'error': error_msg}), 500

def _run_conversion(source_session, target_bucket):
    """Run the conversion process using EC2 for better performance"""
    global conversion_active, conversion_stats
    
    try:
        add_conversion_log(f"Starting conversion for session: {source_session}", "info")
        add_conversion_log(f"Target bucket: {target_bucket}", "info")
        
        # Use EC2 to do the conversion (much faster than local)
        add_conversion_log("Connecting to EC2 for conversion...", "info")
        
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh_client.connect(
                hostname=EC2_HOST,
                username=EC2_USER,
                key_filename=EC2_KEY_PATH,
                timeout=30
            )
            
            add_conversion_log("Connected to EC2 successfully!", "success")
            
            # Create a Python script on EC2 to do the conversion
            conversion_script = f"""
import json
import os
import subprocess

source_bucket = '{S3_BUCKET_NAME}'
target_bucket = '{target_bucket}'
source_prefix = '{source_session}/'
temp_dir = '/tmp/conversion_{source_session}'

# Create temp directory
os.makedirs(temp_dir, exist_ok=True)

print("Downloading files from S3...")
result = subprocess.run(
    f'aws s3 sync s3://{{source_bucket}}/{{source_prefix}} {{temp_dir}}/ --exclude "*" --include "*.json"',
    shell=True,
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Error downloading: {{result.stderr}}")
    exit(1)

# Find all JSON files
json_files = []
for root, dirs, files in os.walk(temp_dir):
    for file in files:
        if file.endswith('.json'):
            json_files.append(os.path.join(root, file))

print(f"Found {{len(json_files)}} JSON files")

converted = 0
for json_path in json_files:
    try:
        relative_path = os.path.relpath(json_path, temp_dir)
        print(f"Processing: {{relative_path}}")
        
        # Read JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            article_data = json.load(f)
        
        # Create text content
        text_content = f\"\"\"Title: {{article_data.get('title', 'N/A')}}
Author: {{article_data.get('author', 'N/A')}}
Date: {{article_data.get('date', 'N/A')}}

Content:
{{article_data.get('content', 'N/A')}}
\"\"\"
        
        # Write text file
        txt_path = json_path.replace('.json', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        converted += 1
        print(f"Converted: {{relative_path.replace('.json', '.txt')}}")
        
    except Exception as e:
        print(f"Error: {{str(e)}}")
        continue

print(f"Uploading {{converted}} text files to S3...")
result = subprocess.run(
    f'aws s3 sync {{temp_dir}}/ s3://{{target_bucket}}/{{source_prefix}} --exclude "*" --include "*.txt"',
    shell=True,
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Upload error: {{result.stderr}}")
else:
    print(f"Conversion completed! {{converted}} files converted")

# Cleanup
subprocess.run(f'rm -rf {{temp_dir}}', shell=True)
"""
            
            # Write script to EC2
            script_path = f"/tmp/convert_{source_session}.py"
            add_conversion_log("Uploading conversion script to EC2...", "info")
            
            # Use SFTP to upload script
            sftp = ssh_client.open_sftp()
            with sftp.file(script_path, 'w') as f:
                f.write(conversion_script)
            sftp.close()
            
            add_conversion_log("Running conversion on EC2...", "info")
            
            # Execute the script
            command = f"source {EC2_ENV_PATH} && python {script_path} && rm {script_path}"
            stdin, stdout, stderr = ssh_client.exec_command(command, get_pty=True)
            
            # Stream output
            while True:
                line = stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line:
                    if 'Error' in line or 'error' in line:
                        add_conversion_log(line, "error")
                    elif 'Converted:' in line or 'completed' in line:
                        add_conversion_log(line, "success")
                    else:
                        add_conversion_log(line, "info")
            
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                add_conversion_log("Conversion completed successfully!", "success")
                add_conversion_log(f"Text files saved to: s3://{target_bucket}/{source_session}/", "info")
                conversion_stats['completed'] = True
            else:
                add_conversion_log("Conversion failed", "error")
                conversion_stats['error'] = "Conversion script failed"
                
        except Exception as e:
            add_conversion_log(f"EC2 connection error: {str(e)}", "error")
            conversion_stats['error'] = str(e)
        finally:
            if ssh_client:
                ssh_client.close()
        
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
        'targetBucket': conversion_stats.get('targetBucket')
    }
    
    return jsonify(response_data)

@app.route('/list_bucket', methods=['POST'])
def list_bucket():
    """List files and folders in S3 bucket"""
    try:
        data = request.json
        bucket_name = data.get('bucket')
        prefix = data.get('prefix', '')
        
        if not bucket_name:
            return jsonify({'error': 'Bucket name is required'}), 400
        
        # Initialize S3 client
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
        else:
            s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # Add trailing slash to prefix if not empty
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        
        # List objects
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            Delimiter='/'
        )
        
        folders = []
        files = []
        
        # Get folders (CommonPrefixes)
        if 'CommonPrefixes' in response:
            for prefix_obj in response['CommonPrefixes']:
                folder_name = prefix_obj['Prefix'].rstrip('/').split('/')[-1]
                folders.append({
                    'name': folder_name,
                    'prefix': prefix_obj['Prefix']
                })
        
        # Get files (Contents)
        if 'Contents' in response:
            for obj in response['Contents']:
                # Skip if it's a folder marker
                if obj['Key'].endswith('/'):
                    continue
                
                # Skip if it's the prefix itself
                if obj['Key'] == prefix:
                    continue
                
                file_name = obj['Key'].split('/')[-1]
                files.append({
                    'name': file_name,
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'lastModified': obj['LastModified'].isoformat()
                })
        
        return jsonify({
            'folders': folders,
            'files': files
        })
        
    except ClientError as e:
        logger.error(f"S3 error: {str(e)}")
        return jsonify({'error': f'S3 error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error listing bucket: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_file', methods=['POST'])
def download_file():
    """Download a file from S3"""
    try:
        data = request.json
        bucket_name = data.get('bucket')
        file_key = data.get('key')
        
        if not bucket_name or not file_key:
            return jsonify({'error': 'Bucket and key are required'}), 400
        
        # Initialize S3 client
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
        else:
            s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # Get the file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read()
        
        # Determine content type
        content_type = response.get('ContentType', 'application/octet-stream')
        
        # Create response with file
        from flask import Response
        return Response(
            file_content,
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{file_key.split("/")[-1]}"'
            }
        )
        
    except ClientError as e:
        logger.error(f"S3 download error: {str(e)}")
        return jsonify({'error': f'S3 error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize logs
    add_log("Web server starting...", "info")
    add_log("BOCK Scraper Web Interface Ready", "success")
    add_log(f"EC2 Instance: {EC2_HOST}", "info")
    add_log(f"S3 Bucket: {S3_BUCKET_NAME}", "info")
    
    print("=" * 80)
    print("🚀 BOCK SCRAPER - WEB INTERFACE")
    print("=" * 80)
    print(f"🌐 Open your browser and go to: http://localhost:5000")
    print(f"☁️  EC2 Instance: {EC2_HOST}")
    print(f"📦 S3 Bucket: {S3_BUCKET_NAME}")
    print("=" * 80)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        if current_job and scraping_active:
            current_job.stop()
    except Exception as e:
        print(f"\n❌ Server error: {e}")
