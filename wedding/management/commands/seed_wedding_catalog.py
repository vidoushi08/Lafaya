from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Load the wedding catalogue fixture into the database."

    def handle(self, *args, **options):
        call_command("loaddata", "wedding_catalog", verbosity=options["verbosity"])
        self.stdout.write(self.style.SUCCESS("Loaded wedding_catalog."))
