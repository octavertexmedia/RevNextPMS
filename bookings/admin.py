"""
Django Unfold Admin Configuration for Bookings
"""
from unfold.admin import ModelAdmin
from unfold.decorators import display
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from simple_history.admin import SimpleHistoryAdmin
from djangoql.admin import DjangoQLSearchMixin

from .models import Reservation, Payment, ReservationModification


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['id', 'created_at']
    fields = ['amount', 'payment_method', 'payment_status', 'transaction_id', 'paid_at']


class ReservationModificationInline(admin.TabularInline):
    model = ReservationModification
    extra = 0
    readonly_fields = ['id', 'created_at']
    fields = ['modification_type', 'modified_by', 'created_at']


class ReservationResource(resources.ModelResource):
    class Meta:
        model = Reservation
        fields = (
            'id', 'provider_name', 'provider_reservation_id', 'property__name',
            'check_in', 'check_out', 'guest_name', 'guest_email', 'status',
            'total_amount', 'currency'
        )
        import_id_fields = ['id']


@admin.register(Reservation)
class ReservationAdmin(DjangoQLSearchMixin, ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    resource_class = ReservationResource
    
    list_display = [
        'provider_reservation_id',
        'provider_name',
        'property',
        'guest_name',
        'check_in',
        'check_out',
        'nights',
        'total_amount',
        'status_badge',
        'created_at',
    ]
    
    list_filter = [
        'provider_name',
        'status',
        'property',
        'check_in',
        'check_out',
    ]
    
    search_fields = [
        'provider_reservation_id',
        'provider_confirmation_code',
        'guest_name',
        'guest_email',
        'guest_phone',
        'property__name',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'nights',
        'last_reconciled_at',
        'pricing_summary',
    ]
    
    autocomplete_fields = ['property', 'room_type', 'rate_plan']
    
    date_hierarchy = 'check_in'
    
    fieldsets = (
        ('Reservation Details', {
            'fields': (
                'id',
                'provider_name',
                'provider_reservation_id',
                'provider_confirmation_code',
                'status',
            )
        }),
        ('Property & Room', {
            'fields': ('property', 'room_type', 'rate_plan')
        }),
        ('Dates', {
            'fields': ('check_in', 'check_out', 'nights')
        }),
        ('Guest Information', {
            'fields': (
                'guest_name',
                'guest_email',
                'guest_phone',
                'guest_address',
                'guest_city',
                'guest_state',
                'guest_country',
                'guest_gstin',
            )
        }),
        ('Occupancy', {
            'fields': ('adults', 'children')
        }),
        ('Pricing', {
            'fields': (
                'base_room_rate',
                'total_taxes_fees',
                'total_amount',
                'currency',
                'pricing_summary',
            )
        }),
        ('GST Breakdown (India)', {
            'fields': ('cgst_amount', 'sgst_amount', 'igst_amount'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'provider_specific_data'),
            'classes': ('collapse',)
        }),
        ('Reconciliation', {
            'fields': ('last_reconciled_at', 'reconciliation_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PaymentInline, ReservationModificationInline]
    
    @display(description='Status')
    def status_badge(self, obj):
        colors = {
            'CONFIRMED': 'success',
            'PENDING': 'warning',
            'CANCELLED': 'danger',
            'CHECKED_IN': 'info',
            'CHECKED_OUT': 'secondary',
            'NO_SHOW': 'dark',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @display(description='Pricing Summary')
    def pricing_summary(self, obj):
        html = f'''
        <table class="table table-sm">
            <tr><td><strong>Base Rate:</strong></td><td>{obj.base_room_rate}</td></tr>
            <tr><td><strong>Taxes & Fees:</strong></td><td>{obj.total_taxes_fees}</td></tr>
            <tr><td><strong>Total Amount:</strong></td><td><strong>{obj.total_amount}</strong></td></tr>
        </table>
        '''
        if obj.cgst_amount.amount > 0 or obj.sgst_amount.amount > 0 or obj.igst_amount.amount > 0:
            html += f'''
            <h6>GST Breakdown:</h6>
            <table class="table table-sm">
                <tr><td>CGST:</td><td>{obj.cgst_amount}</td></tr>
                <tr><td>SGST:</td><td>{obj.sgst_amount}</td></tr>
                <tr><td>IGST:</td><td>{obj.igst_amount}</td></tr>
            </table>
            '''
        return format_html(html)


@admin.register(Payment)
class PaymentAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'reservation',
        'amount',
        'payment_method',
        'payment_status_badge',
        'transaction_id',
        'gateway_name',
        'paid_at',
        'created_at',
    ]
    
    list_filter = [
        'payment_method',
        'payment_status',
        'gateway_name',
        'paid_at',
    ]
    
    search_fields = [
        'transaction_id',
        'gateway_transaction_id',
        'reservation__provider_reservation_id',
        'reservation__guest_name',
        'reservation__guest_email',
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    autocomplete_fields = ['reservation']
    
    @display(description='Status')
    def payment_status_badge(self, obj):
        colors = {
            'COMPLETED': 'success',
            'PENDING': 'warning',
            'PROCESSING': 'info',
            'FAILED': 'danger',
            'REFUNDED': 'secondary',
        }
        color = colors.get(obj.payment_status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_payment_status_display()
        )


@admin.register(ReservationModification)
class ReservationModificationAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'reservation',
        'modification_type',
        'modified_by',
        'created_at',
    ]
    
    list_filter = [
        'modification_type',
        'created_at',
    ]
    
    search_fields = [
        'reservation__provider_reservation_id',
        'reservation__guest_name',
        'notes',
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'old_value_display', 'new_value_display']
    
    autocomplete_fields = ['reservation']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'reservation', 'modification_type', 'modified_by', 'notes')
        }),
        ('Changes', {
            'fields': ('old_value_display', 'new_value_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Old Values')
    def old_value_display(self, obj):
        if obj.old_value:
            return format_html('<pre>{}</pre>', str(obj.old_value))
        return '-'
    
    @display(description='New Values')
    def new_value_display(self, obj):
        if obj.new_value:
            return format_html('<pre>{}</pre>', str(obj.new_value))
        return '-'

