"""
Solution marketing page content for /solutions/<slug>/.
Each entry drives hero copy, UI preview type, modules, and outcomes.
"""

SOLUTIONS = {
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
        'eyebrow': 'Website Builder',
        'title': 'A property site that books, not just browses',
        'lead': (
            'No-code hotel websites with SEO, SSL, and a direct pipe into the Booking Engine — '
            'so your brand page becomes a revenue channel.'
        ),
        'meta': (
            'RevNext Website Builder — no-code hotel websites with SEO, SSL, '
            'and Booking Engine integration.'
        ),
        'preview_caption': 'Property site · sample homepage',
        'highlights': [
            {'label': 'No-code templates', 'text': 'Launch a polished property site without a developer sprint.'},
            {'label': 'Book now', 'text': 'CTA wired to live availability — not a contact form dead-end.'},
            {'label': 'SEO & SSL', 'text': 'Hosting, certificate, and search-friendly structure included.'},
            {'label': 'Multi-language', 'text': 'Reach domestic and international guests on one site.'},
        ],
        'modules': [
            {
                'title': 'Visual editor',
                'text': 'Update photos, amenities, and offers without touching code.',
            },
            {
                'title': 'Rooms & rates pages',
                'text': 'Pull room copy from your inventory so the site never drifts from the desk.',
            },
            {
                'title': 'Hosting included',
                'text': 'SSL and hosting managed — focus on content and conversion.',
            },
            {
                'title': 'Analytics-ready',
                'text': 'Track visits and booking starts from the same property brand.',
            },
        ],
        'outcomes': [
            {'stat': 'Hours', 'label': 'not weeks to launch'},
            {'stat': 'SSL', 'label': 'included with hosting'},
            {'stat': 'Direct', 'label': 'bookings from day one'},
        ],
        'steps': [
            {'num': '01', 'title': 'Pick a template', 'text': 'Choose a layout that fits boutique, resort, or city hotel.'},
            {'num': '02', 'title': 'Add your story', 'text': 'Photos, amenities, location — publish when ready.'},
            {'num': '03', 'title': 'Turn on booking', 'text': 'Connect the engine and start taking direct stays.'},
        ],
        'features': [
            'No-code templates with SEO optimization',
            'Multi-language support',
            'Free hosting with SSL certificate',
            'Direct link to Booking Engine',
            'Room pages synced with inventory',
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
}


def get_solution(slug):
    return SOLUTIONS.get(slug)
