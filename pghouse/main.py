import os
import smtplib
import psycopg2
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json

from dotenv import load_dotenv
load_dotenv(".env")

def get_new_contacts(database_url, last_check_time):
    """
    Fetch contacts added since the last check time.
    """
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Query to get new contacts since last check
        # Handle both DATE type and VARCHAR/TEXT type columns
        query = """
            SELECT id, username, email, phone, message, dateofcontact 
            FROM contact_form_submissions 
            WHERE dateofcontact >= %s
            ORDER BY dateofcontact DESC, id DESC
        """
        
        cursor.execute(query, (last_check_time,))
        rows = cursor.fetchall()
        
        contacts = []
        for row in rows:
            # Handle dateofcontact - could be string, date, or datetime
            date_value = row[5]
            if date_value:
                if isinstance(date_value, str):
                    # Already a string, use as-is
                    formatted_date = date_value
                else:
                    # It's a date or datetime object
                    formatted_date = date_value.strftime('%Y-%m-%d')
            else:
                formatted_date = None
            
            contacts.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'phone': row[3],
                'message': row[4],
                'dateofcontact': formatted_date
            })
        
        cursor.close()
        conn.close()
        
        return contacts
    
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()
        return []

def create_email_body(contacts):
    """
    Create HTML email body with contact details in a beautiful table format.
    Ultra-smooth and user-friendly with card-based mobile layout.
    """
    if not contacts:
        return None
    
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{
                    box-sizing: border-box;
                }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background-color: #f4f7f9;
                    margin: 0;
                    padding: 0;
                    -webkit-text-size-adjust: 100%;
                    -ms-text-size-adjust: 100%;
                }}
                .container {{ 
                    max-width: 900px; 
                    margin: 20px auto; 
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                    overflow: hidden;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; 
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{ 
                    margin: 0 0 8px 0;
                    font-size: 32px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .header p {{
                    margin: 0;
                    opacity: 0.95;
                    font-size: 16px;
                    font-weight: 400;
                }}
                .summary {{ 
                    padding: 24px 30px;
                    background: linear-gradient(to right, #f8f9fa 0%, #ffffff 100%);
                    border-left: 5px solid #667eea;
                    margin: 25px 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
                }}
                .summary p {{ 
                    margin: 0;
                    font-size: 17px;
                    color: #2c3e50;
                    font-weight: 500;
                }}
                .badge {{
                    display: inline-block;
                    padding: 6px 14px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 20px;
                    font-size: 15px;
                    font-weight: 700;
                    margin: 0 4px;
                    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                }}
                
                /* Desktop Table View */
                .table-container {{
                    padding: 0 30px 30px 30px;
                    overflow-x: auto;
                    -webkit-overflow-scrolling: touch;
                }}
                table {{ 
                    width: 100%; 
                    border-collapse: separate;
                    border-spacing: 0;
                    background-color: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
                }}
                thead {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                th {{ 
                    padding: 18px 16px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    white-space: nowrap;
                }}
                th:first-child {{
                    border-top-left-radius: 10px;
                }}
                th:last-child {{
                    border-top-right-radius: 10px;
                }}
                td {{ 
                    padding: 18px 16px;
                    border-bottom: 1px solid #f0f0f0;
                    font-size: 14px;
                    color: #2c3e50;
                    vertical-align: top;
                }}
                tr:last-child td {{
                    border-bottom: none;
                }}
                tr:last-child td:first-child {{
                    border-bottom-left-radius: 10px;
                }}
                tr:last-child td:last-child {{
                    border-bottom-right-radius: 10px;
                }}
                tbody tr {{
                    transition: all 0.3s ease;
                }}
                tbody tr:hover {{ 
                    background-color: #f8f9fe;
                    transform: scale(1.01);
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
                }}
                tbody tr:nth-child(even) {{
                    background-color: #fafbfc;
                }}
                .name-column {{
                    font-weight: 600;
                    color: #1a202c;
                    font-size: 15px;
                }}
                .email-column {{
                    color: #0066cc;
                    word-break: break-word;
                }}
                .email-column a {{
                    color: #0066cc;
                    text-decoration: none;
                }}
                .phone-column {{
                    font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
                    color: #262222;
                    font-weight: 500;
                    white-space: nowrap;
                }}
                .date-column {{
                    color: #64748b;
                    font-size: 13px;
                    white-space: nowrap;
                }}
                .message-column {{
                    max-width: 320px;
                    line-height: 1.7;
                    word-wrap: break-word;
                    color: #475569;
                }}
                
                /* Mobile Card View */
                .mobile-cards {{
                    display: none;
                }}
                .contact-card {{
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 15px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
                    border-left: 4px solid #667eea;
                    transition: all 0.3s ease;
                }}
                .contact-card:hover {{
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
                    transform: translateY(-2px);
                }}
                .card-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                    padding-bottom: 12px;
                    border-bottom: 2px solid #f0f0f0;
                }}
                .card-name {{
                    font-size: 18px;
                    font-weight: 700;
                    color: #1a202c;
                    margin: 0;
                }}
                .card-date {{
                    font-size: 12px;
                    color: #94a3b8;
                    background: #f1f5f9;
                    padding: 4px 10px;
                    border-radius: 12px;
                }}
                .card-field {{
                    margin: 12px 0;
                    display: flex;
                    align-items: flex-start;
                }}
                .card-label {{
                    font-size: 12px;
                    font-weight: 600;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    min-width: 70px;
                    margin-right: 12px;
                    margin-top: 2px;
                }}
                .card-value {{
                    font-size: 14px;
                    color: #2c3e50;
                    flex: 1;
                    word-break: break-word;
                }}
                .card-value.email {{
                    color: #0066cc;
                }}
                .card-value.phone {{
                    color: #10b981;
                    font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
                    font-weight: 500;
                }}
                .card-value.message {{
                    line-height: 1.7;
                    color: #475569;
                    background: #f8fafc;
                    padding: 12px;
                    border-radius: 8px;
                    margin-top: 4px;
                }}
                
                .footer {{ 
                    margin-top: 30px;
                    padding: 25px 30px;
                    background: linear-gradient(to right, #f8f9fa 0%, #ffffff 100%);
                    text-align: center; 
                    color: #64748b;
                    font-size: 13px;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer p {{
                    margin: 6px 0;
                }}
                .footer strong {{
                    color: #475569;
                }}
                
                @media only screen and (max-width: 768px) {{
                    .container {{
                        margin: 0;
                        border-radius: 0;
                    }}
                    .header {{
                        padding: 30px 20px;
                    }}
                    .header h1 {{
                        font-size: 24px;
                    }}
                    .header p {{
                        font-size: 14px;
                    }}
                    .summary {{
                        margin: 20px 15px;
                        padding: 18px 20px;
                    }}
                    .summary p {{
                        font-size: 15px;
                    }}
                    .badge {{
                        padding: 5px 12px;
                        font-size: 14px;
                    }}
                    
                    /* Hide table on mobile */
                    .table-container {{
                        display: none;
                    }}
                    
                    /* Show cards on mobile */
                    .mobile-cards {{
                        display: block;
                        padding: 0;
                    }}
                    
                    .footer {{
                        padding: 20px 15px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📬 Contact Form Submissions</h1>
                    <p>New inquiries from your website</p>
                </div>
                
                <div class="summary">
                    <p>You have received <span class="badge">{count}</span> new contact form submission(s)</p>
                </div>
                
                <!-- Desktop Table View -->
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Date</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody>
    """.format(count=len(contacts))
    
    # Add table rows
    for contact in contacts:
        username = contact['username'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        email = contact['email'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        phone = contact['phone'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        message = contact['message'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        
        html += f"""
                            <tr>
                                <td class="name-column">{username}</td>
                                <td class="email-column">{email}</td>
                                <td class="phone-column">{phone}</td>
                                <td class="date-column">{contact['dateofcontact']}</td>
                                <td class="message-column">{message}</td>
                            </tr>
        """
    
    html += """
                        </tbody>
                    </table>
                </div>
                
                <!-- Mobile Card View -->
                <div class="mobile-cards">
    """
    
    # Add mobile cards
    for contact in contacts:
        username = contact['username'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        email = contact['email'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        phone = contact['phone'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        message = contact['message'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
        
        html += f"""
                    <div class="contact-card">
                        <div class="card-header">
                            <h3 class="card-name">{username}</h3>
                            <span class="card-date">{contact['dateofcontact']}</span>
                        </div>
                        <div class="card-field">
                            <span class="card-label">Email</span>
                            <span class="card-value email">{email}</span>
                        </div>
                        <div class="card-field">
                            <span class="card-label">Phone</span>
                            <span class="card-value phone">{phone}</span>
                        </div>
                        <div class="card-field">
                            <span class="card-label">Message</span>
                            <div class="card-value message">{message}</div>
                        </div>
                    </div>
        """
    
    html += """
                </div>
                
                <div class="footer">
                    <p><strong>📧 Automated Contact Form Notification</strong></p>
                    <p>This email was automatically generated by your contact form monitoring system.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return html

def send_email(recipient_emails, subject, html_body, smtp_config):
    """
    Send email using SMTP to multiple recipients.
    recipient_emails can be a string (single email) or list of emails.
    """
    try:
        # Handle both string and list inputs
        if isinstance(recipient_emails, str):
            # Split by comma if multiple emails in string
            recipients = [email.strip() for email in recipient_emails.split(',')]
        else:
            recipients = recipient_emails
        
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_config['from_email']
        msg['To'] = ', '.join(recipients)  # Join all recipients for display
        msg['Subject'] = subject
        
        # Attach HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
        
        print(f"Email sent successfully to {len(recipients)} recipient(s)")
        return True
    
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def main():
    # Get environment variables
    database_url = os.getenv('DATABASE_URL')
    recipient_email = os.getenv('RECIPIENT_EMAIL')  # Can be comma-separated emails
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL', smtp_username)
    check_interval_hours = int(os.getenv('CHECK_INTERVAL_HOURS', '24'))
    
    # Validate required environment variables
    required_vars = {
        'DATABASE_URL': database_url,
        'RECIPIENT_EMAIL': recipient_email,
        'SMTP_USERNAME': smtp_username,
        'SMTP_PASSWORD': smtp_password
    }
    
    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    # Parse recipient emails (supports comma-separated list)
    if ',' in recipient_email:
        recipients = [email.strip() for email in recipient_email.split(',')]
        print(f"Will send notifications to {len(recipients)} recipients")
    else:
        recipients = recipient_email
        print(f"Will send notification to recipients")
    
    # Calculate last check time
    last_check_time = (datetime.now() - timedelta(hours=check_interval_hours)).strftime('%Y-%m-%d')
    
    print(f"Checking for contacts since: {last_check_time}")
    
    # Fetch new contacts
    contacts = get_new_contacts(database_url, last_check_time)
    
    if not contacts:
        print("No new contacts found.")
        return
    
    print(f"Found {len(contacts)} new contact(s)")
    
    # Create email body
    html_body = create_email_body(contacts)
    
    if not html_body:
        print("Failed to create email body")
        return
    
    # SMTP configuration
    smtp_config = {
        'server': smtp_server,
        'port': smtp_port,
        'username': smtp_username,
        'password': smtp_password,
        'from_email': from_email
    }
    
    # Send email
    subject = f"New Contact Form Submissions - {len(contacts)} New Contact(s)"
    send_email(recipients, subject, html_body, smtp_config)

if __name__ == "__main__":
    main()