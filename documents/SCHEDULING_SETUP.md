# Automated Scheduling Setup Complete ✅

## 🎯 What Was Implemented

### 1. **Celery Task Scheduler**
   - ✅ Celery 5.4.0 installed with Redis broker
   - ✅ Django-Celery-Beat for database-driven scheduling
   - ✅ All tasks configured but **DISABLED by default** for safety

### 2. **Scheduled Tasks Created**
   
   | Task | Schedule | Description | Status |
   |------|----------|-------------|--------|
   | **Twice-Daily Scraping** | 00:00 & 12:00 UTC | Run all enabled scrapers automatically | 🔴 OFF |
   | **Job Expiry** | Daily 01:00 UTC | Mark jobs older than 30 days as expired | 🔴 OFF |
   | **Job Recheck** | Daily 02:00 UTC | Verify active jobs still exist online | 🔴 OFF |
   | **Daily Report** | Daily 23:00 UTC | Generate and email CSV report | 🔴 OFF |
   | **Weekly Summary** | Sunday 09:00 UTC | Email weekly statistics | 🔴 OFF |
   | **Health Check** | Hourly | Alert if scrapers fail or no data found | 🔴 OFF |
   | **Senior Role Alerts** | Real-time | Email when senior jobs found | 🔴 OFF |

### 3. **Admin Panel Control**
   - ✅ New **Schedule Configuration** page in admin panel
   - ✅ Master ON/OFF switch for all scheduling
   - ✅ Individual toggles for each feature
   - ✅ Email configuration for reports and alerts
   - ✅ Customizable job expiry days (default: 30)
   - ✅ Customizable scraper run times

---

## 🔧 How to Enable Scheduling

### **Step 1: Start Celery Services** (One-time setup)

```bash
cd "/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain"

# Check if Redis is running
redis-cli ping  # Should return "PONG"

# If Redis not installed:
sudo apt-get update && sudo apt-get install -y redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Install services
sudo cp celery-worker.service /etc/systemd/system/
sudo cp celery-beat.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start Celery services
sudo systemctl start celery-worker
sudo systemctl start celery-beat

# Enable on boot
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat

# Check status
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

### **Step 2: Enable Scheduling from Admin Panel**

1. **Navigate to Admin:**
   ```
   http://your-domain/admin/jobs/scheduleconfig/1/change/
   ```

2. **Configure Settings:**
   
   **🔴 MASTER CONTROL:**
   - ✅ Check "Scheduling enabled" - This is the MAIN switch
   
   **🤖 SCRAPER AUTOMATION:**
   - ✅ Check "Scraper schedule enabled"
   - Set "Scraper run times": `0:00,12:00` (midnight & noon UTC)
   
   **🗑️ JOB EXPIRY:**
   - ✅ Check "Job expiry enabled"
   - Set "Job expiry days": `30` (or your preference)
   
   **📊 REPORTS:**
   - ✅ Check "Daily reports enabled" (optional)
   - ✅ Check "Weekly reports enabled" (optional)
   - Enter "Report email recipients": `admin@example.com, team@example.com`
   
   **🚨 ALERTS:**
   - ✅ Check "Senior role alerts enabled" (optional)
   - ✅ Check "Health check alerts enabled"
   - Enter "Alert email recipients": `ops@example.com`
   
   **💾 Save!**

3. **Configure Email Settings** (in `.env` or settings.py):
   ```bash
   # Edit .env file
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=1
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   DEFAULT_FROM_EMAIL=noreply@aeroops.com
   ```

---

## 📊 Monitoring & Management

### **Check Celery Status:**
```bash
# Check worker status
sudo systemctl status celery-worker

# Check beat scheduler status
sudo systemctl status celery-beat

# View worker logs
sudo journalctl -u celery-worker -f

# View beat logs
sudo journalctl -u celery-beat -f

# Or check log files:
tail -f logs/celery-worker.log
tail -f logs/celery-beat.log
```

### **Test Tasks Manually:**
```python
# Python shell
python manage.py shell

# Test scraper task
from jobs.tasks import scheduled_scraper_run
result = scheduled_scraper_run.delay(trigger='manual_test')
print(f"Task ID: {result.id}")

# Test email alert
from jobs.tasks import notify_new_senior_roles
notify_new_senior_roles.delay()

# Check task result
from django_celery_results.models import TaskResult
TaskResult.objects.all().order_by('-date_done')[:5]
```

### **Admin Panel Views:**
```
http://your-domain/admin/jobs/scheduleconfig/        # Schedule settings
http://your-domain/admin/django_celery_beat/         # Periodic tasks
http://your-domain/admin/django_celery_results/      # Task results
```

---

## 🚀 What Happens When Enabled

### **Automatic Twice-Daily Scraping:**
1. At **00:00 UTC** and **12:00 UTC** daily
2. All enabled scrapers run automatically
3. New jobs saved to database
4. Senior roles trigger email alerts
5. Execution logged in ScraperJob table

### **Job Expiry (Daily at 01:00 UTC):**
1. Finds jobs older than 30 days (configurable)
2. Updates status from "active" → "expired"
3. Logs count of expired jobs

### **Job Rechecking (Daily at 02:00 UTC):**
1. Samples 50 random active jobs not checked in 7+ days
2. Checks if URL still exists (HTTP HEAD request)
3. Marks as "expired" if 404/removed

### **Daily Report (23:00 UTC):**
1. Generates CSV with today's jobs
2. Sorts by Country → Operation Type → Date
3. Emails to configured recipients

### **Weekly Summary (Sunday 09:00 UTC):**
1. Aggregates last 7 days statistics
2. Shows top countries, companies, operation types
3. Highlights senior roles
4. Emails formatted summary

### **Health Checks (Hourly):**
1. Verifies each scraper ran in last 24 hours
2. Checks major countries (US, UK, UAE, etc.) have jobs
3. Sends alert email if issues detected

### **Senior Role Alerts (Real-time):**
1. Triggers after each scraper run
2. Finds senior jobs created in last hour
3. Emails list of new senior positions

---

## ⚙️ Configuration Options

### **Via Admin Panel:**
| Setting | Default | Description |
|---------|---------|-------------|
| `scheduling_enabled` | `False` | **Master switch** - disables ALL tasks when OFF |
| `scraper_schedule_enabled` | `True` | Enable twice-daily scraping |
| `scraper_run_times` | `"0:00,12:00"` | Times to run scrapers (HH:MM, UTC) |
| `job_expiry_enabled` | `True` | Auto-expire old jobs |
| `job_expiry_days` | `30` | Days before job expires |
| `daily_reports_enabled` | `False` | Generate daily CSV reports |
| `weekly_reports_enabled` | `False` | Generate weekly summaries |
| `senior_role_alerts_enabled` | `False` | Email alerts for senior roles |
| `health_check_alerts_enabled` | `True` | Alert on scraper failures |
| `report_email_recipients` | `""` | Comma-separated emails for reports |
| `alert_email_recipients` | `""` | Comma-separated emails for alerts |

### **Via Environment Variables (.env):**
```bash
# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@aeroops.com
```

---

## 🛑 Troubleshooting

### **Celery not starting:**
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Check logs
sudo journalctl -u celery-worker -n 50
sudo journalctl -u celery-beat -n 50

# Restart services
sudo systemctl restart celery-worker celery-beat
```

### **Tasks not running:**
1. Check "Scheduling enabled" is **TRUE** in admin
2. Verify Celery Beat is running: `systemctl status celery-beat`
3. Check Redis connection: `redis-cli ping`
4. View beat log: `tail -f logs/celery-beat.log`

### **Emails not sending:**
1. Check email settings in `.env`
2. For Gmail, enable "App Passwords"
3. Test email: `python manage.py shell`
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Test email', 'from@example.com', ['to@example.com'])
   ```

### **View task execution history:**
```bash
# Django admin
http://your-domain/admin/django_celery_results/taskresult/

# Or in shell:
python manage.py shell
from django_celery_results.models import TaskResult
TaskResult.objects.filter(task_name='jobs.tasks.scheduled_scraper_run').order_by('-date_done')[:10]
```

---

## 🔒 Safety Features

1. **Disabled by Default:** All scheduling OFF until you enable it
2. **Master Kill Switch:** One toggle disables everything
3. **Graceful Shutdown:** Services can be stopped without data loss
4. **Error Handling:** Failed tasks logged, don't crash system
5. **Rate Limiting:** Tasks won't pile up if previous run still active
6. **Health Monitoring:** System alerts you if something breaks

---

## 📝 Next Steps

1. ✅ **Start Celery services** (follow Step 1 above)
2. ✅ **Configure email settings** in `.env`
3. ✅ **Enable scheduling** from admin panel (Step 2)
4. ✅ **Test manually** to verify it works
5. ✅ **Monitor logs** for first few days
6. ✅ **Adjust schedules** as needed (change run times, expiry days, etc.)

---

## 📞 Commands Cheat Sheet

```bash
# Start services
sudo systemctl start celery-worker celery-beat

# Stop services
sudo systemctl stop celery-worker celery-beat

# Restart services
sudo systemctl restart celery-worker celery-beat

# Enable on boot
sudo systemctl enable celery-worker celery-beat

# Check status
sudo systemctl status celery-worker
sudo systemctl status celery-beat

# View logs
sudo journalctl -u celery-worker -f
sudo journalctl -u celery-beat -f

# Test task manually
python manage.py shell
>>> from jobs.tasks import scheduled_scraper_run
>>> scheduled_scraper_run.delay()

# Check Redis
redis-cli ping
redis-cli info

# View scheduled tasks in database
python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
```

---

**🎉 Congratulations!** Your automated scheduling system is ready. It's **OFF** by default for safety - enable it when you're ready from the admin panel!
