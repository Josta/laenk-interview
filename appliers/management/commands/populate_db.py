import random
import time

from appliers.models import (
    Applier,
    ScreeningQuestion,
    User,
)
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker


USER_COUNT = 70_000
APPLIER_COUNT = 150_000
QUESTION_COUNT = 1_000_000
BATCH_SIZE = 5_000


fake = Faker()


class Command(BaseCommand):
    help = (
        "Populates the database with a large set of mock data for performance testing."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting data population..."))
        self.stdout.write(
            self.style.WARNING(
                f"Users: {USER_COUNT}, Appliers: {APPLIER_COUNT}, Questions: {QUESTION_COUNT}"
            )
        )

        with transaction.atomic():
            # === Phase 1: Generate Users ===
            start_time = time.time()
            self.stdout.write("Generating Users...")
            users_to_create = []
            user_ids = []  # We need these to link Appliers

            for i in range(USER_COUNT):
                users_to_create.append(
                    User(
                        external_id=fake.uuid4(),
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        email=fake.unique.email(),
                        phone=fake.phone_number(),
                        cover_letter=fake.image_url(),
                        country=fake.country_code(),
                        resume=fake.image_url(),
                    )
                )

                if (i + 1) % BATCH_SIZE == 0:
                    created_users = User.objects.bulk_create(users_to_create)
                    user_ids.extend([user.id for user in created_users])
                    users_to_create = []
                    self.stdout.write(f"  Created {i + 1}/{USER_COUNT} users...")

            # Create any remaining users
            if users_to_create:
                created_users = User.objects.bulk_create(users_to_create)
                user_ids.extend([user.id for user in created_users])

            end_time = time.time()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Phase 1 (Users) complete in {end_time - start_time:.2f}s"
                )
            )

            # === Phase 2: Generate Appliers ===
            start_time = time.time()
            self.stdout.write("Generating Appliers...")
            appliers_to_create = []
            applier_ids = []  # We need these to link ScreeningQuestions

            for i in range(APPLIER_COUNT):
                appliers_to_create.append(
                    Applier(
                        external_id=fake.uuid4(),
                        user_id=random.choice(user_ids),  # Link to a random, real user
                        source={
                            "product": random.choice(
                                ["Indeed", "LinkedIn", "Internal"]
                            ),
                            "isPremium": fake.boolean(),
                        },
                        qualified=random.choice(["YES", "NO", "PENDING"]),
                        latitude=fake.latitude(),
                        longitude=fake.longitude(),
                    )
                )

                if (i + 1) % BATCH_SIZE == 0:
                    created_appliers = Applier.objects.bulk_create(appliers_to_create)
                    applier_ids.extend([applier.id for applier in created_appliers])
                    appliers_to_create = []
                    self.stdout.write(f"  Created {i + 1}/{APPLIER_COUNT} appliers...")

            # Create any remaining appliers
            if appliers_to_create:
                created_appliers = Applier.objects.bulk_create(appliers_to_create)
                applier_ids.extend([applier.id for applier in created_appliers])

            end_time = time.time()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Phase 2 (Appliers) complete in {end_time - start_time:.2f}s"
                )
            )

            # === Phase 3: Generate Screening Questions ===
            start_time = time.time()
            self.stdout.write("Generating Screening Questions...")
            questions_to_create = []

            for i in range(QUESTION_COUNT):
                questions_to_create.append(
                    ScreeningQuestion(
                        application_id=random.choice(
                            applier_ids
                        ),  # Link to a random, real application
                        question=fake.sentence(nb_words=10).replace(".", "?"),
                        type=random.choice(["TEXT", "VIDEO", "FILE"]),
                        answer=fake.sentence(nb_words=15),
                        is_skipped=fake.boolean(chance_of_getting_true=15),
                    )
                )

                if (i + 1) % BATCH_SIZE == 0:
                    ScreeningQuestion.objects.bulk_create(questions_to_create)
                    questions_to_create = []
                    self.stdout.write(
                        f"  Created {i + 1}/{QUESTION_COUNT} questions..."
                    )

            # Create any remaining questions
            if questions_to_create:
                ScreeningQuestion.objects.bulk_create(questions_to_create)

            end_time = time.time()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Phase 3 (Screening Questions) complete in {end_time - start_time:.2f}s"
                )
            )

        self.stdout.write(self.style.SUCCESS("Database population complete!"))
