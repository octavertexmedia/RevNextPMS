from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import B2BAgent, B2BAllotment, B2BBooking, B2BRatePlan, CorporateAccount
from .forms import B2BAgentForm, B2BRatePlanForm
from core.models import Property


def _tenant_agents(tenant):
    if not tenant:
        return B2BAgent.objects.none()
    return B2BAgent.objects.filter(
        Q(tenant=tenant) | Q(property_access__property__tenant=tenant)
    ).distinct()


@login_required
def b2b_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    agents = _tenant_agents(tenant)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    bookings = B2BBooking.objects.filter(property__tenant=tenant).order_by('-created_at')[:20] if tenant else []

    context = {
        'page_title': 'B2B Networks',
        'agents': agents,
        'properties': properties,
        'bookings': bookings,
        'product_host': 'networks.revnext.in',
    }
    return render(request, 'b2b_network/dashboard.html', context)


@login_required
def agent_portal_home(request):
    """Agent-facing portal on networks.revnext.in/b2b/portal/."""
    agent = getattr(request.user, 'b2b_agent', None)
    if not agent or not agent.is_active or not agent.portal_enabled:
        messages.error(request, 'You do not have B2B portal access.')
        return redirect('b2b_network:dashboard')
    bookings = B2BBooking.objects.filter(agent=agent).order_by('-created_at')[:30]
    allotments = B2BAllotment.objects.filter(agent=agent).select_related(
        'property', 'room_type',
    ).order_by('date')[:60]
    access = CorporateAccount.objects.filter(agent=agent, has_access=True).select_related('property')
    return render(request, 'b2b_network/portal_home.html', {
        'page_title': 'Agent Portal',
        'agent': agent,
        'bookings': bookings,
        'allotments': allotments,
        'properties': [ca.property for ca in access],
        'product_host': 'networks.revnext.in',
    })


@login_required
def b2b_agents(request):
    tenant = getattr(request, 'tenant', None)
    agents = _tenant_agents(tenant)
    
    # Filters
    agent_type = request.GET.get('type')
    is_active = request.GET.get('active')
    property_id = request.GET.get('property')
    if agent_type:
        agents = agents.filter(agent_type=agent_type)
    if is_active is not None:
        agents = agents.filter(is_active=is_active == '1')
    if property_id:
        agents = agents.filter(property_access__property_id=property_id)
    
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    context = {'page_title': 'B2B Agents', 'agents': agents, 'properties': properties}
    return render(request, 'b2b_network/agents_list.html', context)


@login_required
def agent_create(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('b2b_network:agents')
    if request.method == 'POST':
        form = B2BAgentForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'B2B agent created.')
            return redirect('b2b_network:agents')
    else:
        form = B2BAgentForm(tenant=tenant)
    return render(request, 'b2b_network/agent_form.html', {'form': form, 'page_title': 'New B2B Agent'})


@login_required
def agent_edit(request, agent_id):
    tenant = getattr(request, 'tenant', None)
    agent = get_object_or_404(B2BAgent, id=agent_id, property_access__property__tenant=tenant)
    if request.method == 'POST':
        form = B2BAgentForm(request.POST, instance=agent, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agent updated.')
            return redirect('b2b_network:agents')
    else:
        form = B2BAgentForm(instance=agent, tenant=tenant)
    return render(request, 'b2b_network/agent_form.html', {'form': form, 'page_title': 'Edit Agent', 'agent': agent})


@login_required
def agent_detail(request, agent_id):
    tenant = getattr(request, 'tenant', None)
    agent = get_object_or_404(B2BAgent, id=agent_id, property_access__property__tenant=tenant)
    rate_plans = agent.rate_plans.filter(is_active=True).select_related('rate_plan', 'rate_plan__room_type')
    context = {'page_title': agent.company_name, 'agent': agent, 'rate_plans': rate_plans}
    return render(request, 'b2b_network/agent_detail.html', context)


@login_required
def b2b_rate_create(request, agent_id):
    tenant = getattr(request, 'tenant', None)
    agent = get_object_or_404(B2BAgent, id=agent_id, property_access__property__tenant=tenant)
    if request.method == 'POST':
        form = B2BRatePlanForm(request.POST, agent=agent)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.agent = agent
            obj.save()
            messages.success(request, 'B2B rate added.')
            return redirect('b2b_network:agent_detail', agent_id=agent.id)
    else:
        form = B2BRatePlanForm(agent=agent)
    return render(request, 'b2b_network/b2b_rate_form.html', {
        'form': form, 'agent': agent, 'page_title': f'Add B2B Rate - {agent.company_name}'
    })


@login_required
def b2b_rate_edit(request, agent_id, rate_id):
    tenant = getattr(request, 'tenant', None)
    agent = get_object_or_404(B2BAgent, id=agent_id, property_access__property__tenant=tenant)
    b2b_rate = get_object_or_404(B2BRatePlan, id=rate_id, agent=agent)
    if request.method == 'POST':
        form = B2BRatePlanForm(request.POST, instance=b2b_rate, agent=agent)
        if form.is_valid():
            form.save()
            messages.success(request, 'B2B rate updated.')
            return redirect('b2b_network:agent_detail', agent_id=agent.id)
    else:
        form = B2BRatePlanForm(instance=b2b_rate, agent=agent)
    return render(request, 'b2b_network/b2b_rate_form.html', {
        'form': form, 'agent': agent, 'page_title': f'Edit B2B Rate - {agent.company_name}'
    })
