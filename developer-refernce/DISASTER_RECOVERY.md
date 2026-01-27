# Disaster Recovery Procedures
## RevNext Channel Manager

**Last Updated**: January 2026

---

## Overview

This document outlines disaster recovery procedures for the RevNext Channel Manager application, including backup strategies, recovery procedures, and business continuity planning.

---

## 1. Backup Strategy

### 1.1 Database Backups

**Automated Backups**:
- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days
- **Location**: `/backups/` directory on server
- **Format**: PostgreSQL custom format (`.sql` files)

**Manual Backup Command**:
```bash
python manage.py backup_database --output-dir /backups --retention-days 30
```

**Backup Verification**:
- Automated backups are verified after creation
- Backup integrity checks run weekly
- Old backups are automatically cleaned up after retention period

### 1.2 File Backups

**Static Files**:
- Static files are collected and stored in `staticfiles/` directory
- Backed up as part of deployment process

**Media Files**:
- User-uploaded media files stored in `media/` directory
- Should be backed up separately using rsync or cloud storage

**Backup Command**:
```bash
# Backup media files
rsync -avz /path/to/media/ /backups/media/
```

### 1.3 Configuration Backups

**Environment Variables**:
- `.env` file should be backed up securely
- Stored in encrypted format

**Settings Files**:
- `settings.py` and other configuration files
- Version controlled in Git repository

---

## 2. Recovery Procedures

### 2.1 Database Recovery

**From Automated Backup**:
```bash
# Stop application
sudo systemctl stop gunicorn

# Restore database
pg_restore -h localhost -U postgres -d channel_manager -c /backups/channel_manager_YYYYMMDD_HHMMSS.sql

# Start application
sudo systemctl start gunicorn
```

**From Manual Backup**:
1. Identify the backup file to restore
2. Stop the application
3. Drop existing database (if needed)
4. Restore from backup
5. Run migrations if needed: `python manage.py migrate`
6. Restart application

### 2.2 Application Recovery

**Full Application Restore**:
1. Restore database (see above)
2. Restore media files: `rsync -avz /backups/media/ /path/to/media/`
3. Restore environment variables
4. Install dependencies: `pip install -r requirements.txt`
5. Collect static files: `python manage.py collectstatic --noinput`
6. Restart services

### 2.3 Partial Recovery

**Recover Specific Data**:
- Use Django admin to restore specific models
- Use database tools to restore specific tables
- Use `django-import-export` for data import

---

## 3. High Availability

### 3.1 Database Replication

**Primary-Secondary Setup**:
- Primary database for writes
- Secondary database for reads (optional)
- Automatic failover configuration

### 3.2 Application Load Balancing

**Multiple Application Servers**:
- Deploy application on multiple servers
- Use load balancer (Nginx/HAProxy)
- Session storage in Redis (shared)

### 3.3 Celery Workers

**Worker Redundancy**:
- Multiple Celery workers for task processing
- Automatic task retry on failure
- Dead letter queue for failed tasks

---

## 4. Monitoring and Alerts

### 4.1 Health Checks

**Endpoint**: `/health/`

**Checks Performed**:
- Database connectivity
- Cache (Redis) availability
- Disk space usage
- Memory usage
- Celery worker status

**Response Codes**:
- `200`: Healthy
- `200`: Degraded (warnings but operational)
- `503`: Unhealthy (critical issues)

### 4.2 Monitoring Tools

**Recommended Tools**:
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **Application Monitoring**: Sentry (already integrated)
- **Server Monitoring**: New Relic, Datadog
- **Log Aggregation**: ELK Stack, CloudWatch

### 4.3 Alert Configuration

**Critical Alerts**:
- Database connection failures
- Application crashes
- Disk space > 90%
- Memory usage > 90%
- Backup failures

**Warning Alerts**:
- High error rates
- Slow response times
- Disk space > 80%
- Memory usage > 80%

---

## 5. Business Continuity

### 5.1 RTO and RPO

**Recovery Time Objective (RTO)**: 4 hours
- Maximum acceptable downtime: 4 hours
- Target recovery time: 2 hours

**Recovery Point Objective (RPO)**: 24 hours
- Maximum acceptable data loss: 24 hours
- Daily backups ensure < 24 hour data loss

### 5.2 Communication Plan

**Incident Communication**:
1. Notify stakeholders within 15 minutes
2. Provide status updates every 30 minutes
3. Post-mortem within 48 hours

**Stakeholders**:
- Technical team
- Management
- Affected tenants (if applicable)

---

## 6. Testing and Validation

### 6.1 Backup Testing

**Frequency**: Monthly

**Procedure**:
1. Create test environment
2. Restore from latest backup
3. Verify data integrity
4. Test application functionality
5. Document results

### 6.2 Disaster Recovery Drills

**Frequency**: Quarterly

**Scenarios**:
- Database corruption
- Server failure
- Data center outage
- Application bug

---

## 7. Documentation and Training

### 7.1 Runbooks

**Available Runbooks**:
- Database backup and restore
- Application deployment
- Monitoring and alerting
- Incident response

### 7.2 Training

**Team Training**:
- Disaster recovery procedures
- Backup and restore operations
- Monitoring and alerting
- Incident response

---

## 8. Contact Information

**Technical Team**:
- Email: tech@revnext.in
- On-call: [Phone number]

**Escalation**:
- Level 1: Technical team
- Level 2: Management
- Level 3: External support

---

## 9. Appendices

### 9.1 Backup Locations

- **Local Backups**: `/backups/` on server
- **Remote Backups**: [Configure cloud storage]
- **Offsite Backups**: [Configure offsite location]

### 9.2 Recovery Time Estimates

| Scenario | Estimated Recovery Time |
|----------|------------------------|
| Database corruption | 1-2 hours |
| Server failure | 2-4 hours |
| Data center outage | 4-8 hours |
| Application bug | 1-4 hours |

### 9.3 Backup Verification Checklist

- [ ] Backup file exists
- [ ] Backup file size > 0
- [ ] Backup file is recent (< 24 hours)
- [ ] Backup can be restored
- [ ] Restored data is valid
- [ ] Application works with restored data

---

**Note**: This document should be reviewed and updated quarterly or after any significant infrastructure changes.
