"""
Solution marketing page content for /solutions/<slug>/.
Each entry drives hero copy, UI preview type, modules, and outcomes.
"""

SOLUTIONS = {
    'channel-manager': {
        'slug': 'channel-manager',
        'eyebrow': 'Channel Manager',
        'title': 'One control plane for every OTA',
        'lead': (
            'Push rates, inventory, and restrictions to 75+ channels from a single desk — '
            'so overbooks stop and the morning board stays truthful.'
        ),
        'meta': (
            'RevNext Channel Manager — distribute hotel rates and inventory across '
            'OTAs with real-time sync, built for Indian hotels.'
        ),
        'preview_caption': 'Channel desk · sample ARI sync',
        'highlights': [
            {'label': 'Multi-OTA sync', 'text': 'Booking.com, Expedia, MakeMyTrip, Agoda, Airbnb, and 70+ more.'},
            {'label': 'Live ARI', 'text': 'Availability, rates, and inventory update before the first walk-in.'},
            {'label': 'Overbook guard', 'text': 'One source of truth locks rooms across channels.'},
            {'label': 'India-ready', 'text': 'GST-aware workflows and multi-property tenants.'},
        ],
        'modules': [
            {
                'title': 'Channel connections',
                'text': 'Connect OTAs once; map room types and rate plans cleanly.',
            },
            {
                'title': 'Inventory & rates',
                'text': 'Push BAR, restrictions, and allotments without spreadsheet merges.',
            },
            {
                'title': 'Reservation inbox',
                'text': 'New bookings land in one queue with channel attribution.',
            },
            {
                'title': 'Property portfolio',
                'text': 'Run multiple hotels under one tenant with role-based access.',
            },
        ],
        'outcomes': [
            {'stat': '75+', 'label': 'OTA channels'},
            {'stat': 'Real-time', 'label': 'rate & inventory sync'},
            {'stat': 'Zero', 'label': 'double-book chaos'},
        ],
        'steps': [
            {'num': '01', 'title': 'Add properties', 'text': 'Room types, rate plans, and staff roles.'},
            {'num': '02', 'title': 'Connect channels', 'text': 'Map OTAs and enable live ARI.'},
            {'num': '03', 'title': 'Run the desk', 'text': 'Monitor sync health and reservations from one login.'},
        ],
        'features': [
            'Distribute rates & inventory across 75+ OTAs',
            'Real-time availability and restriction sync',
            'Central reservation visibility by channel',
            'Multi-property SaaS with role-based access',
            'GST-ready workflows for Indian hotels',
            'API access on growth plans',
        ],
    },
    'cloud-pms': {
        'slug': 'cloud-pms',
        'eyebrow': 'Cloud PMS',
        'title': 'Front desk that never loses the plot',
        'lead': (
            'Arrivals, departures, housekeeping, folios, and linked rooms — '
            'one cloud desk for every property in your portfolio.'
        ),
        'meta': (
            'RevNext Cloud PMS — front desk, reservations, housekeeping, folios, '
            'and linked rooms for hotels across India.'
        ),
        'preview_caption': 'Live property ops · sample desk',
        'highlights': [
            {'label': 'Arrivals board', 'text': 'See who is due, in-house, and departing before the shift starts.'},
            {'label': 'Folios', 'text': 'Room charges, POS bills, and payments on one guest account.'},
            {'label': 'Housekeeping', 'text': 'Room status updates that sync with the front desk in real time.'},
            {'label': 'Linked rooms', 'text': 'Sell a villa as one unit or as individual rooms without double-booking.'},
        ],
        'modules': [
            {
                'title': 'Front desk & reservations',
                'text': 'Walk-ins, group blocks, and OTA bookings land in the same queue with clear guest status.',
            },
            {
                'title': 'Housekeeping board',
                'text': 'Assign rooms, track dirty / clean / inspected, and push service requests to mobile.',
            },
            {
                'title': 'Guest folios',
                'text': 'Line items, taxes, deposits, and bill-to-room from POS — close cleanly at checkout.',
            },
            {
                'title': 'Multi-property login',
                'text': 'Chains and management companies switch properties without juggling accounts.',
            },
        ],
        'outcomes': [
            {'stat': '1 desk', 'label': 'for every property'},
            {'stat': 'Real-time', 'label': 'room & folio status'},
            {'stat': 'GST-ready', 'label': 'billing for India'},
        ],
        'steps': [
            {'num': '01', 'title': 'Connect properties', 'text': 'Add room types, rates, and staff roles under one tenant.'},
            {'num': '02', 'title': 'Run the morning board', 'text': 'Check-in arrivals, push HK tasks, keep folios open.'},
            {'num': '03', 'title': 'Close the day', 'text': 'Checkout, settle bills, and hand a clean board to night audit.'},
        ],
        'features': [
            'Front desk, reservations, housekeeping, folios, and billing',
            'Linked Room: sell villas/apartments as whole unit or individual rooms',
            'Bill-to-room integration with Cloud POS',
            'Multi-property management under a single login',
            'Arrivals, departures, and in-house views for the shift',
            'GST-aware invoicing built for Indian hotels',
        ],
    },
    'cloud-pos': {
        'slug': 'cloud-pos',
        'eyebrow': 'Cloud POS',
        'title': 'F&B that posts straight to the folio',
        'lead': (
            'Touch-friendly restaurant and outlet billing with tables, KOT flow, '
            'and bill-to-room into Cloud PMS — no end-of-day spreadsheet merge.'
        ),
        'meta': (
            'RevNext Cloud POS — hotel F&B point of sale with bill-to-room, '
            'tables, and folio integration.'
        ),
        'preview_caption': 'Outlet ticket · sample service',
        'highlights': [
            {'label': 'Tables & outlets', 'text': 'Run dine-in, room service, and takeaway from one menu.'},
            {'label': 'Bill to room', 'text': 'Post charges to the open guest folio in one tap.'},
            {'label': 'Kitchen tickets', 'text': 'Print or route KOTs by station without leaving the order.'},
            {'label': 'Settlements', 'text': 'Cash, card, UPI, or room charge — reconciled with PMS.'},
        ],
        'modules': [
            {
                'title': 'Menu & categories',
                'text': 'Build outlet menus with taxes, modifiers, and availability windows.',
            },
            {
                'title': 'Order lifecycle',
                'text': 'Open, fire, modify, and settle tickets with clear status for floor staff.',
            },
            {
                'title': 'Room service',
                'text': 'Link orders to room number and push charges to the guest folio instantly.',
            },
            {
                'title': 'Outlet reports',
                'text': 'Sales by outlet, payment mix, and tax summaries for the night audit.',
            },
        ],
        'outcomes': [
            {'stat': '1 folio', 'label': 'room + F&B together'},
            {'stat': 'Touch UI', 'label': 'built for busy outlets'},
            {'stat': 'Multi-outlet', 'label': 'restaurant, bar, café'},
        ],
        'steps': [
            {'num': '01', 'title': 'Set up outlets', 'text': 'Menus, tables, taxes, and kitchen stations.'},
            {'num': '02', 'title': 'Take the order', 'text': 'Floor staff fire tickets; guests charge to room if in-house.'},
            {'num': '03', 'title': 'Settle cleanly', 'text': 'Close the check — PMS folio already has the line items.'},
        ],
        'features': [
            'Touch-friendly F&B management',
            'Direct integration with PMS folios',
            'Bill-to-room for in-house guests',
            'Tables, dine-in, room service, and takeaway',
            'Kitchen order tickets and outlet reporting',
            'Unified restaurant and room billing',
        ],
    },
    'booking-engine': {
        'slug': 'booking-engine',
        'eyebrow': 'Booking Engine',
        'title': 'Direct bookings without the OTA cut',
        'lead': (
            'A one-page booking flow on your site — live rates, multi-currency, '
            'payment gateways, and Google Hotel Ads — so more stays land commission-free.'
        ),
        'meta': (
            'RevNext Booking Engine — commission-free direct hotel bookings with '
            'multi-currency and payment gateway support.'
        ),
        'preview_caption': 'Direct book widget · sample stay',
        'highlights': [
            {'label': 'Live availability', 'text': 'Rates and rooms pull from the same inventory as your channels.'},
            {'label': 'One-page checkout', 'text': 'Dates → room → guest → pay — fewer drop-offs.'},
            {'label': 'Payments', 'text': 'Razorpay and other gateways for deposits or full prepay.'},
            {'label': 'Meta ready', 'text': 'Feeds Google Hotel Ads with real-time rates.'},
        ],
        'modules': [
            {
                'title': 'Embeddable widget',
                'text': 'Drop the engine on your site or RevNext website — brand stays yours.',
            },
            {
                'title': 'Rate parity control',
                'text': 'Offer member or direct-only rates without breaking channel rules.',
            },
            {
                'title': 'Multi-currency',
                'text': 'Show prices guests understand; settle in your property currency.',
            },
            {
                'title': 'Confirmation flow',
                'text': 'Instant confirmation emails and a reservation that hits the PMS board.',
            },
        ],
        'outcomes': [
            {'stat': '0%', 'label': 'OTA commission on directs'},
            {'stat': '1 page', 'label': 'from search to book'},
            {'stat': 'Live ARI', 'label': 'same as channel sync'},
        ],
        'steps': [
            {'num': '01', 'title': 'Publish rates', 'text': 'Connect room types and rate plans already in RevNext.'},
            {'num': '02', 'title': 'Embed the widget', 'text': 'Add to your website or use the hosted booking page.'},
            {'num': '03', 'title': 'Convert directs', 'text': 'Guests book; inventory locks across OTAs automatically.'},
        ],
        'features': [
            'One-page booking with multi-currency support',
            'Google Hotel Ads integration',
            'Payment gateway integration',
            'Commission-free direct revenue',
            'Live inventory shared with Channel Manager',
            'Instant confirmations into the front desk',
        ],
    },
    'website-builder': {
        'slug': 'website-builder',
        'eyebrow': 'Hotel CMS',
        'title': 'A property site that books, not just browses',
        'lead': (
            'RevNextCMS — multi-tenant Wagtail hotel websites with themes, SEO, custom domains, '
            'and SSO via auth.revnext.in. Subscribe alone or inside the Hospitality Suite.'
        ),
        'meta': (
            'RevNext Hotel CMS (cms.revnext.in) — Wagtail property websites with SEO, SSL, '
            'custom domains, and suite SSO.'
        ),
        'preview_caption': 'Property site · sample homepage',
        'highlights': [
            {'label': 'Wagtail CMS', 'text': 'Full content editing on cms.revnext.in with owner portal at app.revnext.in.'},
            {'label': 'Book now', 'text': 'CTA wired to live availability — not a contact form dead-end.'},
            {'label': 'SEO & SSL', 'text': 'Hosting, certificate, and search-friendly structure included.'},
            {'label': 'Suite SSO', 'text': 'Same IdP as Channel Manager, PMS, and POS — one login across products.'},
        ],
        'modules': [
            {
                'title': 'Owner portal',
                'text': 'Provision properties, themes, and domains from app.revnext.in.',
            },
            {
                'title': 'Themes & branding',
                'text': 'Layout families and brand settings without a developer sprint.',
            },
            {
                'title': 'Custom domains',
                'text': 'Verified custom domains with on-demand TLS on the CMS VPS.',
            },
            {
                'title': 'Suite packaging',
                'text': 'Buy CMS alone (cms_starter / cms_pro) or unlock it with revnext_suite.',
            },
        ],
        'outcomes': [
            {'stat': 'Hours', 'label': 'not weeks to launch'},
            {'stat': 'SSL', 'label': 'included with hosting'},
            {'stat': 'Direct', 'label': 'bookings from day one'},
        ],
        'steps': [
            {'num': '01', 'title': 'Subscribe', 'text': 'Choose cms_starter, cms_pro, or the Hospitality Suite.'},
            {'num': '02', 'title': 'Open Hotel CMS', 'text': 'SSO into app.revnext.in and provision your property.'},
            {'num': '03', 'title': 'Publish', 'text': 'Edit in Wagtail, attach a domain, and go live on *.sites.revnext.in.'},
        ],
        'features': [
            'Wagtail CMS on cms.revnext.in',
            'Owner portal on app.revnext.in',
            'Shared OIDC IdP (auth.revnext.in)',
            'Individual CMS plans or suite package',
            'Custom domains with on-demand TLS',
            'Mobile-responsive property sites',
        ],
    },
    'mobile-apps': {
        'slug': 'mobile-apps',
        'eyebrow': 'Mobile Apps',
        'title': 'The desk in your pocket',
        'lead': (
            'iOS and Android apps for front desk and housekeeping — '
            'check-ins, room status, and guest requests without running back to the PC.'
        ),
        'meta': (
            'RevNext Mobile Apps — iOS and Android for hotel front desk, '
            'housekeeping, and property operations.'
        ),
        'preview_caption': 'RevNext PMS app · sample screens',
        'highlights': [
            {'label': 'Front desk app', 'text': 'Arrivals, check-in/out, and reservation search on the floor.'},
            {'label': 'Housekeeping', 'text': 'Task lists, room status flips, and photo notes from the cart.'},
            {'label': 'Secure login', 'text': 'Same tenant auth as the web desk — roles respected.'},
            {'label': 'Offline-tolerant', 'text': 'Built for patchy Wi‑Fi in service corridors.'},
        ],
        'modules': [
            {
                'title': 'Property switcher',
                'text': 'Managers jump between properties without re-logging.',
            },
            {
                'title': 'Live sync',
                'text': 'Status changes hit the cloud desk so the board stays truthful.',
            },
            {
                'title': 'Push alerts',
                'text': 'New arrivals, VIP notes, and HK escalations when you need them.',
            },
            {
                'title': 'Owner view', 'text': 'Occupancy and key metrics for owners on the go.',
            },
        ],
        'outcomes': [
            {'stat': 'iOS + Android', 'label': 'native apps'},
            {'stat': 'Same API', 'label': 'as the web PMS'},
            {'stat': 'Role-aware', 'label': 'desk vs housekeeping'},
        ],
        'steps': [
            {'num': '01', 'title': 'Install & sign in', 'text': 'Use your RevNext credentials — no separate account.'},
            {'num': '02', 'title': 'Pick the property', 'text': 'See today’s board and assigned HK tasks.'},
            {'num': '03', 'title': 'Work the floor', 'text': 'Update status; the cloud desk updates with you.'},
        ],
        'features': [
            'Front desk and housekeeping apps for iOS & Android',
            'Real-time service requests to housekeeping',
            'Property management and inventory visibility',
            'Remote management for owners and staff',
            'Secure token auth with the RevNext API',
            'Arrivals, departures, and room status on mobile',
        ],
    },
    'b2b-network': {
        'slug': 'b2b-network',
        'eyebrow': 'Stay B2B',
        'title': 'Corporate & agent rates without the chaos',
        'lead': (
            'Give travel agents and corporate buyers a secure portal with negotiated rates, '
            'while you keep control of allotments and commissions.'
        ),
        'meta': (
            'RevNext Stay B2B — corporate and travel agent portals with '
            'special rates and role-based access.'
        ),
        'preview_caption': 'Agent portal · sample rates',
        'highlights': [
            {'label': 'Agent logins', 'text': 'Each partner gets a secure portal — not a shared spreadsheet.'},
            {'label': 'Contract rates', 'text': 'Load negotiated BAR, corporate, and allotment rates per agent.'},
            {'label': 'Role control', 'text': 'Limit who can book, view, or request changes.'},
            {'label': 'B2B channel', 'text': 'A dedicated sales path alongside OTAs and direct.'},
        ],
        'modules': [
            {
                'title': 'Partner directory',
                'text': 'Onboard agencies and corporates with contacts and commercial terms.',
            },
            {
                'title': 'Rate sheets',
                'text': 'Publish date-bound rates by room type without emailing PDFs.',
            },
            {
                'title': 'Booking visibility',
                'text': 'See which partner drove the stay when it hits the desk.',
            },
            {
                'title': 'Commission tracking',
                'text': 'Keep partner economics clear for finance at month-end.',
            },
        ],
        'outcomes': [
            {'stat': 'Secure', 'label': 'partner portals'},
            {'stat': 'Per-agent', 'label': 'rate control'},
            {'stat': 'One source', 'label': 'no rate PDFs'},
        ],
        'steps': [
            {'num': '01', 'title': 'Add partners', 'text': 'Create agent/corporate profiles with access rules.'},
            {'num': '02', 'title': 'Load rates', 'text': 'Attach negotiated rates and allotments.'},
            {'num': '03', 'title': 'Let them book', 'text': 'Partners self-serve; you monitor from RevNext.'},
        ],
        'features': [
            'Corporate and agent login portals',
            'Role-based access control',
            'Special rate management',
            'Dedicated B2B sales channel',
            'Allotment and contract rate support',
            'Clear attribution on the reservation',
        ],
    },
    'ota-listing': {
        'slug': 'ota-listing',
        'eyebrow': 'OTA Listing',
        'title': 'Get listed right — then stay optimized',
        'lead': (
            'Professional setup and optimization of your property on major OTAs — '
            'photos, content, amenities, and channel readiness so you go live faster.'
        ),
        'meta': (
            'RevNext OTA Listing Service — professional hotel listing setup '
            'and optimization across major booking platforms.'
        ),
        'preview_caption': 'Listing checklist · sample project',
        'highlights': [
            {'label': 'Expert setup', 'text': 'Listings built to platform guidelines, not guesswork.'},
            {'label': 'Content polish', 'text': 'Titles, descriptions, and amenities that convert browsers.'},
            {'label': 'Photo guidance', 'text': 'What each OTA expects so you do not get rejected.'},
            {'label': 'Channel ready', 'text': 'Hand-off into Channel Manager when mapping is done.'},
        ],
        'modules': [
            {
                'title': 'Project tracker',
                'text': 'See listing status per OTA — draft, submitted, live.',
            },
            {
                'title': 'Optimization checklist',
                'text': 'Score content completeness before you hit publish.',
            },
            {
                'title': 'Multi-OTA rollout',
                'text': 'Prioritize Booking, MMT, Agoda, Expedia, and your long tail.',
            },
            {
                'title': 'Ongoing tweaks',
                'text': 'Refresh seasons, offers, and photo sets as the property evolves.',
            },
        ],
        'outcomes': [
            {'stat': '100+', 'label': 'platforms supported'},
            {'stat': 'Faster', 'label': 'time-to-live'},
            {'stat': 'Mapped', 'label': 'ready for sync'},
        ],
        'steps': [
            {'num': '01', 'title': 'Share property pack', 'text': 'Photos, amenities, policies, and tax details.'},
            {'num': '02', 'title': 'We build listings', 'text': 'Optimized content per OTA requirements.'},
            {'num': '03', 'title': 'Go live & sync', 'text': 'Connect Channel Manager and open inventory.'},
        ],
        'features': [
            'Professional setup on major OTAs',
            'Listing optimization checklists',
            'Quick onboarding for new properties',
            'Support across 100+ platforms',
            'Content and photo guidance',
            'Handoff into Channel Manager mapping',
        ],
    },
    'google-hotel-ads': {
        'slug': 'google-hotel-ads',
        'eyebrow': 'Google Hotel Ads',
        'title': 'Show up where guests already search',
        'lead': (
            'Push live rates to Google Search, Maps, and Business profiles. '
            'Pay-per-conversion — you pay when a booking confirms, not for empty clicks.'
        ),
        'meta': (
            'RevNext Google Hotel Ads — pay-per-conversion hotel ads with '
            'real-time rates on Google Search and Maps.'
        ),
        'preview_caption': 'Google results · sample hotel ad',
        'highlights': [
            {'label': 'Pay per conversion', 'text': 'Budget follows confirmed bookings, not vanity traffic.'},
            {'label': 'Live rates', 'text': 'ARI feeds keep Google honest with your desk.'},
            {'label': 'Direct path', 'text': 'Clicks land on your Booking Engine, not an OTA.'},
            {'label': 'Maps + Search', 'text': 'Capture intent across Google surfaces guests already use.'},
        ],
        'modules': [
            {
                'title': 'Hotel feed',
                'text': 'Property, room, and rate data submitted through the Google path.',
            },
            {
                'title': 'Bid & budget',
                'text': 'Control spend against the conversions that matter.',
            },
            {
                'title': 'Landing on direct',
                'text': 'Ads resolve to your engine so commission stays with you.',
            },
            {
                'title': 'Performance view',
                'text': 'See impressions, clicks, and booked stays in one place.',
            },
        ],
        'outcomes': [
            {'stat': 'Pay / book', 'label': 'not pay per click'},
            {'stat': 'Live ARI', 'label': 'on Search & Maps'},
            {'stat': 'Direct', 'label': 'bookings preferred'},
        ],
        'steps': [
            {'num': '01', 'title': 'Connect the feed', 'text': 'Link property and Booking Engine in RevNext.'},
            {'num': '02', 'title': 'Go live on Google', 'text': 'Rates appear where travelers compare hotels.'},
            {'num': '03', 'title': 'Pay for bookings', 'text': 'Optimize toward confirmed stays, not clicks alone.'},
        ],
        'features': [
            'Pay-per-conversion (pay for confirmed bookings)',
            'Real-time rates on Google Search & Maps',
            'Direct API link to Booking Engine',
            'Improve look-to-book and ARR',
            'Budget control tied to conversions',
            'Brand-safe landing on your site',
        ],
    },
    'hotel-aggregator': {
        'slug': 'hotel-aggregator',
        'eyebrow': 'RevNext Hotels',
        'title': 'Discover, claim, and sell hotel inventory',
        'lead': (
            'Hotel discovery for travelers, listing claims for owners, and metasearch-ready '
            'feeds — one aggregator surface for the RevNext network.'
        ),
        'meta': (
            'RevNext Hotels — hotel search, listing claims, OTA setup, and metasearch feeds.'
        ),
        'preview_caption': 'Hotel search · sample results',
        'highlights': [
            {'label': 'Guest search', 'text': 'Find stays by destination, dates, and budget.'},
            {'label': 'Listing claims', 'text': 'Owners claim and manage their property presence.'},
            {'label': 'OTA setup', 'text': 'Bridge into channel distribution when you go live.'},
            {'label': 'Metasearch', 'text': 'Feeds ready for Google Hotel Ads and partners.'},
        ],
        'modules': [
            {
                'title': 'Public search',
                'text': 'Traveler-facing hotel discovery without leaving RevNext.',
            },
            {
                'title': 'Owner console',
                'text': 'Claim listings, update content, and connect distribution.',
            },
            {
                'title': 'OTA listing tools',
                'text': 'Prepare properties for channel onboarding.',
            },
            {
                'title': 'Ads & feeds',
                'text': 'Push live rates toward metasearch when Booking Engine is linked.',
            },
        ],
        'outcomes': [
            {'stat': 'Search', 'label': 'for travelers'},
            {'stat': 'Claim', 'label': 'for owners'},
            {'stat': 'Distribute', 'label': 'when ready'},
        ],
        'steps': [
            {'num': '01', 'title': 'Search or claim', 'text': 'Travelers browse; owners claim their hotel.'},
            {'num': '02', 'title': 'Connect products', 'text': 'Link Channel Manager, PMS, or Booking Engine.'},
            {'num': '03', 'title': 'Go live', 'text': 'Sell direct and across OTAs from one tenant.'},
        ],
        'features': [
            'Hotel discovery and public search',
            'Listing claims for property owners',
            'OTA listing and metasearch feed tools',
            'Bridge into Channel Manager and Booking Engine',
            'Multi-property owner login',
            'India-focused hospitality inventory',
        ],
    },
    'tours': {
        'slug': 'tours',
        'eyebrow': 'Tours Planner',
        'title': 'Packages, itineraries, and activity inventory',
        'lead': (
            'Build tour products, publish a guest catalog, and manage bookings — '
            'alongside your hotel stack, not in a separate spreadsheet world.'
        ),
        'meta': (
            'RevNext Tours — tour packages, itineraries, and activity inventory for hospitality operators.'
        ),
        'preview_caption': 'Tour catalog · sample package',
        'highlights': [
            {'label': 'Packages', 'text': 'Day trips, multi-day itineraries, and add-ons.'},
            {'label': 'Guest catalog', 'text': 'Public browse-and-book surface for travelers.'},
            {'label': 'Inventory', 'text': 'Capacity and departure dates without overselling.'},
            {'label': 'Ops desk', 'text': 'Operator login to manage products and bookings.'},
        ],
        'modules': [
            {
                'title': 'Product builder',
                'text': 'Define tours, pricing, and departure windows.',
            },
            {
                'title': 'Public catalog',
                'text': 'Let guests explore packages before they talk to the desk.',
            },
            {
                'title': 'Booking queue',
                'text': 'Confirm, amend, and settle tour reservations.',
            },
            {
                'title': 'Hotel link',
                'text': 'Attach tours to stays when the guest is already in-house.',
            },
        ],
        'outcomes': [
            {'stat': 'Catalog', 'label': 'guest-ready'},
            {'stat': 'Capacity', 'label': 'controlled'},
            {'stat': 'One login', 'label': 'with your suite'},
        ],
        'steps': [
            {'num': '01', 'title': 'Create packages', 'text': 'Itineraries, prices, and seats.'},
            {'num': '02', 'title': 'Publish catalog', 'text': 'Guests browse; operators stay in control.'},
            {'num': '03', 'title': 'Fulfill', 'text': 'Confirm bookings and run the day\'s departures.'},
        ],
        'features': [
            'Tour package and itinerary management',
            'Public guest catalog',
            'Activity inventory and capacity',
            'Operator dashboard and booking queue',
            'Works alongside PMS and Channel Manager',
            'Multi-property tenant support',
        ],
    },
}


def get_solution(slug):
    return SOLUTIONS.get(slug)
