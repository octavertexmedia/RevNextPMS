"""
Website Builder Forms
"""
from django import forms
from .models import PropertyWebsite, SiteTemplate


class PropertyWebsiteForm(forms.ModelForm):
    """Property website - template, SEO, domain"""
    class Meta:
        model = PropertyWebsite
        fields = [
            'template', 'meta_title', 'meta_description', 'meta_keywords',
            'custom_domain', 'subdomain', 'ssl_enabled', 'is_published'
        ]
        widgets = {
            'template': forms.Select(attrs={'class': 'form-select'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Hotel Name - Best Stay in City', 'maxlength': 70}),
            'meta_description': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 2, 'placeholder': 'Short description for search engines (max 160 chars)', 'maxlength': 160}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'hotel, city, stay, accommodation'}),
            'custom_domain': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'www.myhotel.com'}),
            'subdomain': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'myhotel'}),
            'ssl_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox h-4 w-4 text-indigo-600'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox h-4 w-4 text-indigo-600'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['template'].queryset = SiteTemplate.objects.filter(is_active=True)
