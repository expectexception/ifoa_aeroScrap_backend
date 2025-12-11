# Django Unfold Configuration
from django.templatetags.static import static
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "Ifoa Admin",
    "SITE_HEADER": "IFOA Jobs",
    "SITE_URL": "/",
    "SITE_ICON": None,  # Can add custom icon later
    "SITE_LOGO": None,  # Can add custom logo later
    "SITE_SYMBOL": None,  # Google Material icon  : "flight"
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "COLORS": {
        "primary": {
            "50": "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": False,
                "items": [
                    {
                        "title": "Overview",
                        "icon": "dashboard",
                        "link": lambda request: reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Scraper Management",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Scraper Jobs",
                        "icon": "work",
                        "link": lambda request: reverse_lazy("admin:scraper_manager_scraperjob_changelist"),
                    },
                    {
                        "title": "Scraper Config",
                        "icon": "settings",
                        "link": lambda request: reverse_lazy("admin:scraper_manager_scraperconfig_changelist"),
                    },
                    {
                        "title": "Scraped URLs",
                        "icon": "link",
                        "link": lambda request: reverse_lazy("admin:scraper_manager_scrapedurl_changelist"),
                    },
                ],
            },
            {
                "title": "Jobs & Applications",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Jobs",
                        "icon": "work_outline",
                        "link": lambda request: reverse_lazy("admin:jobs_job_changelist"),
                    },
                    {
                        "title": "Applications",
                        "icon": "description",
                        "link": lambda request: reverse_lazy("admin:jobs_jobapplication_changelist"),
                    },
                    {
                        "title": "Saved Jobs",
                        "icon": "bookmark",
                        "link": lambda request: reverse_lazy("admin:jobs_savedjob_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Resumes",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": lambda request: reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": "User Profiles",
                        "icon": "person",
                        "link": lambda request: reverse_lazy("admin:users_userprofile_changelist"),
                    },
                    {
                        "title": "Resumes",
                        "icon": "description",
                        "link": lambda request: reverse_lazy("admin:resumes_resume_changelist"),
                    },
                ],
            },
            {
                "title": "Scheduling",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Periodic Tasks",
                        "icon": "schedule",
                        "link": lambda request: reverse_lazy("admin:django_celery_beat_periodictask_changelist"),
                    },
                ],
            },
        ],
    },
}


