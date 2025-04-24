from django.contrib import admin
from .models import Student
from django.utils.html import format_html
from django.templatetags.static import static

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    def image_tag(self, obj):
        if obj.profile_pic:
            return format_html('<img src="{}" style="max-width:100px; max-height:100px"/>', obj.profile_pic.url)
        return format_html('<img src="{}" style="max-width:100px; max-height:100px"/>', static('image/student.png'))
    
    image_tag.short_description = 'Profile Picture'
    list_display = ['get_name', 'mobile', 'image_tag']
    search_fields = ['user__first_name', 'user__last_name', 'mobile']
