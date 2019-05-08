"""Create fake models for tests and seeding dev DB."""
import factory
from faker import Factory as FakerFactory
from pytest_factoryboy import register
from yaspin import yaspin

from jb.db import Session
from jb.model.user import User as UserBase
from jb.model.asset import Asset

faker: FakerFactory = FakerFactory.create()
faker.seed(420)  # for reproducibility
session = Session()


# create a concrete class of UserBase
class User(UserBase):
    __tablename__ = 'person'


def seed_db():
    with yaspin(text="Seeding database...", color="yellow") as spinner:
        for i in range(1, 2):
            session.add(Asset.create())
            session.add(UserFactory.create())
    session.commit()
    print("Database seeded.")
    spinner.ok("✅ ")


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    dob = factory.LazyAttribute(lambda x: faker.simple_profile()['birthdate'])
    name = factory.LazyAttribute(lambda x: faker.name())


@register
class AssetFactory(factory.Factory):
    class Meta:
        model = Asset

    s3bucket = factory.Sequence(lambda n: f'{faker.word()}{n}')
    s3key = factory.Sequence(lambda n: f'{faker.word()}{n}')
    mime_type = factory.Sequence(lambda n: f'{faker.word()}{n}')
    createdby = factory.SubFactory(UserFactory)