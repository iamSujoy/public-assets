# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="your-database-url"
export RECIPIENT_EMAIL="your-email@example.com,test@test.com"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export CHECK_INTERVAL_HOURS="24"

# Run the script
python main.py