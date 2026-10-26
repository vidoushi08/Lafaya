from django.contrib.admin import AdminSite


class SuperAdminSite(AdminSite):
    site_header = "Lafaya superadmin"
    site_title = "Lafaya administration"
    index_title = "Account management"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser


superadmin_site = SuperAdminSite(name="admin")
