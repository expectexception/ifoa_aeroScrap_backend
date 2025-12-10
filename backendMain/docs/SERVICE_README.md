# AeroOps Backend System Service

This guide explains how to set up the AeroOps backend to start automatically when your system boots.

## Quick Setup

Run the setup script:

```bash
cd /home/rajat/Desktop/AeroOps\ Intel/aeroScrap_backend/backendMain
sudo bash setup_service.sh
```

This will:
1. Install Gunicorn (production WSGI server)
2. Create logs directory
3. Copy the service file to systemd
4. Enable the service to start on boot
5. Start the service immediately

## Manual Setup (Alternative)

If you prefer to set it up manually:

### 1. Install Gunicorn

```bash
cd /home/rajat/Desktop/AeroOps\ Intel/aeroScrap_backend/backendMain
.venv/bin/pip install gunicorn whitenoise
```

### 2. Copy Service File

```bash
sudo cp aeroops-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 3. Enable and Start Service

```bash
sudo systemctl enable aeroops-backend.service
sudo systemctl start aeroops-backend.service
```

## Service Management Commands

### Check Status
```bash
sudo systemctl status aeroops-backend
```

### Start Service
```bash
sudo systemctl start aeroops-backend
```

### Stop Service
```bash
sudo systemctl stop aeroops-backend
```

### Restart Service
```bash
sudo systemctl restart aeroops-backend
```

### Disable Auto-Start
```bash
sudo systemctl disable aeroops-backend
```

### Enable Auto-Start
```bash
sudo systemctl enable aeroops-backend
```

## View Logs

### Live Logs (follow)
```bash
sudo journalctl -u aeroops-backend -f
```

### Last 100 Lines
```bash
sudo journalctl -u aeroops-backend -n 100
```

### Logs Since Boot
```bash
sudo journalctl -u aeroops-backend -b
```

### Gunicorn Access Logs
```bash
tail -f logs/gunicorn-access.log
```

### Gunicorn Error Logs
```bash
tail -f logs/gunicorn-error.log
```

## Configuration

The service file is located at: `/etc/systemd/system/aeroops-backend.service`

### Key Settings:

- **Workers**: 3 (adjust based on CPU cores: `2-4 × CPU cores`)
- **Bind Address**: `0.0.0.0:8000` (accessible from all interfaces)
- **Timeout**: 120 seconds
- **Restart Policy**: Always restart on failure

### To Change Settings:

1. Edit the service file:
   ```bash
   sudo nano /etc/systemd/system/aeroops-backend.service
   ```

2. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart aeroops-backend
   ```

## Troubleshooting

### Service Won't Start

1. Check service status:
   ```bash
   sudo systemctl status aeroops-backend
   ```

2. View detailed logs:
   ```bash
   sudo journalctl -u aeroops-backend -n 50 --no-pager
   ```

3. Check if port 8000 is already in use:
   ```bash
   sudo lsof -i :8000
   ```

### Permission Issues

If you see permission errors:
```bash
sudo chown -R rajat:rajat /home/rajat/Desktop/AeroOps\ Intel/aeroScrap_backend/backendMain
chmod +x /home/rajat/Desktop/AeroOps\ Intel/aeroScrap_backend/backendMain/.venv/bin/gunicorn
```

### Database Connection Issues

Ensure PostgreSQL is running and starts before the backend:
```bash
sudo systemctl status postgresql
sudo systemctl enable postgresql
```

### Static Files Not Loading

Run collectstatic:
```bash
cd /home/rajat/Desktop/AeroOps\ Intel/aeroScrap_backend/backendMain
.venv/bin/python manage.py collectstatic --noinput
```

## Performance Tuning

### Adjust Workers

Edit the service file and change `--workers 3` to:
- Light load: 2 workers
- Medium load: 3-4 workers  
- Heavy load: `(2 × CPU cores) + 1`

Example for 4 CPU cores:
```bash
--workers 9 \
```

### Add Threading

For I/O-bound applications, add threads:
```bash
--workers 3 \
--threads 2 \
```

### Increase Timeout

For long-running requests:
```bash
--timeout 300 \
```

## Testing

### Test Service Status
```bash
sudo systemctl status aeroops-backend
```

### Test API Endpoint
```bash
curl http://localhost:8000/api/health/
```

### Test After Reboot
```bash
sudo reboot
# After reboot
sudo systemctl status aeroops-backend
curl http://localhost:8000/api/health/
```

## Security Notes

The service includes security hardening:
- `NoNewPrivileges=true` - Prevents privilege escalation
- `PrivateTmp=true` - Isolated temporary directory
- Runs as non-root user `rajat`

## Production Recommendations

For production use, consider:

1. **Nginx Reverse Proxy**: Put Nginx in front of Gunicorn
   - Better static file serving
   - SSL/TLS termination
   - Load balancing

2. **Environment Variables**: Use a `.env` file for sensitive data
   - Update service file: `EnvironmentFile=/path/to/.env`

3. **Monitoring**: Set up monitoring tools
   - Prometheus + Grafana
   - New Relic
   - DataDog

4. **Logging**: Configure log rotation
   ```bash
   sudo nano /etc/logrotate.d/aeroops-backend
   ```

5. **Firewall**: Configure firewall rules
   ```bash
   sudo ufw allow 8000/tcp
   ```

## Uninstall

To remove the service:

```bash
# Stop and disable service
sudo systemctl stop aeroops-backend
sudo systemctl disable aeroops-backend

# Remove service file
sudo rm /etc/systemd/system/aeroops-backend.service
sudo systemctl daemon-reload
```

## Support

If you encounter issues:
1. Check logs: `sudo journalctl -u aeroops-backend -n 100`
2. Verify database connection: `python manage.py check`
3. Test migrations: `python manage.py migrate --check`
4. Review Django logs: `tail -f logs/django.log`
