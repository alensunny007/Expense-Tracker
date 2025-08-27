
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, datetime, timedelta
import logging
from .gmail_service import GmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DueExpenseMonitor:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.gmail_service = GmailService()
        self.app = app
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
        
        # Ensure scheduler shuts down when app stops
        import atexit
        atexit.register(lambda: self.scheduler.shutdown())
    
    def check_newly_due_expenses(self):
        """Check for expenses that became due since last check"""
        if self.app:
            with self.app.app_context():
                self._check_due_expenses()
        else:
            self._check_due_expenses()
    
    def _check_due_expenses(self):
        """Internal method to check due expenses"""
        try:
            # Import here to avoid circular imports
            from app.models import RecurringExpense, User
            from app.extensions import db
            
            current_date = date.today()
            logger.info(f"Checking for due expenses on {current_date}")
            
            # Find recurring expenses that are due for processing
            newly_due = RecurringExpense.query.filter(
                RecurringExpense.is_active == True,
                RecurringExpense.next_due_date <= current_date,
                # Either never processed OR last processed before current due date
                db.or_(
                    RecurringExpense.last_processed_date.is_(None),
                    RecurringExpense.last_processed_date < RecurringExpense.next_due_date
                )
            ).all()
            
            if newly_due:
                logger.info(f"Found {len(newly_due)} newly due recurring expenses")
                
                # Group by user for consolidated emails
                users_with_due = {}
                for recurring_expense in newly_due:
                    if recurring_expense.user_id not in users_with_due:
                        users_with_due[recurring_expense.user_id] = []
                    users_with_due[recurring_expense.user_id].append(recurring_expense)
                
                # Send notifications to each user
                for user_id, due_expenses in users_with_due.items():
                    user = User.query.get(user_id)
                    if user and self.should_send_notification(user):
                        self.send_due_notification(user, due_expenses)
            
            # Also check for overdue expenses (past due and not processed)
            overdue = RecurringExpense.query.filter(
                RecurringExpense.is_active == True,
                RecurringExpense.next_due_date < current_date,
                db.or_(
                    RecurringExpense.last_processed_date.is_(None),
                    RecurringExpense.last_processed_date < RecurringExpense.next_due_date
                )
            ).all()
            
            if overdue:
                logger.info(f"Found {len(overdue)} overdue recurring expenses")
                self.handle_overdue_expenses(overdue)
                
        except Exception as e:
            logger.error(f"Error checking due expenses: {str(e)}", exc_info=True)
    
    def should_send_notification(self, user):
        """Check if we should send notification to this user"""
        # Check if user has email notifications enabled (assuming you have this field)
        # If not, you can remove this check or add the field to your User model
        return True  # For now, always send
        
        # Uncomment if you have email preferences:
        # return getattr(user, 'email_notifications_enabled', True)
    
    def send_due_notification(self, user, due_expenses):
        """Send notification for due recurring expenses"""
        try:
            # Check if we already sent notification today for this user
            if self.already_notified_today(user, due_expenses):
                logger.info(f"Already notified {user.email} today, skipping")
                return
            
            html_content, text_content = self.gmail_service.create_due_expenses_email(
                user, due_expenses
            )
            
            # Determine email subject based on overdue vs due today
            overdue_count = len([exp for exp in due_expenses if exp.next_due_date < date.today()])
            due_today_count = len([exp for exp in due_expenses if exp.next_due_date == date.today()])
            
            if overdue_count > 0:
                subject = f" {overdue_count} Overdue + {due_today_count} Due Expenses"
            else:
                subject = f" {due_today_count} Expense(s) Due Today!"
            
            success = self.gmail_service.send_email(
                user.email,
                subject,
                html_content,
                text_content
            )
            
            if success:
                logger.info(f"Due notification sent successfully to {user.email}")
                self.mark_notification_sent(user, due_expenses)
            else:
                logger.error(f"Failed to send notification to {user.email}")
            
        except Exception as e:
            logger.error(f"Error sending due notification to {user.email}: {str(e)}")
    
    def handle_overdue_expenses(self, overdue_expenses):
        """Handle overdue expenses separately if needed"""
        # Group by user
        users_overdue = {}
        for expense in overdue_expenses:
            if expense.user_id not in users_overdue:
                users_overdue[expense.user_id] = []
            users_overdue[expense.user_id].append(expense)
        
        for user_id, expenses in users_overdue.items():
            from app.models import User
            user = User.query.get(user_id)
            
            if user and self.should_send_notification(user):
                # Check if it's been more than 24 hours since last overdue notification
                if self.should_send_overdue_reminder(user, expenses):
                    self.send_overdue_reminder(user, expenses)
    
    def send_overdue_reminder(self, user, overdue_expenses):
        """Send reminder for overdue expenses"""
        try:
            html_content, text_content = self.gmail_service.create_due_expenses_email(
                user, overdue_expenses
            )
            
            days_overdue = max((date.today() - exp.next_due_date).days for exp in overdue_expenses)
            subject = f" {len(overdue_expenses)} Overdue Expense(s) - {days_overdue} Days Past Due"
            
            success = self.gmail_service.send_email(
                user.email,
                subject,
                html_content,
                text_content
            )
            
            if success:
                logger.info(f"Overdue reminder sent to {user.email}")
                self.mark_overdue_notification_sent(user, overdue_expenses)
            
        except Exception as e:
            logger.error(f"Error sending overdue reminder to {user.email}: {str(e)}")
    
    def already_notified_today(self, user, due_expenses):
        """Check if user was already notified today about these expenses"""
        # Simple approach: check if any expense has a recent notification
        # You might want to add a last_notification_date field to RecurringExpense model
        return False  # For now, always send
        
        # If you add last_notification_date field to RecurringExpense:
        # today = date.today()
        # return any(
        #     getattr(exp, 'last_notification_date', None) == today 
        #     for exp in due_expenses
        # )
    
    def should_send_overdue_reminder(self, user, expenses):
        """Check if we should send overdue reminder"""
        # Send overdue reminders every 3 days to avoid spam
        return True  # For now, always send overdue reminders
    
    def mark_notification_sent(self, user, due_expenses):
        """Mark that notification was sent (optional enhancement)"""
        # If you want to track notifications, you can add a field to your model
        # and update it here
        pass
        
        # Example if you add last_notification_date to RecurringExpense:
        # from app.extensions import db
        # today = date.today()
        # for expense in due_expenses:
        #     expense.last_notification_date = today
        # db.session.commit()
    
    def mark_overdue_notification_sent(self, user, overdue_expenses):
        """Mark that overdue notification was sent"""
        # Similar to mark_notification_sent but for overdue tracking
        pass
    
    def get_user_due_expenses(self, user_id):
        """Get all due expenses for a specific user"""
        from app.models import RecurringExpense
        from app.extensions import db
        
        return RecurringExpense.query.filter(
            RecurringExpense.user_id == user_id,
            RecurringExpense.is_active == True,
            RecurringExpense.next_due_date <= date.today(),
            db.or_(
                RecurringExpense.last_processed_date.is_(None),
                RecurringExpense.last_processed_date < RecurringExpense.next_due_date
            )
        ).all()
    
    def start_monitoring(self):
        """Start monitoring for due expenses"""
        try:
            # Check every hour during business hours (8 AM to 8 PM)
            self.scheduler.add_job(
                self.check_newly_due_expenses,
                'cron',
                minute=0,  # At the top of every hour
                hour='8-20',
                id='hourly_due_expense_check',
                replace_existing=True
            )
            
            # Check at midnight for day rollover
            self.scheduler.add_job(
                self.check_newly_due_expenses,
                'cron',
                hour=0,
                minute=1,
                id='midnight_due_check',
                replace_existing=True
            )
            
            # Morning notification at 9 AM
            self.scheduler.add_job(
                self.check_newly_due_expenses,
                'cron',
                hour=9,
                minute=0,
                id='morning_due_notification',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("Due expense monitoring started successfully")
            logger.info("Scheduled jobs:")
            for job in self.scheduler.get_jobs():
                logger.info(f"  - {job.id}: {job.trigger}")
            
        except Exception as e:
            logger.error(f"Error starting due expense monitor: {str(e)}")
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Due expense monitoring stopped")
    
    def force_check_now(self):
        """Manual trigger for immediate check (useful for testing)"""
        logger.info("Manual due expense check triggered")
        self.check_newly_due_expenses()
        
    def get_monitoring_status(self):
        """Get status of the monitoring service"""
        return {
            'running': self.scheduler.running,
            'jobs': [
                {
                    'id': job.id,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                for job in self.scheduler.get_jobs()
            ]
        }