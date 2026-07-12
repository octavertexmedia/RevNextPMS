"""
Multi-product SaaS catalog for RevNext Hospitality.

Billable product hosts (shared Django backend):
  - channel-manager.revnext.in
  - pms.revnext.in
  - pos.revnext.in
  - cms.revnext.in          (RevNextCMS on dedicated VPS 84.247.183.69 — not this process)
  - booking.revnext.in      (direct booking engine — standalone)
  - hotels.revnext.in       (hotel aggregator)
  - networks.revnext.in     (B2B / agent network — standalone)
  - tours.revnext.in

Infrastructure:
  - secrets.revnext.in → OpenBao
  - auth.revnext.in    → OIDC IdP (SSO across all product hosts)

Billing: subscribe per product (monthly/yearly) OR Hospitality Suite package.
"""

PRODUCT_CATALOG = [
    (
        'channel_manager',
        'RevNext Channel Manager',
        'Channel Manager',
        'channel-manager',
        'channel-manager.revnext.in',
        ['/integrations/', '/tenants/dashboard/', '/tenants/properties/'],
        ['/api/core/', '/api/integrations/', '/api/bookings/', '/api/reports/'],
        'integrations',
        'Distribute rates & inventory across OTAs from one control plane.',
        10,
    ),
    (
        'pms',
        'RevNext Cloud PMS',
        'Cloud PMS',
        'pms',
        'pms.revnext.in',
        ['/pms/'],
        ['/api/pms/'],
        'cloud_pms',
        'Front office, folios, housekeeping, and guest operations.',
        20,
    ),
    (
        'pos',
        'RevNext Cloud POS',
        'Cloud POS',
        'pos',
        'pos.revnext.in',
        ['/pos/'],
        ['/api/pos/'],
        'cloud_pos',
        'Restaurant & outlet billing synced to guest folios.',
        30,
    ),
    (
        'cms',
        'RevNext Hotel CMS',
        'Hotel CMS',
        'cms',
        'cms.revnext.in',
        [],  # externally served — no local web paths on ChannelManager
        [],  # externally served — no local API paths on ChannelManager
        '',  # runtime is RevNextCMS, not an in-process Django app
        'Property websites, content, and brand publishing (RevNextCMS).',
        40,
    ),
    (
        'booking',
        'RevNext Booking Engine',
        'Booking Engine',
        'booking',
        'booking.revnext.in',
        ['/booking/'],
        ['/api/booking-engine/'],
        'booking_engine',
        'Commission-free direct bookings, embeddable widget, and guest checkout.',
        45,
    ),
    (
        'aggregator',
        'RevNext Hotels',
        'Hotel Aggregator',
        'hotels',
        'hotels.revnext.in',
        ['/hotels/', '/ota-listing/', '/google-hotel-ads/'],
        ['/api/hotels/', '/api/ota-listing/', '/api/google-hotel-ads/'],
        'hotels',
        'Hotel discovery, listing claims, OTA setup, and metasearch feeds.',
        50,
    ),
    (
        'networks',
        'RevNext B2B Networks',
        'B2B Networks',
        'networks',
        'networks.revnext.in',
        ['/b2b/'],
        ['/api/b2b/'],
        'b2b_network',
        'Corporate & travel-agent portals, contracted rates, and allotments.',
        55,
    ),
    (
        'tours',
        'RevNext Tours',
        'Tours Planner',
        'tours',
        'tours.revnext.in',
        ['/tours/'],
        ['/api/tours/'],
        'tours',
        'Tour packages, itineraries, and activity inventory.',
        60,
    ),
]

PRODUCT_PLANS = {
    'channel_manager': [
        ('cm_starter', 'Channel Manager Starter', 2999, 29990, 'starter',
         {'max_properties': 3, 'max_integrations_per_property': 10, 'max_users': 3, 'max_api_calls_per_month': 10000},
         ['ota_sync', 'inventory', 'rates', 'email_support']),
        ('cm_growth', 'Channel Manager Growth', 4999, 49990, 'growth',
         {'max_properties': 15, 'max_integrations_per_property': 25, 'max_users': 10, 'max_api_calls_per_month': 100000},
         ['ota_sync', 'inventory', 'rates', 'api_access', 'priority_support']),
        ('cm_scale', 'Channel Manager Scale', 9999, 99990, 'scale',
         {'max_properties': 100, 'max_integrations_per_property': 999, 'max_users': 50, 'max_api_calls_per_month': 999999},
         ['ota_sync', 'inventory', 'rates', 'api_access', 'dedicated_am', 'sla']),
    ],
    'pms': [
        ('pms_starter', 'PMS Starter', 3999, 39990, 'starter',
         {'max_properties': 2, 'max_users': 5},
         ['front_desk', 'folios', 'housekeeping']),
        ('pms_pro', 'PMS Pro', 6999, 69990, 'pro',
         {'max_properties': 25, 'max_users': 25},
         ['front_desk', 'folios', 'housekeeping', 'night_audit', 'reports']),
    ],
    'pos': [
        ('pos_starter', 'POS Starter', 2499, 24990, 'starter',
         {'max_outlets': 2, 'max_users': 5},
         ['orders', 'tables', 'folio_posting']),
        ('pos_pro', 'POS Pro', 4499, 44990, 'pro',
         {'max_outlets': 20, 'max_users': 30},
         ['orders', 'tables', 'folio_posting', 'voids', 'shift_reports']),
    ],
    'cms': [
        ('cms_starter', 'CMS Starter', 1499, 14990, 'starter',
         {'max_sites': 1, 'max_properties': 1},
         ['website', 'ssl']),
        ('cms_pro', 'CMS Pro', 2999, 29990, 'pro',
         {'max_sites': 25, 'max_properties': 25},
         ['website', 'ssl', 'custom_domain', 'seo']),
    ],
    'booking': [
        ('booking_starter', 'Booking Engine Starter', 1999, 19990, 'starter',
         {'max_properties': 3, 'max_widgets': 3},
         ['direct_bookings', 'embed_widget', 'email_confirmations']),
        ('booking_pro', 'Booking Engine Pro', 3999, 39990, 'pro',
         {'max_properties': 25, 'max_widgets': 50},
         ['direct_bookings', 'embed_widget', 'email_confirmations',
          'multi_currency', 'google_hotel_ads', 'deposits', 'api']),
    ],
    'aggregator': [
        ('agg_partner', 'Aggregator Partner', 3999, 39990, 'partner',
         {'max_listings': 50},
         ['listing', 'search', 'google_hotel_ads', 'claims']),
        ('agg_network', 'Aggregator Network', 12999, 129990, 'network',
         {'max_listings': 500},
         ['listing', 'search', 'google_hotel_ads', 'claims', 'parity', 'featured', 'feeds', 'api']),
    ],
    'networks': [
        ('networks_starter', 'B2B Networks Starter', 2499, 24990, 'starter',
         {'max_agents': 25, 'max_properties': 5},
         ['agents', 'contract_rates', 'property_access']),
        ('networks_pro', 'B2B Networks Pro', 5499, 54990, 'pro',
         {'max_agents': 250, 'max_properties': 50},
         ['agents', 'contract_rates', 'property_access',
          'agent_portal', 'allotments', 'commission_reports', 'api']),
    ],
    'tours': [
        ('tours_starter', 'Tours Starter', 2999, 29990, 'starter',
         {'max_packages': 25, 'max_users': 3, 'max_departures': 100},
         ['itineraries', 'inventory', 'bookings', 'public_storefront']),
        ('tours_pro', 'Tours Pro', 5999, 59990, 'pro',
         {'max_packages': 250, 'max_users': 15, 'max_departures': 2000},
         ['itineraries', 'inventory', 'bookings', 'agents', 'agent_portal', 'api', 'public_storefront']),
    ],
}

SUITE_PACKAGE = {
    'code': 'revnext_suite',
    'name': 'RevNext Hospitality Suite',
    'description': (
        'Everything in one package: Channel Manager, Cloud PMS, Cloud POS, '
        'Hotel CMS, Booking Engine, Hotels Aggregator, B2B Networks, and Tours.'
    ),
    'monthly_price': 17999,
    'yearly_price': 179990,
    'product_codes': [
        'channel_manager', 'pms', 'pos', 'cms', 'booking',
        'aggregator', 'networks', 'tours',
    ],
    'limits': {
        'max_properties': 25,
        'max_integrations_per_property': 25,
        'max_users': 25,
        'max_api_calls_per_month': 200000,
        'max_outlets': 10,
        'max_sites': 25,
        'max_listings': 100,
        'max_packages': 100,
        'max_agents': 100,
        'max_widgets': 50,
    },
    'features': [
        'all_products',
        'unified_billing',
        'priority_support',
        'cross_product_sso',
        'suite_discount',
        'shared_oidc',
    ],
}

# OIDC relying-party client env keys per product (secrets in OpenBao oidc/)
OIDC_PRODUCT_CLIENTS = {
    'channel_manager': 'OIDC_CLIENT_CHANNEL_MANAGER',
    'pms': 'OIDC_CLIENT_PMS',
    'pos': 'OIDC_CLIENT_POS',
    'cms': 'OIDC_CLIENT_CMS',
    'booking': 'OIDC_CLIENT_BOOKING',
    'aggregator': 'OIDC_CLIENT_HOTELS',
    'networks': 'OIDC_CLIENT_NETWORKS',
    'tours': 'OIDC_CLIENT_TOURS',
}

# Products billed here but served on another deploy (RevNextCMS VPS).
# Seed maps these onto Product.is_externally_served / runtime_url / launch_path.
EXTERNAL_PRODUCT_RUNTIME = {
    'cms': {
        'is_externally_served': True,
        'runtime_url': 'https://app.revnext.in',
        'launch_path': '/dashboard/',
        'oidc_authenticate_path': '/oidc/authenticate/',
        'marketing_url': 'https://cms.revnext.in/',
    },
}

HOST_ALIASES = {
    'channel-manager.revnext.in': 'channel_manager',
    'channel-manager.localhost': 'channel_manager',
    'pms.revnext.in': 'pms',
    'pms.localhost': 'pms',
    'pos.revnext.in': 'pos',
    'pos.localhost': 'pos',
    'cms.revnext.in': 'cms',
    'cms.localhost': 'cms',
    'booking.revnext.in': 'booking',
    'booking.localhost': 'booking',
    'tours.revnext.in': 'tours',
    'tours.localhost': 'tours',
    'hotels.revnext.in': 'aggregator',
    'hotels.localhost': 'aggregator',
    'networks.revnext.in': 'networks',
    'networks.localhost': 'networks',
    'revnext.in': 'aggregator',
    'www.revnext.in': 'aggregator',
    'secrets.revnext.in': None,
    'secrets.localhost': None,
    'auth.revnext.in': None,
    'auth.localhost': None,
    'localhost': None,
    '127.0.0.1': None,
}

# Product-host marketing homepage (unauthenticated `/` on each subdomain).
# solution_slug → core.solutions_data.SOLUTIONS; app_home → post-login destination.
PRODUCT_HOST_LANDING = {
    'channel_manager': {
        'solution_slug': 'channel-manager',
        'app_home': '/tenants/dashboard/',
        'login_label': 'Sign in to Channel Manager',
        'cta_label': 'Start Channel Manager trial',
        'auth_eyebrow': 'Channel Manager',
        'auth_title': 'One control plane for every OTA',
        'auth_lead': 'Sign in to push rates, inventory, and restrictions across 75+ channels.',
        'welcome_title': 'Welcome back',
        'welcome_lead': 'Sign in to manage channels and inventory',
        'register_title': 'Start Channel Manager',
        'register_lead': 'Connect OTAs and lock inventory before the morning rush',
        'auth_stats': [
            {'value': '75+', 'label': 'OTAs'},
            {'value': '500+', 'label': 'Hotels'},
            {'value': '99.9%', 'label': 'Uptime'},
        ],
        'auth_bullets': [
            'Real-time ARI across channels',
            'Multi-property from one login',
            'Overbook protection built in',
        ],
    },
    'pms': {
        'solution_slug': 'cloud-pms',
        'app_home': '/pms/',
        'login_label': 'Front desk sign in',
        'cta_label': 'Start Cloud PMS trial',
        'auth_eyebrow': 'Cloud PMS',
        'auth_title': 'Front desk that never loses the plot',
        'auth_lead': 'Sign in to run arrivals, housekeeping, folios, and linked rooms.',
        'welcome_title': 'Front desk sign in',
        'welcome_lead': 'Open today’s board for your property',
        'register_title': 'Open your cloud desk',
        'register_lead': '14-day trial — front desk, HK, and folios in one login',
        'auth_stats': [
            {'value': '1 desk', 'label': 'every property'},
            {'value': 'Live', 'label': 'room status'},
            {'value': 'GST', 'label': 'ready'},
        ],
        'auth_bullets': [
            'Arrivals, departures, in-house board',
            'Housekeeping synced to the desk',
            'Folios with POS bill-to-room',
        ],
    },
    'pos': {
        'solution_slug': 'cloud-pos',
        'app_home': '/pos/',
        'login_label': 'Sign in to POS',
        'cta_label': 'Start Cloud POS trial',
        'auth_eyebrow': 'Cloud POS',
        'auth_title': 'Billing POS built for busy outlets',
        'auth_lead': 'Dine In, Takeaway, Delivery, QR ordering, inventory, and Swiggy / Zomato — with bill-to-room.',
        'welcome_title': 'Outlet sign in',
        'welcome_lead': 'Open Billing POS, Waiter App, or the aggregator inbox',
        'register_title': 'Start Cloud POS',
        'register_lead': 'Touch billing, QR tables, and online orders in one login',
        'auth_stats': [
            {'value': '5', 'label': 'modules'},
            {'value': 'QR', 'label': 'per table'},
            {'value': '1 folio', 'label': 'room + F&B'},
        ],
        'auth_bullets': [
            'Touch Billing POS with Hold & Pay',
            'Waiter floor board + QR guest ordering',
            'Inventory and Swiggy / Zomato inbox',
        ],
    },
    'booking': {
        'solution_slug': 'booking-engine',
        'app_home': '/booking/',
        'login_label': 'Sign in to Booking Engine',
        'cta_label': 'Start Booking Engine trial',
        'auth_eyebrow': 'Booking Engine',
        'auth_title': 'Commission-free direct bookings',
        'auth_lead': 'Sign in to manage your widget, rates, and direct checkout.',
        'welcome_title': 'Booking Engine sign in',
        'welcome_lead': 'Manage direct booking and your embeddable widget',
        'register_title': 'Start Booking Engine',
        'register_lead': 'Sell direct without OTA commissions',
        'auth_stats': [
            {'value': '0%', 'label': 'OTA fee'},
            {'value': 'Embed', 'label': 'widget'},
            {'value': 'Live', 'label': 'rates'},
        ],
        'auth_bullets': [
            'Guest checkout on your brand',
            'Embeddable booking widget',
            'Inventory shared with Channel Manager',
        ],
    },
    'networks': {
        'solution_slug': 'b2b-network',
        'app_home': '/b2b/',
        'login_label': 'Sign in to B2B Network',
        'cta_label': 'Start B2B Network trial',
        'auth_eyebrow': 'Stay B2B',
        'auth_title': 'Corporate & agent rates without the chaos',
        'auth_lead': 'Sign in to manage partner portals, allotments, and contract rates.',
        'welcome_title': 'B2B Network sign in',
        'welcome_lead': 'Manage agents, corporates, and contracted rates',
        'register_title': 'Start B2B Network',
        'register_lead': 'Secure portals for agents and corporate buyers',
        'auth_stats': [
            {'value': 'Secure', 'label': 'portals'},
            {'value': 'Per-agent', 'label': 'rates'},
            {'value': '1 source', 'label': 'no PDFs'},
        ],
        'auth_bullets': [
            'Partner directory and access roles',
            'Contract rate sheets by agent',
            'Commission tracking for finance',
        ],
    },
    'aggregator': {
        'solution_slug': 'hotel-aggregator',
        'app_home': '/hotels/',
        'login_label': 'Sign in to Hotels',
        'cta_label': 'List your property',
        'guest_cta': {'label': 'Search hotels', 'url': '/hotels/search/'},
        'auth_eyebrow': 'RevNext Hotels',
        'auth_title': 'Discover, claim, and sell hotel inventory',
        'auth_lead': 'Sign in to claim listings and manage your hotel presence.',
        'welcome_title': 'Hotels owner sign in',
        'welcome_lead': 'Claim listings and connect distribution',
        'register_title': 'List your property',
        'register_lead': 'Join the RevNext Hotels network',
        'auth_stats': [
            {'value': 'Search', 'label': 'travelers'},
            {'value': 'Claim', 'label': 'owners'},
            {'value': 'Distribute', 'label': 'when ready'},
        ],
        'auth_bullets': [
            'Public hotel search',
            'Owner listing claims',
            'Bridge into Channel Manager',
        ],
    },
    'tours': {
        'solution_slug': 'tours',
        'app_home': '/tours/',
        'login_label': 'Sign in to Tours',
        'cta_label': 'Start Tours trial',
        'guest_cta': {'label': 'Browse catalog', 'url': '/tours/catalog/'},
        'auth_eyebrow': 'Tours Planner',
        'auth_title': 'Packages, itineraries, and activity inventory',
        'auth_lead': 'Sign in to manage tour products and guest bookings.',
        'welcome_title': 'Tours operator sign in',
        'welcome_lead': 'Manage packages, capacity, and departures',
        'register_title': 'Start Tours Planner',
        'register_lead': 'Publish a guest catalog alongside your hotel stack',
        'auth_stats': [
            {'value': 'Catalog', 'label': 'guest-ready'},
            {'value': 'Capacity', 'label': 'controlled'},
            {'value': '1 login', 'label': 'with suite'},
        ],
        'auth_bullets': [
            'Package and itinerary builder',
            'Public guest catalog',
            'Booking queue for operators',
        ],
    },
}
