# services/gmail_service.py
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from datetime import date

class GmailService:
    def __init__(self):
        self.SCOPES=['https://www.googleapis.com/auth/gmail.send']
        self.credentials=None
        self.service=None
        
    def get_gmail_service(self):
        try:
            creds = Credentials.from_authorized_user_info({
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),  
                'token_uri': 'https://oauth2.googleapis.com/token'
            })
            
            # Add token refresh check
            if creds.expired:
                creds.refresh(Request())
                
            self.service=build('gmail','v1',credentials=creds)
            return self.service
        except Exception as e:
            print(f"Error creating gmail service: {str(e)}")
            return None
            
    def create_message(self,sender,to,subject,html_body,text_body=None):
        try:
            message=MIMEMultipart('alternative')
            message['to']=to
            message['from']=sender
            message['subject']=subject

            if text_body:
                text_part=MIMEText(text_body,'plain')
                message.attach(text_part)
            html_part=MIMEText(html_body,'html')
            message.attach(html_part)

            raw_message=base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            return {'raw':raw_message}
        except Exception as e:
            print(f"Error creating message:{str(e)}")
            return None
            
    def send_email(self,to_email,subject,html_body,text_body=None):
        try:
            service=self.get_gmail_service()
            if not service:
                return False
            sender=os.getenv('GMAIL_SENDER_EMAIL')
            message=self.create_message(sender,to_email,subject,html_body,text_body)
            if not message:
                return False
            res=service.users().messages().send(userId='me',body=message).execute()
            print(f"Email sent successfully. Message ID: {res['id']}")
            return True
        except HttpError as e:
            print(f"Gmail api error: {e}")
            return False
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
            
    def create_due_expenses_email(self, user, due_expenses):

        total_amount = sum(float(exp.amount) for exp in due_expenses)
        overdue_expenses = [exp for exp in due_expenses if exp.next_due_date < date.today()]
        due_today = [exp for exp in due_expenses if exp.next_due_date == date.today()]
        
        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Due Expenses Notification</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; }}
                .header {{ background: #e53e3e; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; }}
                .expense-item {{ background: #f8f9fa; border-left: 4px solid #e53e3e; margin: 10px 0; padding: 15px; border-radius: 4px; }}
                .overdue {{ border-left-color: #dc3545; }}
                .due-today {{ border-left-color: #ffc107; }}
                .amount {{ font-weight: bold; color: #e53e3e; font-size: 18px; }}
                .total-box {{ background: #e9ecef; padding: 20px; margin: 20px 0; text-align: center; border-radius: 8px; }}
                .button {{ display: inline-block; background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 5px; }}
                .footer {{ background: #6c757d; color: white; text-align: center; padding: 15px; font-size: 14px; }}
                .badge {{ padding: 4px 8px; border-radius: 12px; font-size: 12px; color: white; }}
                .badge-danger {{ background: #dc3545; }}
                .badge-warning {{ background: #ffc107; color: #333; }}
                .frequency {{ font-size: 12px; background: #17a2b8; color: white; padding: 2px 6px; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2> Expense Tracker Reminder</h2>
                    <p>Hello {getattr(user, 'first_name', user.username) if hasattr(user, 'first_name') else user.username}, you have {len(due_expenses)} recurring expense(s) due for processing!</p>
                </div>
                
                <div class="content">
                    <div class="total-box">
                        <h3>Total Amount Due: ₹{total_amount:.2f}</h3>
                        <p>
                            {len(overdue_expenses)} overdue • {len(due_today)} due today
                        </p>
                    </div>
                    
                    <h3> Due Recurring Expenses:</h3>
        """
        
        # Add each expense
        for expense in due_expenses:
            status_class = "overdue" if expense.next_due_date < date.today() else "due-today"
            status_text = "OVERDUE" if expense.next_due_date < date.today() else "DUE TODAY"
            badge_class = "badge-danger" if expense.next_due_date < date.today() else "badge-warning"
            
            # Calculate days overdue/until due
            days_diff = (date.today() - expense.next_due_date).days
            if days_diff > 0:
                days_text = f"{days_diff} days overdue"
            elif days_diff == 0:
                days_text = "Due today"
            else:
                days_text = f"Due in {abs(days_diff)} days"
            
            html_content += f"""
                    <div class="expense-item {status_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <h4 style="margin: 0; color: #333;">{expense.title}</h4>
                                <p style="margin: 5px 0; color: #666;">
                                    {expense.category.name} • 
                                    <span class="frequency">{expense.frequency.title()}</span>
                                </p>
                                <p style="margin: 5px 0; font-size: 14px; color: #666;">
                                    Due: {expense.next_due_date.strftime('%d %b %Y')} • {days_text}
                                </p>
                                {f'<p style="margin: 5px 0; font-size: 12px; color: #888;">{expense.description}</p>' if expense.description else ''}
                            </div>
                            <div style="text-align: right;">
                                <div class="amount">₹{float(expense.amount):.2f}</div>
                                <span class="badge {badge_class}">{status_text}</span>
                            </div>
                        </div>
                    </div>
            """
        
        # Close HTML
        html_content += f"""
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{os.getenv('APP_BASE_URL', 'http://localhost:5000')}/process-due" class="button">
                             Process Due Expenses
                        </a>
                        <a href="{os.getenv('APP_BASE_URL', 'http://localhost:5000')}/recurring-expenses" class="button" style="background: #6c757d;">
                             View All Recurring Expenses
                        </a>
                    </div>
                    
                    <div style="margin-top: 30px; padding: 15px; background: #e3f2fd; border-radius: 6px;">
                        <h4 style="color: #1976d2; margin-top: 0;">💡 Quick Tip:</h4>
                        <p style="margin-bottom: 0; color: #1565c0;">
                            Processing these expenses will add them to your expense records and automatically update their next due dates based on their frequency.
                        </p>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 6px; border-left: 4px solid #17a2b8;">
                        <h4 style="color: #17a2b8; margin-top: 0;"> Frequency Info:</h4>
                        <ul style="margin: 0; color: #555;">
        """
        
        # Add frequency breakdown
        frequency_counts = {}
        for exp in due_expenses:
            freq = exp.frequency.title()
            frequency_counts[freq] = frequency_counts.get(freq, 0) + 1
        
        for freq, count in frequency_counts.items():
            html_content += f"<li>{count} {freq} expense{'s' if count > 1 else ''}</li>"
        
        html_content += """
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from your Expense Tracker app.</p>
                    <p style="font-size: 12px;">
                        Don't want these emails? 
                        <a href="{}/settings" style="color: #ffc107;">Update your preferences</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """.format(os.getenv('APP_BASE_URL', 'http://localhost:5000'))
        
        # Create text version (fallback)
        text_content = f"""
        EXPENSE TRACKER REMINDER
        
        Hello {getattr(user, 'first_name', user.username) if hasattr(user, 'first_name') else user.username}!
        
        You have {len(due_expenses)} recurring expense(s) due for processing:
        Total Amount: ₹{total_amount:.2f}
        
        Due Recurring Expenses:
        """
        
        for expense in due_expenses:
            status = "OVERDUE" if expense.next_due_date < date.today() else "DUE TODAY"
            text_content += f"• {expense.title} - ₹{float(expense.amount):.2f} ({expense.frequency.title()}) - {status}\n"
            text_content += f"  Due: {expense.next_due_date.strftime('%d %b %Y')}\n"
            if expense.description:
                text_content += f"  Note: {expense.description}\n"
            text_content += "\n"
        
        text_content += f"""
        Process your expenses: {os.getenv('APP_BASE_URL', 'http://localhost:5000')}/process-due
        View all recurring expenses: {os.getenv('APP_BASE_URL', 'http://localhost:5000')}/recurring-expenses
        
        ---
        This is an automated notification from your Expense Tracker app.
        """
        
        return html_content, text_content