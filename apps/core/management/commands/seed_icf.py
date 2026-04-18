"""Seed ICF organization, Bird Trade project, and all reference data."""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.core.models import (
    KeywordCategory,
    Language,
    Organization,
    OrganizationMembership,
    Platform,
    ProjectFieldConfig,
    ProjectSettings,
    User,
)
from apps.keywords.models import Keyword


class Command(BaseCommand):
    help = "Seed ICF organization with Bird Trade Central Asia project and reference data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-email",
            default="admin@crane.local",
            help="Email for the admin/coordinator user (default: admin@crane.local)",
        )
        parser.add_argument(
            "--admin-password",
            default="admin",
            help="Password for the admin user (default: admin)",
        )

    def handle(self, *args, **options):
        # 13.1 — Org + Project
        admin = self._ensure_admin(options["admin_email"], options["admin_password"])
        org = self._create_org(admin)
        project = self._create_project(org, admin)

        # 13.2 — Platforms
        self._seed_platforms(project)

        # 13.3 — Languages
        self._seed_languages(project)

        # 13.4 — Keyword categories
        categories = self._seed_categories(project)

        # 13.5 — Project field configs
        self._seed_field_configs(project)

        # 13.6 — Species list (seeded as choices in species_name field config)
        # Already handled in _seed_field_configs

        # 13.7 — Keywords
        self._seed_keywords(project, org, admin, categories)

        # Project settings
        ProjectSettings.objects.get_or_create(
            project=project, defaults={"record_id_prefix": "BTCA"}
        )

        # 13.9 — Test accounts
        self._seed_test_accounts(org, project)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded ICF org '{org.name}' with project '{project.name}'"
        ))

    def _ensure_admin(self, email, password):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"  Created admin user: {email}")
        return user

    def _create_org(self, admin):
        org, created = Organization.objects.get_or_create(
            slug="icf",
            defaults={
                "name": "International Crane Foundation",
                "description": "Collaborative OSINT platform for monitoring illegal wildlife trade in cranes and waterbirds across Central and South Asian Flyway.",
            },
        )
        OrganizationMembership.objects.get_or_create(
            user=admin, organization=org,
            defaults={"role": OrganizationMembership.Role.OWNER},
        )
        if created:
            self.stdout.write("  Created organization: ICF")
        return org

    def _create_project(self, org, admin):
        from apps.core.models import Project, ProjectMembership

        project, created = Project.objects.get_or_create(
            organization=org, slug="bird-trade-central-asia",
            defaults={
                "name": "Bird Trade Central Asia",
                "description": "Monitoring online trade of cranes and waterbirds across Central Asian and South Asian Flyway countries.",
            },
        )
        ProjectMembership.objects.get_or_create(
            user=admin, project=project,
            defaults={"role": ProjectMembership.Role.COORDINATOR},
        )
        if created:
            self.stdout.write("  Created project: Bird Trade Central Asia")
        return project

    def _seed_platforms(self, project):
        platforms = [
            ("Facebook", r"facebook\.com|fb\.com"),
            ("Instagram", r"instagram\.com"),
            ("Telegram", r"t\.me|telegram\.org"),
            ("TikTok", r"tiktok\.com"),
            ("YouTube", r"youtube\.com|youtu\.be"),
            ("X", r"x\.com|twitter\.com"),
            ("VK", r"vk\.com"),
            ("OLX", r"olx\.\w+"),
            ("Lalafo", r"lalafo\.\w+"),
        ]
        for name, pattern in platforms:
            Platform.objects.get_or_create(
                project=project, name=name,
                defaults={"url_pattern": pattern},
            )
        self.stdout.write(f"  Seeded {len(platforms)} platforms")

    def _seed_languages(self, project):
        languages = [
            ("English", "en"), ("Russian", "ru"), ("Hindi", "hi"),
            ("Urdu", "ur"), ("Kyrgyz", "ky"), ("Tajik", "tg"),
            ("Uzbek", "uz"), ("Kazakh", "kk"), ("Pashto", "ps"),
            ("Bengali", "bn"),
        ]
        for name, code in languages:
            Language.objects.get_or_create(
                project=project, name=name,
                defaults={"code": code},
            )
        self.stdout.write(f"  Seeded {len(languages)} languages")

    def _seed_categories(self, project):
        category_names = [
            "sale", "purchase", "hunting", "transport",
            "slang", "market", "species-specific",
        ]
        categories = {}
        for name in category_names:
            cat, _ = KeywordCategory.objects.get_or_create(
                project=project, slug=slugify(name),
                defaults={"name": name.replace("-", " ").title()},
            )
            categories[name] = cat
        self.stdout.write(f"  Seeded {len(categories)} keyword categories")
        return categories

    def _seed_field_configs(self, project):
        species_list = [
            "Siberian Crane (Leucogeranus leucogeranus)",
            "Demoiselle Crane (Anthropoides virgo)",
            "Common Crane (Grus grus)",
            "Sarus Crane (Antigone antigone)",
            "Black-necked Crane (Grus nigricollis)",
            "Bar-headed Goose",
            "Ruddy Shelduck",
            "Marbled Teal",
            "White-headed Duck",
            "Sociable Lapwing",
        ]

        species_groups = [
            "Cranes (Gruidae)",
            "Ducks & Geese (Anatidae)",
            "Waders (Charadriidae)",
            "Other waterbirds",
        ]

        fields = [
            ("species_name", "Species Name", "choice", True, species_list, 1),
            ("scientific_name", "Scientific Name", "text", False, None, 2),
            ("species_group", "Species Group", "choice", False, species_groups, 3),
            ("trade_term", "Trade Term Used", "text", False, None, 4),
            ("trade_type", "Trade Type", "choice", False,
             ["Live sale", "Parts/derivatives", "Hunting offer", "Capture service", "Other"], 5),
            ("purpose", "Purpose", "choice", False,
             ["Pet", "Food", "Traditional medicine", "Sport hunting", "Unknown"], 6),
            ("quantity", "Quantity", "number", False, None, 7),
            ("price", "Price", "text", False, None, 8),
            ("seller_type", "Seller Type", "choice", False,
             ["Individual", "Pet shop", "Market vendor", "Online store", "Unknown"], 9),
            ("media_evidence", "Media Evidence Present", "boolean", False, None, 10),
            ("image_verification", "Image Verification", "choice", False,
             ["Original photo", "Stock photo", "Screenshot", "Cannot determine"], 11),
        ]

        for field_name, label, field_type, required, choices, order in fields:
            ProjectFieldConfig.objects.get_or_create(
                project=project, field_name=field_name,
                defaults={
                    "label": label,
                    "field_type": field_type,
                    "required": required,
                    "choices": choices,
                    "order": order,
                },
            )
        self.stdout.write(f"  Seeded {len(fields)} custom field configs")

    def _seed_keywords(self, project, org, admin, categories):
        keywords = [
            # Sale
            ("crane for sale", "English", "sale"),
            ("buy crane", "English", "sale"),
            ("pet crane", "English", "sale"),
            ("live bird for sale", "English", "sale"),
            ("exotic bird sale", "English", "sale"),
            ("журавль продажа", "Russian", "sale"),
            ("купить журавля", "Russian", "sale"),
            ("продам журавля", "Russian", "sale"),
            # Purchase
            ("looking for crane", "English", "purchase"),
            ("want to buy crane", "English", "purchase"),
            ("ищу журавля", "Russian", "purchase"),
            # Hunting
            ("crane hunting", "English", "hunting"),
            ("bird hunting permit", "English", "hunting"),
            ("охота на журавля", "Russian", "hunting"),
            # Transport
            ("bird shipping", "English", "transport"),
            ("live bird transport", "English", "transport"),
            ("доставка птиц", "Russian", "transport"),
            # Species-specific
            ("Siberian crane", "English", "species-specific"),
            ("demoiselle crane", "English", "species-specific"),
            ("common crane", "English", "species-specific"),
            ("sarus crane", "English", "species-specific"),
            ("стерх", "Russian", "species-specific"),
            ("красавка", "Russian", "species-specific"),
            ("серый журавль", "Russian", "species-specific"),
            # Market
            ("bird market", "English", "market"),
            ("птичий рынок", "Russian", "market"),
            ("animal market", "English", "market"),
        ]

        created = 0
        for term, language, cat_key in keywords:
            cat = categories.get(cat_key)
            _, was_created = Keyword.objects.get_or_create(
                project=project, term=term, language=language,
                defaults={
                    "organization": org,
                    "category": cat,
                    "added_by": admin,
                    "status": Keyword.Status.ACTIVE,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Seeded {created} keywords")

    def _seed_test_accounts(self, org, project):
        from apps.core.models import ProjectMembership

        accounts = [
            ("coordinator@crane.local", "coordinator", OrganizationMembership.Role.MEMBER, ProjectMembership.Role.COORDINATOR),
            ("volunteer1@crane.local", "volunteer1", OrganizationMembership.Role.MEMBER, ProjectMembership.Role.VOLUNTEER),
            ("volunteer2@crane.local", "volunteer2", OrganizationMembership.Role.MEMBER, ProjectMembership.Role.VOLUNTEER),
        ]

        for email, password, org_role, proj_role in accounts:
            user, created = User.objects.get_or_create(
                email=email,
            )
            if created:
                user.set_password(password)
                user.save()

            OrganizationMembership.objects.get_or_create(
                user=user, organization=org,
                defaults={"role": org_role},
            )
            ProjectMembership.objects.get_or_create(
                user=user, project=project,
                defaults={"role": proj_role},
            )

        self.stdout.write(f"  Seeded {len(accounts)} test accounts")
