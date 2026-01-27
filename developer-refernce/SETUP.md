# Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Database**
   ```bash
   # Create PostgreSQL database
   createdb channel_manager
   
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   
   # Load initial data
   python manage.py setup_initial_data
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start Services**
   ```bash
   # Terminal 1: Django server
   python manage.py runserver
   
   # Terminal 2: Celery worker
   celery -A channel_manager worker -l info
   
   # Terminal 3: Celery beat
   celery -A channel_manager beat -l info
   ```

5. **Access Admin**
   - Open http://localhost:8000/admin/
   - Login with superuser credentials

## Adding Your First Property

1. Go to Admin → Core → Properties
2. Click "Add Property"
3. Fill in property details:
   - Name, address, contact information
   - GST details (for India)
   - Location (requires Google Maps API key)
4. Save

## Adding Room Types

1. Go to Admin → Core → Room Types
2. Click "Add Room Type"
3. Select property
4. Fill in room details:
   - Name, capacity, amenities
5. Save

## Creating Rate Plans

1. Go to Admin → Core → Rate Plans
2. Click "Add Rate Plan"
3. Select property and room type
4. Set base rate and pricing rules
5. Configure policies (cancellation, prepayment)
6. Save

## Setting Up Inventory

1. Go to Admin → Core → Inventories
2. Click "Add Inventory"
3. Select property, room type, and date
4. Set available and total rooms
5. Save

## Configuring Platform Integration

1. **Add Platform**
   - Go to Admin → Integrations → Integration Platforms
   - Click "Add Integration Platform"
   - Fill in:
     - Name (e.g., "booking.com")
     - Display name
     - Platform type
     - API base URL
     - Authentication credentials
     - Rate limits

2. **Link Property to Platform**
   - Go to Admin → Integrations → Property Integrations
   - Click "Add Property Integration"
   - Select property and platform
   - Enter provider property ID
   - Set up room type and rate plan mappings
   - Configure sync intervals
   - Enable syncs (check boxes)
   - Set is_active = True

3. **Verify Sync**
   - Check Admin → Integrations → Sync Logs
   - Look for successful sync entries

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check database credentials in .env
- Ensure database exists

### Celery Not Working
- Verify Redis is running: `redis-cli ping`
- Check CELERY_BROKER_URL in .env
- Check Celery worker logs for errors

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version (3.10+)

### Admin Not Loading
- Run `python manage.py collectstatic`
- Check DEBUG setting in .env
- Check ALLOWED_HOSTS setting

## Next Steps

- Configure additional platforms
- Set up webhook endpoints
- Customize GST rates per property
- Set up monitoring and alerts
- Configure backup strategy

