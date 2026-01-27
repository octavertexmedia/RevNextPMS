"""
Core views for the channel manager application
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone


def health_check(request):
    """Comprehensive health check endpoint"""
    from django.db import connection
    from django.http import JsonResponse
    import psutil
    
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = {
                'status': 'healthy',
                'response_time_ms': 0,
            }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e),
        }
    
    # Redis check (if used)
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        cache_result = cache.get('health_check')
        if cache_result == 'ok':
            health_status['checks']['cache'] = {
                'status': 'healthy',
            }
        else:
            health_status['checks']['cache'] = {
                'status': 'degraded',
            }
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unavailable',
            'error': str(e),
        }
    
    # Disk space check
    try:
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        health_status['checks']['disk'] = {
            'status': 'healthy' if disk_percent < 90 else 'warning',
            'usage_percent': round(disk_percent, 2),
            'free_gb': round(disk.free / (1024**3), 2),
        }
        if disk_percent > 90:
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'error': str(e),
        }
    
    # Memory check
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        health_status['checks']['memory'] = {
            'status': 'healthy' if memory_percent < 90 else 'warning',
            'usage_percent': round(memory_percent, 2),
            'available_gb': round(memory.available / (1024**3), 2),
        }
        if memory_percent > 90:
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'unknown',
            'error': str(e),
        }
    
    # Celery check (if workers are running)
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            health_status['checks']['celery'] = {
                'status': 'healthy',
                'active_workers': len(active_workers),
            }
        else:
            health_status['checks']['celery'] = {
                'status': 'warning',
                'message': 'No active workers found',
            }
    except Exception as e:
        health_status['checks']['celery'] = {
            'status': 'unknown',
            'error': str(e),
        }
    
    # Determine HTTP status code
    status_code = 200
    if health_status['status'] == 'unhealthy':
        status_code = 503
    elif health_status['status'] == 'degraded':
        status_code = 200  # Still return 200 but with warning
    
    return JsonResponse(health_status, status=status_code)


def landing_page(request):
    """Landing page for RevNext Channel Manager"""
    context = {
        'page_title': 'RevNext Channel Manager - Hotel Channel Management SaaS',
        'meta_description': 'Manage your hotel inventory, rates, and bookings across 75+ OTA platforms with RevNext Channel Manager. Real-time synchronization, multi-tenant support, and India-specific GST compliance.',
    }
    return render(request, 'landing/index.html', context)


def about_us(request):
    """About Us page"""
    context = {
        'page_title': 'About Us - RevNext Channel Manager',
        'meta_description': 'Learn about RevNext Channel Manager and our mission to simplify hotel channel management for Indian hotels.',
    }
    return render(request, 'pages/about.html', context)


def blog(request):
    """Blog listing page"""
    context = {
        'page_title': 'Blog - RevNext Channel Manager',
        'meta_description': 'Read the latest articles, tips, and insights about hotel channel management, revenue optimization, and OTA integration.',
    }
    return render(request, 'pages/blog.html', context)


def blog_detail(request, slug):
    """Blog detail page"""
    # Blog posts data
    blog_posts = {
        'getting-started-with-channel-management': {
            'title': 'Getting Started with Channel Management',
            'date': 'January 15, 2026',
            'author': 'RevNext Team',
            'category': 'Getting Started',
            'read_time': '5 min read',
            'image_gradient': 'from-indigo-400 to-purple-500',
            'content': '''
                <p class="text-lg text-gray-700 mb-6">Channel management is the cornerstone of modern hotel operations. In today's digital landscape, hotels need to maintain a consistent presence across multiple online travel agencies (OTAs) to maximize bookings and revenue.</p>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">What is Channel Management?</h2>
                <p class="text-gray-700 mb-4">Channel management refers to the process of distributing your hotel's inventory, rates, and availability across multiple booking channels simultaneously. This includes major OTAs like Booking.com, Expedia, Agoda, and many others.</p>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Key Benefits</h2>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Increased visibility across 75+ booking platforms</li>
                    <li>Real-time synchronization of rates and availability</li>
                    <li>Reduced risk of overbookings</li>
                    <li>Centralized management from a single dashboard</li>
                    <li>Automated inventory updates</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Getting Started</h2>
                <p class="text-gray-700 mb-4">To get started with channel management, you'll need to:</p>
                <ol class="list-decimal list-inside space-y-2 text-gray-700 mb-6">
                    <li>Choose a reliable channel manager platform</li>
                    <li>Set up your property information and room types</li>
                    <li>Configure your rates and availability</li>
                    <li>Connect your preferred OTA channels</li>
                    <li>Enable real-time synchronization</li>
                </ol>
                
                <p class="text-gray-700 mb-6">With RevNext Channel Manager, you can complete this setup in minutes and start managing your hotel's online presence effectively.</p>
            '''
        },
        'gst-compliance-for-indian-hotels': {
            'title': 'GST Compliance for Indian Hotels',
            'date': 'January 10, 2026',
            'author': 'RevNext Team',
            'category': 'Compliance',
            'read_time': '8 min read',
            'image_gradient': 'from-green-400 to-blue-500',
            'content': '''
                <p class="text-lg text-gray-700 mb-6">GST (Goods and Services Tax) compliance is crucial for Indian hotels. Understanding how to calculate and apply GST correctly can save you from legal complications and ensure smooth operations.</p>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Understanding GST for Hotels</h2>
                <p class="text-gray-700 mb-4">Hotels in India are subject to GST based on their room tariff. The GST rates vary depending on the room rate:</p>
                
                <div class="bg-gray-50 rounded-lg p-6 mb-6">
                    <ul class="space-y-3 text-gray-700">
                        <li><strong>Room rate up to ₹1,000:</strong> 12% GST</li>
                        <li><strong>Room rate ₹1,001 to ₹7,500:</strong> 18% GST</li>
                        <li><strong>Room rate above ₹7,500:</strong> 28% GST</li>
                    </ul>
                </div>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">CGST, SGST, and IGST</h2>
                <p class="text-gray-700 mb-4">GST is divided into:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li><strong>CGST (Central GST):</strong> Collected by the central government</li>
                    <li><strong>SGST (State GST):</strong> Collected by the state government</li>
                    <li><strong>IGST (Integrated GST):</strong> Applied for inter-state transactions</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Automated GST Calculation</h2>
                <p class="text-gray-700 mb-6">RevNext Channel Manager automatically calculates CGST, SGST, and IGST based on your hotel's location and the guest's location, ensuring full compliance with Indian tax regulations.</p>
            '''
        },
        'optimizing-revenue-with-dynamic-pricing': {
            'title': 'Optimizing Revenue with Dynamic Pricing',
            'date': 'January 5, 2026',
            'author': 'RevNext Team',
            'category': 'Revenue Management',
            'read_time': '6 min read',
            'image_gradient': 'from-yellow-400 to-orange-500',
            'content': '''
                <p class="text-lg text-gray-700 mb-6">Dynamic pricing is a revenue optimization strategy that adjusts room rates based on demand, seasonality, and market conditions. When implemented correctly, it can significantly increase your hotel's revenue.</p>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">What is Dynamic Pricing?</h2>
                <p class="text-gray-700 mb-4">Dynamic pricing, also known as revenue management, involves adjusting your room rates in real-time based on various factors such as:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Current demand and occupancy levels</li>
                    <li>Seasonal trends and local events</li>
                    <li>Competitor pricing</li>
                    <li>Booking lead time</li>
                    <li>Day of the week</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Benefits of Dynamic Pricing</h2>
                <p class="text-gray-700 mb-4">Implementing dynamic pricing can help you:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Maximize revenue during high-demand periods</li>
                    <li>Fill rooms during low-demand periods</li>
                    <li>Stay competitive in the market</li>
                    <li>Optimize occupancy rates</li>
                    <li>Increase overall profitability</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Best Practices</h2>
                <p class="text-gray-700 mb-6">To effectively implement dynamic pricing, monitor your performance metrics regularly, set minimum and maximum rate limits, and use data-driven insights to make pricing decisions.</p>
            '''
        },
        'ota-integration-best-practices': {
            'title': 'OTA Integration Best Practices',
            'date': 'December 28, 2025',
            'author': 'RevNext Team',
            'category': 'Integration',
            'read_time': '7 min read',
            'image_gradient': 'from-pink-400 to-red-500',
            'content': '''
                <p class="text-lg text-gray-700 mb-6">Integrating with OTA platforms is essential for modern hotels. Following best practices ensures smooth operations, prevents errors, and maximizes your bookings.</p>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Choosing the Right OTAs</h2>
                <p class="text-gray-700 mb-4">Not all OTAs are created equal. Focus on platforms that:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Have strong presence in your target market</li>
                    <li>Offer competitive commission rates</li>
                    <li>Provide reliable technical support</li>
                    <li>Have good user reviews and ratings</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">API Integration Essentials</h2>
                <p class="text-gray-700 mb-4">When integrating with OTA APIs, ensure:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Proper authentication and security</li>
                    <li>Real-time synchronization of rates and availability</li>
                    <li>Error handling and retry mechanisms</li>
                    <li>Rate limiting compliance</li>
                    <li>Data validation and consistency</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Common Pitfalls to Avoid</h2>
                <p class="text-gray-700 mb-6">Avoid rate parity violations, delayed updates, incorrect inventory counts, and poor data quality. These can lead to overbookings, customer dissatisfaction, and potential penalties from OTAs.</p>
            '''
        },
        'preventing-overbookings': {
            'title': 'Preventing Overbookings',
            'date': 'December 20, 2025',
            'author': 'RevNext Team',
            'category': 'Operations',
            'read_time': '5 min read',
            'image_gradient': 'from-teal-400 to-cyan-500',
            'content': '''
                <p class="text-lg text-gray-700 mb-6">Overbookings can damage your hotel's reputation and lead to costly compensation. Real-time synchronization is key to preventing this common issue.</p>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">What Causes Overbookings?</h2>
                <p class="text-gray-700 mb-4">Overbookings typically occur due to:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Delayed inventory updates across channels</li>
                    <li>Manual data entry errors</li>
                    <li>System synchronization failures</li>
                    <li>Multiple booking sources updating simultaneously</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Real-Time Synchronization</h2>
                <p class="text-gray-700 mb-4">With real-time synchronization, every booking and cancellation is immediately reflected across all channels. This ensures:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Accurate inventory counts at all times</li>
                    <li>Instant updates when bookings are made</li>
                    <li>Automatic blocking of rooms when sold</li>
                    <li>Consistent data across all platforms</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Best Practices</h2>
                <p class="text-gray-700 mb-6">Maintain a buffer inventory, set up automated alerts, monitor sync logs regularly, and use a reliable channel manager to minimize the risk of overbookings.</p>
            '''
        },
        'multi-property-management': {
            'title': 'Multi-Property Management',
            'date': 'December 15, 2025',
            'author': 'RevNext Team',
            'category': 'Management',
            'read_time': '6 min read',
            'image_gradient': 'from-purple-400 to-indigo-500',
            'content': '''
                <p class="text-lg text-gray-700 mb-6">Managing multiple hotel properties can be challenging. A multi-tenant channel manager simplifies this by allowing you to manage all properties from a single dashboard.</p>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Benefits of Multi-Property Management</h2>
                <p class="text-gray-700 mb-4">Managing multiple properties through a single platform offers:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Centralized control and oversight</li>
                    <li>Consistent branding and pricing strategies</li>
                    <li>Unified reporting and analytics</li>
                    <li>Reduced operational complexity</li>
                    <li>Cost savings through bulk management</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Multi-Tenant Architecture</h2>
                <p class="text-gray-700 mb-4">RevNext Channel Manager uses a multi-tenant architecture that ensures:</p>
                <ul class="list-disc list-inside space-y-2 text-gray-700 mb-6">
                    <li>Complete data isolation between properties</li>
                    <li>Individual user access controls</li>
                    <li>Property-specific configurations</li>
                    <li>Scalable infrastructure</li>
                </ul>
                
                <h2 class="text-2xl font-bold text-gray-900 mt-8 mb-4">Getting Started</h2>
                <p class="text-gray-700 mb-6">To manage multiple properties, simply add each property to your account, configure their individual settings, and start managing them all from your unified dashboard.</p>
            '''
        }
    }
    
    # Get blog post by slug
    post = blog_posts.get(slug)
    
    if not post:
        from django.http import Http404
        raise Http404("Blog post not found")
    
    context = {
        'page_title': f"{post['title']} - RevNext Channel Manager",
        'meta_description': f"Read about {post['title']} on RevNext Channel Manager blog.",
        'post': post,
        'slug': slug,
    }
    return render(request, 'pages/blog_detail.html', context)


def careers(request):
    """Careers page"""
    context = {
        'page_title': 'Careers - RevNext Channel Manager',
        'meta_description': 'Join the RevNext team and help transform hotel channel management in India.',
    }
    return render(request, 'pages/careers.html', context)


def contact(request):
    """Contact page"""
    context = {
        'page_title': 'Contact Us - RevNext Channel Manager',
        'meta_description': 'Get in touch with RevNext Channel Manager. We\'re here to help you with your hotel channel management needs.',
    }
    return render(request, 'pages/contact.html', context)


def documentation(request):
    """Documentation page"""
    context = {
        'page_title': 'Documentation - RevNext Channel Manager',
        'meta_description': 'Complete documentation to get started with RevNext Channel Manager. Learn how to integrate, manage properties, and sync with OTA platforms.',
    }
    return render(request, 'pages/documentation.html', context)


def guide_getting_started(request):
    """Getting Started guide"""
    context = {
        'page_title': 'Getting Started Guide - RevNext Channel Manager',
        'meta_description': 'Learn the basics and set up your first property in RevNext Channel Manager.',
    }
    return render(request, 'pages/guide_getting_started.html', context)


def guide_property_management(request):
    """Property Management guide"""
    context = {
        'page_title': 'Property Management Guide - RevNext Channel Manager',
        'meta_description': 'Complete guide to managing properties, rooms, and rate plans in RevNext Channel Manager.',
    }
    return render(request, 'pages/guide_property_management.html', context)


def guide_ota_integration(request):
    """OTA Integration guide"""
    context = {
        'page_title': 'OTA Integration Guide - RevNext Channel Manager',
        'meta_description': 'Connect with Booking.com, Expedia, Agoda, and 75+ other OTA platforms.',
    }
    return render(request, 'pages/guide_ota_integration.html', context)


def guide_inventory_management(request):
    """Inventory Management guide"""
    context = {
        'page_title': 'Inventory Management Guide - RevNext Channel Manager',
        'meta_description': 'Manage room availability, blocks, and restrictions across all channels.',
    }
    return render(request, 'pages/guide_inventory_management.html', context)


def guide_rate_management(request):
    """Rate Management guide"""
    context = {
        'page_title': 'Rate Management Guide - RevNext Channel Manager',
        'meta_description': 'Set up dynamic pricing and automated rate rules to maximize revenue.',
    }
    return render(request, 'pages/guide_rate_management.html', context)


def guide_gst_invoicing(request):
    """GST & Invoicing guide"""
    context = {
        'page_title': 'GST & Invoicing Guide - RevNext Channel Manager',
        'meta_description': 'GST compliance and automated invoice generation for Indian hotels.',
    }
    return render(request, 'pages/guide_gst_invoicing.html', context)


def api_reference(request):
    """API Reference page with Swagger and Redoc"""
    context = {
        'page_title': 'API Reference - RevNext Channel Manager',
        'meta_description': 'Complete API reference documentation for RevNext Channel Manager. Integrate with our REST API using Swagger or Redoc.',
    }
    return render(request, 'pages/api_reference.html', context)


def help_center(request):
    """Help Center / Support page"""
    context = {
        'page_title': 'Help Center - RevNext Channel Manager',
        'meta_description': 'Get help and support for RevNext Channel Manager. Find answers to common questions and contact our support team.',
    }
    return render(request, 'pages/help_center.html', context)


def privacy_policy(request):
    """Privacy Policy page"""
    context = {
        'page_title': 'Privacy Policy - RevNext Channel Manager',
        'meta_description': 'Privacy Policy for RevNext Channel Manager. Learn how we collect, use, and protect your data.',
    }
    return render(request, 'pages/privacy_policy.html', context)


def terms_of_service(request):
    """Terms of Service page"""
    context = {
        'page_title': 'Terms of Service - RevNext Channel Manager',
        'meta_description': 'Terms of Service for RevNext Channel Manager. Read our terms and conditions for using our platform.',
    }
    return render(request, 'pages/terms_of_service.html', context)


def integrations_page(request):
    """Dedicated integrations page showing all 75+ booking platforms"""
    context = {
        'page_title': 'All Integrations - 75+ Booking Platforms | RevNext Channel Manager',
        'meta_description': 'Browse all 75+ booking platform integrations available in RevNext Channel Manager. Connect with OTAs, GDS systems, metasearch engines, bedbanks, and more.',
    }
    return render(request, 'pages/integrations.html', context)
