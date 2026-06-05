from django.contrib import admin
from .models import FeeComponent, SchoolFeeStructure, FeePayment, LedgerEntry  

# Register your models here.
admin.site.register(FeeComponent)
admin.site.register(SchoolFeeStructure)
admin.site.register(FeePayment)
admin.site.register(LedgerEntry)