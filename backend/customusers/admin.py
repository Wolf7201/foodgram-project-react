from django.contrib import admin
from .models import CustomUser, Follow
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('id',)
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    filter_horizontal = ('groups', 'user_permissions',)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'first_name', 'last_name')
        }),
    )


class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__email', 'author__email')
    ordering = ('id',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Follow, FollowAdmin)

if Group in admin.site._registry:
    admin.site.unregister(Group)

# Не отключается!!!
if TokenProxy in admin.site._registry:
    admin.site.unregister(TokenProxy)
