# Configuration
EC2_HOST = "54.82.140.246"
EC2_USER = "ec2-user" 
EC2_KEY_PATH = r"C:\Internship\key-scraper.pem"
EC2_SCRAPER_PATH = "/home/ec2-user/ultimate_scraper_v2.py"
EC2_ENV_PATH = "/home/ec2-user/ultimate_scraper_env/bin/activate"

# S3 Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'bockscraper')
S3_TEXT_BUCKET_NAME = 'bockscraper1'  # Hard-coded for text conversion
AWS_ACCESS_KEY_ID = 'AKIA5IK3AWDA3ITLCHFL'  # Hard-coded AWS credentials
AWS_SECRET_ACCESS_KEY = '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'  # Hard-coded AWS credentials
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
