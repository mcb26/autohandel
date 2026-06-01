from django.urls import path

from . import catalog_api, views

app_name = "leads"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/catalog/brands/", catalog_api.catalog_brands, name="catalog_brands"),
    path(
        "api/catalog/<slug:brand_slug>/",
        catalog_api.catalog_brand_detail,
        name="catalog_brand_detail",
    ),
    path("danke/", views.thank_you, name="thank_you"),
    path("datenschutz/", views.privacy, name="privacy"),
    path("impressum/", views.imprint, name="imprint"),
    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("dashboard/vorlagen/", views.dashboard_document_templates, name="dashboard_document_templates"),
    path(
        "dashboard/vorlagen/beispiel/<slug:template_type>/",
        views.dashboard_download_starter_template,
        name="dashboard_starter_template_download",
    ),
    path("dashboard/leads/<int:pk>/", views.dashboard_lead_detail, name="dashboard_lead_detail"),
    path("dashboard/leads/<int:pk>/archive/", views.dashboard_lead_archive, name="dashboard_lead_archive"),
    path("dashboard/leads/<int:pk>/unarchive/", views.dashboard_lead_unarchive, name="dashboard_lead_unarchive"),
    path("dashboard/leads/<int:pk>/delete/", views.dashboard_lead_delete, name="dashboard_lead_delete"),
    path("dashboard/leads/<int:pk>/print/", views.dashboard_lead_print, name="dashboard_lead_print"),
    path(
        "dashboard/leads/<int:pk>/dokument/<slug:template_type>/",
        views.dashboard_lead_generate_document,
        name="dashboard_lead_generate_document",
    ),
    path(
        "dashboard/leads/<int:pk>/package.zip/",
        views.dashboard_lead_package_download,
        name="dashboard_lead_package_download",
    ),
    path("dashboard/login/", views.DashboardLoginView.as_view(), name="dashboard_login"),
    path("dashboard/logout/", views.DashboardLogoutView.as_view(), name="dashboard_logout"),
]
