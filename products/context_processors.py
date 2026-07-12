"""Template context for external product launch URLs (RevNextCMS, etc.)."""
from __future__ import annotations


def product_launch(request):
    """
    Expose CMS launch / pricing URLs for the sidebar.

    Entitled tenants get the RevNextCMS OIDC launch URL; others get pricing.
    """
    cms_launch_url = 'https://app.revnext.in/oidc/authenticate/?next=%2Fdashboard%2F'
    cms_pricing_url = '/pricing/?product=cms&reason=subscribe'
    has_cms = False

    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        if getattr(user, 'is_superuser', False):
            has_cms = True
        else:
            tenant = getattr(request, 'tenant', None) or getattr(user, 'tenant', None)
            if tenant:
                try:
                    from products.services import has_product
                    from products.models import Product

                    has_cms = has_product(tenant, 'cms')
                    product = Product.objects.filter(code='cms', is_active=True).first()
                    if product:
                        cms_launch_url = product.launch_url(with_oidc=True)
                except Exception:
                    pass

    return {
        'cms_entitled': has_cms,
        'cms_launch_url': cms_launch_url if has_cms else cms_pricing_url,
        'cms_pricing_url': cms_pricing_url,
    }
