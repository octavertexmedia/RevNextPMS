"""
B2B Network Forms
"""
from django import forms
from .models import B2BAgent, B2BRatePlan, CorporateAccount


class B2BAgentForm(forms.ModelForm):
    """B2B Agent create/edit"""
    properties = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Properties this agent can access'
    )
    
    class Meta:
        model = B2BAgent
        fields = ['company_name', 'agent_type', 'contact_email', 'contact_phone', 'commission_percent', 'credit_limit', 'is_active', 'notes']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            'agent_type': forms.Select(attrs={'class': 'form-select'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-input'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'commission_percent': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        self._tenant = tenant
        super().__init__(*args, **kwargs)
        if tenant:
            from core.models import Property
            self.fields['properties'].queryset = Property.objects.filter(tenant=tenant, is_active=True)
        if self.instance and self.instance.pk:
            self.fields['properties'].initial = [
                ca.property_id for ca in CorporateAccount.objects.filter(agent=self.instance, has_access=True)
            ]

    def save(self, commit=True):
        agent = super().save(commit=False)
        tenant = getattr(self, '_tenant', None)
        if tenant and not agent.tenant_id:
            agent.tenant = tenant
        if commit:
            agent.save()
            if 'properties' in self.cleaned_data:
                CorporateAccount.objects.filter(agent=agent).delete()
                for prop in self.cleaned_data['properties']:
                    CorporateAccount.objects.create(property=prop, agent=agent, has_access=True)
        return agent


class B2BRatePlanForm(forms.ModelForm):
    """B2B Rate Plan create/edit"""
    class Meta:
        model = B2BRatePlan
        fields = ['rate_plan', 'discount_percent', 'net_rate', 'is_active', 'valid_from', 'valid_to']
        widgets = {
            'rate_plan': forms.Select(attrs={'class': 'form-select'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'net_rate': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'valid_from': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'valid_to': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        agent = kwargs.pop('agent', None)
        super().__init__(*args, **kwargs)
        if agent:
            from core.models import RatePlan
            prop_ids = [ca.property_id for ca in CorporateAccount.objects.filter(agent=agent, has_access=True)]
            self.fields['rate_plan'].queryset = RatePlan.objects.filter(property_id__in=prop_ids, is_active=True)
