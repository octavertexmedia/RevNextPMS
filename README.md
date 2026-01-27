# Hotel Channel Manager
[![CI/CD Pipeline - Deploy to Contabo VPS](https://github.com/octavertexmedia/ChannelManager/actions/workflows/deploy.yml/badge.svg)](https://github.com/octavertexmedia/ChannelManager/actions/workflows/deploy.yml)
A comprehensive Django-based hotel channel manager for managing Availability, Rates, and Inventory (ARI) synchronization across multiple Online Travel Agencies (OTAs), Global Distribution Systems (GDS), and metasearch platforms.

## Features

- **Multi-Platform Integration**: Support for 25+ platforms including Booking.com, Expedia, Agoda, MakeMyTrip, Goibibo, Yatra, and more
- **Canonical Data Model**: Unified data model that normalizes data from diverse provider formats
- **Real-time Synchronization**: Event-driven architecture with Celery for async task processing
- **Modern Admin Interface**: Beautiful django-unfold admin interface with advanced features
- **India-Specific Features**: GST calculation, invoicing, and compliance support
- **Comprehensive Logging**: Full audit trail with django-simple-history
- **Rate Limiting**: Adaptive rate limiting to respect provider API limits
- **Error Handling**: Robust error handling with retry logic and dead letter queues

## Technology Stack

- **Django 5.0+**: Web framework
- **django-unfold**: Modern admin theme
- **Celery**: Distributed task queue
- **Redis**: Message broker and result backend
- **PostgreSQL**: Database with JSONB support
- **django-guardian**: Object-level permissions
- **django-import-export**: Data import/export
- **django-simple-history**: Audit trail
- **django-constance**: Dynamic configuration
- **django-celery-beat**: Periodic task scheduling

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**
   ```bash
   cd ChannelManager
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Load initial data (optional)**
   ```bash
   python manage.py loaddata initial_data.json
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Start Celery worker** (in a separate terminal)
   ```bash
   celery -A channel_manager worker -l info
   ```

9. **Start Celery beat** (in a separate terminal)
   ```bash
   celery -A channel_manager beat -l info
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=channel_manager
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Google Maps (for location field)
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Environment
ENVIRONMENT=development
```

### Platform Integration Setup

1. **Add Integration Platform**
   - Go to Admin → Integrations → Integration Platforms
   - Click "Add Integration Platform"
   - Fill in platform details (name, API URL, credentials, etc.)

2. **Configure Property Integration**
   - Go to Admin → Integrations → Property Integrations
   - Link a property to a platform
   - Set provider property ID and mappings
   - Configure sync intervals

3. **Enable Sync**
   - Set `is_active = True` on Property Integration
   - Syncs will be scheduled automatically via Celery Beat

## Project Structure

```
ChannelManager/
├── channel_manager/          # Main project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL configuration
│   ├── celery.py            # Celery configuration
│   └── celery_beat_schedule.py  # Periodic tasks
├── core/                    # Core models and admin
│   ├── models.py            # Canonical data models
│   ├── admin.py             # Admin configuration
│   └── utils.py             # Utility functions (GST, etc.)
├── bookings/                # Reservation management
│   ├── models.py            # Reservation, Payment models
│   └── admin.py             # Booking admin
├── integrations/            # Platform integrations
│   ├── models.py            # Integration models
│   ├── admin.py             # Integration admin
│   ├── base_adapter.py      # Base adapter class
│   ├── tasks.py             # Celery tasks
│   └── adapters/            # Platform-specific adapters
│       ├── booking_com_adapter.py
│       ├── expedia_adapter.py
│       └── agoda_adapter.py
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Usage

### Adding a New Platform Integration

1. **Create Adapter Class**
   ```python
   # integrations/adapters/new_platform_adapter.py
   from integrations.base_adapter import BaseAdapter
   
   class NewPlatformAdapter(BaseAdapter):
       def authenticate(self) -> bool:
           # Implement authentication
           pass
       
       def push_availability(self, inventory_data: Dict) -> bool:
           # Implement availability push
           pass
       
       # Implement other required methods
   ```

2. **Register Adapter**
   ```python
   # integrations/tasks.py
   ADAPTER_MAP = {
       'new-platform': NewPlatformAdapter,
       # ...
   }
   ```

3. **Add Platform in Admin**
   - Create IntegrationPlatform entry
   - Configure credentials and settings

### Manual Sync Trigger

You can trigger syncs manually via Django admin or Celery:

```python
from integrations.tasks import sync_availability, sync_rates, sync_reservations

# Sync availability
sync_availability.delay(property_integration_id)

# Sync rates
sync_rates.delay(property_integration_id)

# Sync reservations
sync_reservations.delay(property_integration_id)
```

## GST Calculation

The system includes India-specific GST calculation utilities:

```python
from core.utils import calculate_gst

# Calculate GST for a reservation
gst_breakdown = calculate_gst(
    base_amount=Money(1000, 'INR'),
    property_state='Maharashtra',
    guest_state='Maharashtra'  # Intra-state: CGST + SGST
)

# Returns: {'cgst': Money(60, 'INR'), 'sgst': Money(60, 'INR'), 'igst': Money(0, 'INR')}
```

## API Documentation

API endpoints are available at `/api/`:

- `/api/core/` - Core property and inventory APIs
- `/api/integrations/` - Integration management APIs
- `/api/bookings/` - Reservation APIs

## Testing

```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## Production Deployment

1. **Set DEBUG = False** in settings
2. **Configure proper SECRET_KEY**
3. **Set up proper database (PostgreSQL)**
4. **Configure Redis for Celery**
5. **Set up static file serving** (e.g., WhiteNoise, S3, etc.)
6. **Configure logging** (file rotation, etc.)
7. **Set up monitoring** (Sentry, etc.)
8. **Use process manager** (supervisor, systemd) for Celery workers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.

## Acknowledgments

- [django-unfold](https://github.com/unfoldadmin/django-unfold) for the beautiful admin interface
- All the third-party packages that make this project possible

