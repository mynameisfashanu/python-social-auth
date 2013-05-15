import json

from sure import expect

from tests.actions.actions_tests import BaseActionTest
from tests.models import TestUserSocialAuth, TestStorage, User
from tests.strategy import TestStrategy


class IntegrityError(Exception):
    pass


class UnknownError(Exception):
    pass


class IntegrityErrorUserSocialAuth(TestUserSocialAuth):
    @classmethod
    def create_social_auth(cls, user, uid, provider):
        raise IntegrityError()

    @classmethod
    def get_social_auth(cls, provider, uid):
        if not hasattr(cls, '_called_times'):
            cls._called_times = 1
        if cls._called_times == 2:
            user = list(User.cache.values())[0]
            return IntegrityErrorUserSocialAuth(user, provider, uid)
        else:
            cls._called_times += 1
            return super(IntegrityErrorUserSocialAuth, cls).get_social_auth(
                provider, uid
            )


class IntegrityErrorStorage(TestStorage):
    user = IntegrityErrorUserSocialAuth

    @classmethod
    def is_integrity_error(cls, exception):
        """Check if given exception flags an integrity error in the DB"""
        return isinstance(exception, IntegrityError)


class UnknownErrorUserSocialAuth(TestUserSocialAuth):
    @classmethod
    def create_social_auth(cls, user, uid, provider):
        raise UnknownError()


class UnknownErrorStorage(IntegrityErrorStorage):
    user = UnknownErrorUserSocialAuth


class IntegrityErrorOnLoginTest(BaseActionTest):
    def setUp(self):
        super(IntegrityErrorOnLoginTest, self).setUp()
        self.strategy = TestStrategy(self.backend, IntegrityErrorStorage)

    def test_integrity_error(self):
        self.do_login()


class UnknownErrorOnLoginTest(BaseActionTest):
    def setUp(self):
        super(UnknownErrorOnLoginTest, self).setUp()
        self.strategy = TestStrategy(self.backend, UnknownErrorStorage)

    def test_unknown_error(self):
        self.do_login.when.called_with().should.throw(UnknownError)


class EmailAsUsernameTest(BaseActionTest):
    expected_username = 'foo@bar.com'

    def test_email_as_username(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL': True
        })
        self.do_login()


class RandomUsernameTest(BaseActionTest):
    user_data_body = json.dumps({
        'id': 1,
        'avatar_url': 'https://github.com/images/error/foobar_happy.gif',
        'gravatar_id': 'somehexcode',
        'url': 'https://api.github.com/users/foobar',
        'name': 'monalisa foobar',
        'company': 'GitHub',
        'blog': 'https://github.com/blog',
        'location': 'San Francisco',
        'email': 'foo@bar.com',
        'hireable': False,
        'bio': 'There once was...',
        'public_repos': 2,
        'public_gists': 1,
        'followers': 20,
        'following': 0,
        'html_url': 'https://github.com/foobar',
        'created_at': '2008-01-14T04:33:35Z',
        'type': 'User',
        'total_private_repos': 100,
        'owned_private_repos': 100,
        'private_gists': 81,
        'disk_usage': 10000,
        'collaborators': 8,
        'plan': {
            'name': 'Medium',
            'space': 400,
            'collaborators': 10,
            'private_repos': 20
        }
    })

    def test_random_username(self):
        self.do_login(after_complete_checks=False)


class SluggedUsernameTest(BaseActionTest):
    expected_username = 'foo-bar'
    user_data_body = json.dumps({
        'login': 'Foo Bar',
        'id': 1,
        'avatar_url': 'https://github.com/images/error/foobar_happy.gif',
        'gravatar_id': 'somehexcode',
        'url': 'https://api.github.com/users/foobar',
        'name': 'monalisa foobar',
        'company': 'GitHub',
        'blog': 'https://github.com/blog',
        'location': 'San Francisco',
        'email': 'foo@bar.com',
        'hireable': False,
        'bio': 'There once was...',
        'public_repos': 2,
        'public_gists': 1,
        'followers': 20,
        'following': 0,
        'html_url': 'https://github.com/foobar',
        'created_at': '2008-01-14T04:33:35Z',
        'type': 'User',
        'total_private_repos': 100,
        'owned_private_repos': 100,
        'private_gists': 81,
        'disk_usage': 10000,
        'collaborators': 8,
        'plan': {
            'name': 'Medium',
            'space': 400,
            'collaborators': 10,
            'private_repos': 20
        }
    })

    def test_random_username(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_CLEAN_USERNAMES': False,
            'SOCIAL_AUTH_SLUGIFY_USERNAMES': True
        })
        self.do_login()


class RepeatedUsernameTest(BaseActionTest):
    def test_random_username(self):
        User(username='foobar')
        self.do_login(after_complete_checks=False)
        expect(self.strategy.session_get('username').startswith('foobar')) \
                .to.equal(True)