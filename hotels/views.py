from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import AggregatorListing, ListingClaim, search_listings


@login_required
def hotels_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    listings = AggregatorListing.objects.filter(tenant=tenant) if tenant else AggregatorListing.objects.none()
    claims = ListingClaim.objects.filter(listing__tenant=tenant).order_by('-created_at')[:20] if tenant else []
    return render(request, 'hotels/dashboard.html', {
        'page_title': 'RevNext Hotels',
        'host': 'hotels.revnext.in',
        'listings': listings,
        'published_count': listings.filter(status='PUBLISHED').count() if tenant else 0,
        'claims': claims,
        'public_api': '/api/hotels/public/search/',
    })


def public_search_page(request):
    city = request.GET.get('city', '')
    results = search_listings(city=city) if city else search_listings()
    return render(request, 'hotels/public_search.html', {
        'page_title': 'Find Hotels',
        'host': 'hotels.revnext.in',
        'city': city,
        'results': results[:40],
    })
