# Migration Guide - Adding Subscription System

## Overview

This guide helps you migrate your existing database to include the new subscription system models.

## Step 1: Create Migrations

```bash
# Create migrations for the new models
python manage.py makemigrations tenants

# Review the migrations
python manage.py showmigrations tenants
```

## Step 2: Apply Migrations

```bash
# Apply all migrations
python manage.py migrate
```

## Step 3: Seed Subscription Plans

```bash
# Create subscription plans
python manage.py seed_subscription_plans
```

This will create:
- Free Plan
- Basic Plan
- Professional Plan
- Enterprise Plan

## Step 4: Update Existing Tenants

If you have existing tenants, you may need to:

1. Assign them to a subscription plan
2. Set their subscription status
3. Start a trial period if needed

You can do this through the admin panel or via Django shell:

```python
from tenants.models import Tenant, SubscriptionPlan

# Get a plan
plan = SubscriptionPlan.objects.get(name='enterprise')

# Update tenant
tenant = Tenant.objects.get(name='Your Tenant Name')
tenant.subscription_plan = plan
tenant.subscription_status = 'active'
tenant.upgrade_subscription(plan, 'monthly')
tenant.save()
```

## Step 5: Verify

1. Check admin panel: `/admin/tenants/subscriptionplan/`
2. Check tenant subscriptions: `/admin/tenants/tenant/`
3. Test API: `/api/docs/`

## Troubleshooting

### Migration Conflicts

If you have migration conflicts:

```bash
# Show migration status
python manage.py showmigrations

# Fake migration if needed (use with caution)
python manage.py migrate --fake tenants
```

### Missing Fields

If you see errors about missing fields:
1. Ensure all migrations are applied
2. Check that models match migrations
3. Consider resetting migrations (development only)

## Rollback (If Needed)

If you need to rollback:

```bash
# Rollback to a specific migration
python manage.py migrate tenants <migration_name>

# Or rollback all
python manage.py migrate tenants zero
```

**Note**: Rolling back will delete subscription data. Only do this in development.
