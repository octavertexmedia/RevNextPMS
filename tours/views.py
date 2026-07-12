from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Departure, TourBooking, TourPackage


@login_required
def tours_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    packages = TourPackage.objects.filter(tenant=tenant) if tenant else TourPackage.objects.none()
    bookings = TourBooking.objects.filter(tenant=tenant).select_related(
        'package', 'departure',
    ).order_by('-created_at')[:25] if tenant else []
    open_deps = Departure.objects.filter(
        package__tenant=tenant, status__in=('OPEN', 'GUARANTEED'),
        start_date__gte=timezone.now().date(),
    ).count() if tenant else 0

    return render(request, 'tours/dashboard.html', {
        'page_title': 'RevNext Tours',
        'product_name': 'RevNext Tours',
        'host': 'tours.revnext.in',
        'packages': packages,
        'bookings': bookings,
        'package_count': packages.count() if tenant else 0,
        'published_count': packages.filter(is_published=True).count() if tenant else 0,
        'open_departures': open_deps,
        'public_api': '/api/tours/public/packages/',
    })


@login_required
def package_detail(request, package_id):
    tenant = getattr(request, 'tenant', None)
    package = get_object_or_404(TourPackage, id=package_id, tenant=tenant)
    return render(request, 'tours/package_detail.html', {
        'page_title': package.name,
        'package': package,
        'itinerary': package.itinerary_days.all(),
        'departures': package.departures.order_by('start_date'),
        'host': 'tours.revnext.in',
    })


def public_catalog(request):
    """Public browse page on tours.revnext.in (no login)."""
    packages = TourPackage.objects.filter(is_active=True, is_published=True).order_by('name')[:40]
    return render(request, 'tours/public_catalog.html', {
        'page_title': 'Explore Tours',
        'packages': packages,
        'host': 'tours.revnext.in',
    })
