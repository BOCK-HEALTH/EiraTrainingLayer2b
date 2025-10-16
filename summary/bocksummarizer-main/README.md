# S3 Text and Image Summarization

Automated text and image summarization for files stored in AWS S3 buckets using Hugging Face transformers.

## Features

- **Text Summarization**: Summarizes JSON text content using BART or T5 models
- **Image Captioning**: Generates captions for JPG/JPEG/PNG images using Vision Transformer models
- **S3 Integration**: Processes files from input S3 bucket and saves results to output S3 bucket
- **Batch Processing**: Handles nested folder structures automatically
- **Flexible Configuration**: Support for different models and bucket configurations

## Scripts

### `summarize_all.py`
Complete processing script that handles both text and image summarization:
- Processes JSON files and generates text summaries
- Captions JPG/JPEG/PNG images
- Preserves folder structure in output bucket

### `summarize_text.py`
Text-only summarization script:
- Focuses on JSON text content summarization
- Lighter weight for text-only use cases

## Quick Start Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/EerthineniAnupama/bocksummarizer.git
cd bocksummarizer
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Up AWS Credentials
Choose one of these methods:

#### Option A: Environment Variables (Recommended)
```bash
# Windows PowerShell
$env:AWS_ACCESS_KEY_ID="your_aws_access_key_here"
$env:AWS_SECRET_ACCESS_KEY="your_aws_secret_key_here"
$env:AWS_REGION="us-east-1"

# Linux/Mac
export AWS_ACCESS_KEY_ID="your_aws_access_key_here"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_key_here"
export AWS_REGION="us-east-1"
```

#### Option B: AWS CLI
```bash
aws configure
# Enter your AWS credentials when prompted
```

#### Option C: IAM Roles (for EC2 instances)
Use IAM roles instead of hardcoded credentials for better security.

### Step 4: Run the Scripts
```bash
# For text + image processing
python summarize_all.py --input-bucket YOUR_INPUT_BUCKET --output-bucket YOUR_OUTPUT_BUCKET

# For text-only processing
python summarize_text.py --input-bucket YOUR_INPUT_BUCKET --output-bucket YOUR_OUTPUT_BUCKET
```

## Example Usage

Here's a complete example of how to use the scripts:

```bash
# 1. Clone the repository
git clone https://github.com/EerthineniAnupama/bocksummarizer.git
cd bocksummarizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your AWS credentials (Windows PowerShell)
$env:AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$env:AWS_REGION="us-east-1"

# 4. Run the script with your actual bucket names
python summarize_all.py --input-bucket my-documents-bucket --output-bucket my-summaries-bucket
```

**Note:** Replace `my-documents-bucket` and `my-summaries-bucket` with your actual S3 bucket names.

## Usage

### Basic Usage
```bash
# Process both text and images
python summarize_all.py --input-bucket my-input-bucket --output-bucket my-output-bucket

# Process text only
python summarize_text.py --input-bucket my-input-bucket --output-bucket my-output-bucket
```

### Using Environment Variables
```bash
# Set default buckets
export INPUT_BUCKET="my-input-bucket"
export OUTPUT_BUCKET="my-output-bucket"

# Run without specifying buckets
python summarize_all.py
```

### Advanced Options
```bash
# Specify custom models
python summarize_all.py \
    --input-bucket my-input-bucket \
    --output-bucket my-output-bucket \
    --text-model facebook/bart-large-cnn \
    --image-model nlpconnect/vit-gpt2-image-captioning
```

## Output Format

### Text Summaries
Saved as `article_text_summary.json`:
```json
{
  "filename": "original_file.json",
  "summary_type": "text",
  "summary": "Generated summary text..."
}
```

### Image Summaries
Saved as `image_summary.json` or `filename_image_summary.json`:
```json
{
  "filename": "image.jpg",
  "summary_type": "image", 
  "summary": "Generated image caption..."
}
```

## Requirements

- Python 3.7+
- AWS credentials with S3 read/write permissions
- Sufficient disk space for model downloads
- GPU recommended for faster processing

## Models

- **Default Text Model**: `facebook/bart-large-cnn`
- **Default Image Model**: `nlpconnect/vit-gpt2-image-captioning`
- **Alternative Text Models**: `t5-base`, `google/pegasus-xsum`

## Troubleshooting

### Common Issues:

1. **"No AWS credentials found"**
   - Make sure you've set your AWS credentials using one of the methods above
   - Check that your AWS credentials have S3 read/write permissions

2. **"Access Denied" when accessing S3**
   - Verify your AWS credentials are correct
   - Ensure your AWS user has permissions for the S3 buckets you're trying to access

3. **"Model not found" errors**
   - Make sure you have an internet connection for downloading models
   - Check that transformers and torch are properly installed

4. **Out of memory errors**
   - Try using a smaller model: `--text-model t5-base`
   - Close other applications to free up memory
   - Consider using a machine with more RAM

## Security Note

⚠️ **Never commit AWS credentials to version control!**
- Use environment variables or AWS CLI configuration
- Add `.env` files and credential files to `.gitignore`
- Consider using IAM roles for production deployments
