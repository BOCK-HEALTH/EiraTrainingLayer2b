#!/bin/bash
echo "================================================================================"
echo "Installing BOCK Scraper Dependencies in Virtual Environment"
echo "================================================================================"
echo ""

# Activate virtual environment
source web_venv/bin/activate

echo "Installing scraping libraries..."
pip install trafilatura newspaper3k scrapy beautifulsoup4 lxml Pillow requests aiohttp

echo ""
echo "Installing AI/ML libraries for summarization..."
pip install transformers torch --index-url https://download.pytorch.org/whl/cpu

echo ""
echo "Installing web server libraries..."
pip install Flask Flask-CORS

echo ""
echo "================================================================================"
echo "Installation Complete!"
echo "================================================================================"
echo ""
echo "You can now run: python web_server_local.py"
echo ""

