"""
Enterprise hospitality RBAC catalog.

Capabilities are atomic (module.action). System roles map to capability sets.
Custom tenant roles can reuse the same capability pool.
"""

# (codename, module, action, label, description)
CAPABILITIES = [
    # Tenant / org
    ('tenant.view', 'tenant', 'view', 'View tenant', 'View organization profile and subscription status'),
    ('tenant.manage', 'tenant', 'manage', 'Manage tenant', 'Edit organization profile and settings'),
    ('billing.view', 'billing', 'view', 'View billing', 'View invoices and subscription details'),
    ('billing.manage', 'billing', 'manage', 'Manage billing', 'Change plan, payment method, and renewals'),
    ('users.view', 'users', 'view', 'View users', 'List staff and role assignments'),
    ('users.manage', 'users', 'manage', 'Manage users', 'Invite, update, deactivate staff and assign roles'),
    ('roles.view', 'roles', 'view', 'View roles', 'View roles and permission matrix'),
    ('roles.manage', 'roles', 'manage', 'Manage roles', 'Create custom roles and edit assignments'),
    ('audit.view', 'audit', 'view', 'View audit log', 'View security and access audit events'),

    # Properties
    ('properties.view', 'properties', 'view', 'View properties', 'View hotel / property profiles'),
    ('properties.create', 'properties', 'create', 'Create properties', 'Add new properties to the tenant'),
    ('properties.edit', 'properties', 'edit', 'Edit properties', 'Update property details and policies'),
    ('properties.delete', 'properties', 'delete', 'Delete properties', 'Remove properties from the tenant'),

    # Reservations / front office
    ('reservations.view', 'reservations', 'view', 'View reservations', 'View bookings and guest folios'),
    ('reservations.create', 'reservations', 'create', 'Create reservations', 'Create walk-in and phone bookings'),
    ('reservations.edit', 'reservations', 'edit', 'Edit reservations', 'Modify dates, rates, guest details'),
    ('reservations.cancel', 'reservations', 'cancel', 'Cancel reservations', 'Cancel or no-show bookings'),
    ('reservations.checkin', 'reservations', 'checkin', 'Check-in', 'Check guests in'),
    ('reservations.checkout', 'reservations', 'checkout', 'Check-out', 'Check guests out and close folios'),

    # Rates & inventory / revenue
    ('rates.view', 'rates', 'view', 'View rates', 'View rate plans and pricing'),
    ('rates.edit', 'rates', 'edit', 'Edit rates', 'Update rate plans and restrictions'),
    ('inventory.view', 'inventory', 'view', 'View inventory', 'View availability calendars'),
    ('inventory.edit', 'inventory', 'edit', 'Edit inventory', 'Update allotments and stop-sell'),

    # Channel manager
    ('channel.view', 'channel', 'view', 'View channels', 'View OTA integrations and sync status'),
    ('channel.sync', 'channel', 'sync', 'Sync channels', 'Trigger inventory / rate / booking sync'),
    ('channel.configure', 'channel', 'configure', 'Configure channels', 'Connect and map OTA integrations'),

    # Cloud PMS
    ('pms.view', 'pms', 'view', 'View PMS', 'Access PMS dashboards and room status'),
    ('pms.operate', 'pms', 'operate', 'Operate PMS', 'Room moves, folios, guest services'),
    ('pms.configure', 'pms', 'configure', 'Configure PMS', 'PMS settings and workflows'),

    # Housekeeping
    ('housekeeping.view', 'housekeeping', 'view', 'View housekeeping', 'View room cleanliness board'),
    ('housekeeping.update', 'housekeeping', 'update', 'Update housekeeping', 'Mark rooms clean / dirty / inspected'),
    ('housekeeping.manage', 'housekeeping', 'manage', 'Manage housekeeping', 'Assign tasks and manage HK staff'),

    # F&B / POS
    ('pos.view', 'pos', 'view', 'View POS', 'View outlets and orders'),
    ('pos.operate', 'pos', 'operate', 'Operate POS', 'Take orders and settle bills'),
    ('pos.void', 'pos', 'void', 'Void POS', 'Void / comp items and close shifts'),
    ('pos.configure', 'pos', 'configure', 'Configure POS', 'Menus, outlets, and POS settings'),

    # Engineering / maintenance
    ('maintenance.view', 'maintenance', 'view', 'View maintenance', 'View work orders and asset status'),
    ('maintenance.update', 'maintenance', 'update', 'Update maintenance', 'Update work order progress'),
    ('maintenance.manage', 'maintenance', 'manage', 'Manage maintenance', 'Create and assign work orders'),

    # Sales / events / B2B
    ('sales.view', 'sales', 'view', 'View sales', 'View group / corporate / event leads'),
    ('sales.manage', 'sales', 'manage', 'Manage sales', 'Manage accounts, quotes, and contracts'),
    ('b2b.view', 'b2b', 'view', 'View B2B', 'View agent and corporate network'),
    ('b2b.manage', 'b2b', 'manage', 'Manage B2B', 'Manage agents, rates, and access'),
    ('events.view', 'events', 'view', 'View events', 'View banquet and event bookings'),
    ('events.manage', 'events', 'manage', 'Manage events', 'Create and edit event bookings'),

    # Concierge / guest services
    ('concierge.view', 'concierge', 'view', 'View concierge', 'View guest service requests'),
    ('concierge.operate', 'concierge', 'operate', 'Operate concierge', 'Handle guest requests and arrangements'),

    # Finance
    ('finance.view', 'finance', 'view', 'View finance', 'View folios, payments, and night audit'),
    ('finance.manage', 'finance', 'manage', 'Manage finance', 'Post adjustments, refunds, and close day'),
    ('night_audit.run', 'finance', 'night_audit', 'Run night audit', 'Execute night audit / day close'),

    # Reports
    ('reports.view', 'reports', 'view', 'View reports', 'View operational and revenue reports'),
    ('reports.export', 'reports', 'export', 'Export reports', 'Export and download report data'),

    # Digital / marketing surfaces
    ('booking_engine.view', 'booking_engine', 'view', 'View booking engine', 'View booking engine configuration'),
    ('booking_engine.configure', 'booking_engine', 'configure', 'Configure booking engine', 'Edit booking engine settings'),
    ('website.view', 'website', 'view', 'View website', 'View hotel website builder'),
    ('website.edit', 'website', 'edit', 'Edit website', 'Edit website content and publish'),
    ('ota_listing.view', 'ota_listing', 'view', 'View OTA listing', 'View listing content'),
    ('ota_listing.manage', 'ota_listing', 'manage', 'Manage OTA listing', 'Edit listing content and media'),
    ('google_ads.view', 'google_ads', 'view', 'View Google Hotel Ads', 'View Google Hotel Ads campaigns'),
    ('google_ads.manage', 'google_ads', 'manage', 'Manage Google Hotel Ads', 'Configure Google Hotel Ads'),

    # Tours product (tours.revnext.in)
    ('tours.view', 'tours', 'view', 'View tours', 'View tour packages, departures, and bookings'),
    ('tours.manage', 'tours', 'manage', 'Manage tours', 'Create and edit tour packages and itineraries'),
    ('tours.inventory', 'tours', 'inventory', 'Manage tour inventory', 'Manage departure seats and cutoffs'),
    ('tours.bookings', 'tours', 'bookings', 'Manage tour bookings', 'Create and cancel tour bookings'),
    ('tours.agents', 'tours', 'agents', 'Manage tour agents', 'Manage tour agent portal access'),

    # Hotels aggregator (hotels.revnext.in)
    ('aggregator.listings.view', 'aggregator', 'listings_view', 'View aggregator listings', 'View hotels.revnext.in listings'),
    ('aggregator.listings.manage', 'aggregator', 'listings_manage', 'Manage aggregator listings', 'Publish and edit discovery listings'),
    ('aggregator.claims.review', 'aggregator', 'claims_review', 'Review listing claims', 'Approve or reject listing ownership claims'),
]

# Convenience sets
_ALL = [c[0] for c in CAPABILITIES]
_READ_HEAVY = [
    'tenant.view', 'properties.view', 'reservations.view', 'rates.view',
    'inventory.view', 'channel.view', 'pms.view', 'housekeeping.view',
    'pos.view', 'maintenance.view', 'sales.view', 'b2b.view', 'events.view',
    'concierge.view', 'finance.view', 'reports.view', 'booking_engine.view',
    'website.view', 'ota_listing.view', 'google_ads.view', 'tours.view',
    'aggregator.listings.view', 'users.view',
    'roles.view', 'billing.view', 'audit.view',
]


def _except(*deny):
    deny_set = set(deny)
    return [c for c in _ALL if c not in deny_set]


# System hospitality roles: (code, name, department, scope_default, description, capabilities)
# scope_default: tenant | property
SYSTEM_ROLES = [
    (
        'owner',
        'Owner',
        'executive',
        'tenant',
        'Full organization control including billing and user administration.',
        _ALL,
    ),
    (
        'corporate_admin',
        'Corporate Administrator',
        'executive',
        'tenant',
        'Multi-property corporate admin without ownership transfer rights.',
        _except('billing.manage'),
    ),
    (
        'general_manager',
        'General Manager',
        'executive',
        'property',
        'Property P&L owner with full operational control for assigned hotels.',
        _except('billing.manage', 'tenant.manage', 'roles.manage'),
    ),
    (
        'front_office_manager',
        'Front Office Manager',
        'front_office',
        'property',
        'Owns front desk, reservations, and guest arrival operations.',
        [
            'properties.view', 'reservations.view', 'reservations.create', 'reservations.edit',
            'reservations.cancel', 'reservations.checkin', 'reservations.checkout',
            'rates.view', 'inventory.view', 'pms.view', 'pms.operate',
            'housekeeping.view', 'concierge.view', 'concierge.operate',
            'finance.view', 'reports.view', 'users.view',
        ],
    ),
    (
        'front_desk_agent',
        'Front Desk Agent',
        'front_office',
        'property',
        'Check-in/out, walk-ins, and guest services at the desk.',
        [
            'properties.view', 'reservations.view', 'reservations.create', 'reservations.edit',
            'reservations.checkin', 'reservations.checkout', 'rates.view', 'inventory.view',
            'pms.view', 'pms.operate', 'housekeeping.view', 'concierge.view',
        ],
    ),
    (
        'reservations_agent',
        'Reservations Agent',
        'front_office',
        'property',
        'Handles inbound bookings, modifications, and cancellations.',
        [
            'properties.view', 'reservations.view', 'reservations.create', 'reservations.edit',
            'reservations.cancel', 'rates.view', 'inventory.view', 'channel.view',
            'booking_engine.view',
        ],
    ),
    (
        'revenue_manager',
        'Revenue Manager',
        'revenue',
        'property',
        'Owns pricing, inventory controls, and channel distribution strategy.',
        [
            'properties.view', 'reservations.view', 'rates.view', 'rates.edit',
            'inventory.view', 'inventory.edit', 'channel.view', 'channel.sync',
            'channel.configure', 'booking_engine.view', 'booking_engine.configure',
            'reports.view', 'reports.export', 'google_ads.view', 'google_ads.manage',
            'ota_listing.view', 'aggregator.listings.view', 'aggregator.listings.manage',
            'aggregator.claims.review',
        ],
    ),
    (
        'channel_manager_operator',
        'Channel Manager Operator',
        'revenue',
        'property',
        'Day-to-day OTA mapping, sync, and distribution operations.',
        [
            'properties.view', 'rates.view', 'inventory.view', 'inventory.edit',
            'channel.view', 'channel.sync', 'channel.configure', 'reservations.view',
            'ota_listing.view', 'ota_listing.manage', 'aggregator.listings.view',
            'aggregator.listings.manage', 'reports.view',
        ],
    ),
    (
        'housekeeping_manager',
        'Housekeeping Manager',
        'housekeeping',
        'property',
        'Assigns rooms, inspects quality, and manages HK roster.',
        [
            'properties.view', 'reservations.view', 'pms.view',
            'housekeeping.view', 'housekeeping.update', 'housekeeping.manage',
            'maintenance.view', 'reports.view',
        ],
    ),
    (
        'housekeeping_attendant',
        'Housekeeping Attendant',
        'housekeeping',
        'property',
        'Updates room status and completes assigned cleaning tasks.',
        [
            'properties.view', 'housekeeping.view', 'housekeeping.update', 'pms.view',
        ],
    ),
    (
        'night_auditor',
        'Night Auditor',
        'finance',
        'property',
        'Runs night audit, reconciles folios, and overnight front office.',
        [
            'properties.view', 'reservations.view', 'reservations.create', 'reservations.edit',
            'reservations.checkin', 'reservations.checkout', 'pms.view', 'pms.operate',
            'finance.view', 'finance.manage', 'night_audit.run', 'rates.view',
            'inventory.view', 'reports.view', 'reports.export',
        ],
    ),
    (
        'fb_manager',
        'F&B Manager',
        'food_beverage',
        'property',
        'Owns outlets, menus, and F&B performance.',
        [
            'properties.view', 'pos.view', 'pos.operate', 'pos.void', 'pos.configure',
            'events.view', 'events.manage', 'reports.view', 'reports.export',
        ],
    ),
    (
        'pos_cashier',
        'POS Cashier',
        'food_beverage',
        'property',
        'Takes orders and settles guest checks at an outlet.',
        [
            'properties.view', 'pos.view', 'pos.operate', 'reservations.view',
        ],
    ),
    (
        'concierge',
        'Concierge',
        'guest_services',
        'property',
        'Handles guest arrangements, transport, and local experiences.',
        [
            'properties.view', 'reservations.view', 'concierge.view', 'concierge.operate',
            'pms.view',
        ],
    ),
    (
        'engineering_manager',
        'Engineering Manager',
        'engineering',
        'property',
        'Owns preventive maintenance and engineering staff.',
        [
            'properties.view', 'maintenance.view', 'maintenance.update', 'maintenance.manage',
            'housekeeping.view', 'reports.view',
        ],
    ),
    (
        'maintenance_staff',
        'Maintenance Staff',
        'engineering',
        'property',
        'Completes assigned work orders and updates status.',
        [
            'properties.view', 'maintenance.view', 'maintenance.update',
        ],
    ),
    (
        'sales_manager',
        'Sales Manager',
        'sales',
        'property',
        'Corporate, group, and negotiated-rate sales ownership.',
        [
            'properties.view', 'reservations.view', 'reservations.create', 'reservations.edit',
            'rates.view', 'sales.view', 'sales.manage', 'b2b.view', 'b2b.manage',
            'events.view', 'events.manage', 'tours.view', 'tours.manage', 'tours.inventory',
            'tours.bookings', 'tours.agents', 'reports.view', 'reports.export',
        ],
    ),
    (
        'events_coordinator',
        'Events Coordinator',
        'sales',
        'property',
        'Coordinates banquets, meetings, and event logistics.',
        [
            'properties.view', 'events.view', 'events.manage', 'reservations.view',
            'sales.view', 'pos.view',
        ],
    ),
    (
        'accountant',
        'Accountant',
        'finance',
        'property',
        'Financial controls, payments, and reporting.',
        [
            'properties.view', 'reservations.view', 'finance.view', 'finance.manage',
            'billing.view', 'reports.view', 'reports.export', 'audit.view',
        ],
    ),
    (
        'auditor_viewer',
        'Auditor / Viewer',
        'compliance',
        'tenant',
        'Read-only access for auditors, owners’ office, and compliance.',
        _READ_HEAVY,
    ),
    (
        'spa_manager',
        'Spa Manager',
        'wellness',
        'property',
        'Manages spa appointments and wellness outlet operations.',
        [
            'properties.view', 'reservations.view', 'reservations.create', 'reservations.edit',
            'pos.view', 'pos.operate', 'concierge.view', 'reports.view',
        ],
    ),
    (
        'security_officer',
        'Security Officer',
        'security',
        'property',
        'Guest safety visibility with limited operational write access.',
        [
            'properties.view', 'reservations.view', 'pms.view', 'maintenance.view',
            'audit.view',
        ],
    ),
    # Legacy-compatible aliases used by TenantUser.role today
    (
        'manager',
        'Manager (Legacy)',
        'executive',
        'tenant',
        'Legacy manager role — maps to broad multi-property operations.',
        _except('billing.manage', 'roles.manage'),
    ),
    (
        'staff',
        'Staff (Legacy)',
        'front_office',
        'property',
        'Legacy staff role — front desk style defaults.',
        [
            'properties.view', 'reservations.view', 'reservations.create', 'reservations.edit',
            'reservations.checkin', 'reservations.checkout', 'rates.view', 'inventory.view',
            'pms.view', 'pms.operate', 'housekeeping.view',
        ],
    ),
    (
        'viewer',
        'Viewer (Legacy)',
        'compliance',
        'tenant',
        'Legacy read-only viewer.',
        _READ_HEAVY,
    ),
]

LEGACY_ROLE_MAP = {
    'owner': 'owner',
    'manager': 'manager',
    'staff': 'staff',
    'viewer': 'viewer',
}

DEPARTMENT_CHOICES = [
    ('executive', 'Executive'),
    ('front_office', 'Front Office'),
    ('revenue', 'Revenue Management'),
    ('housekeeping', 'Housekeeping'),
    ('food_beverage', 'Food & Beverage'),
    ('guest_services', 'Guest Services'),
    ('engineering', 'Engineering'),
    ('sales', 'Sales & Events'),
    ('finance', 'Finance'),
    ('compliance', 'Compliance & Audit'),
    ('wellness', 'Spa & Wellness'),
    ('security', 'Security'),
    ('other', 'Other'),
]
