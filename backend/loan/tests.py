#import json
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from channels.layers import get_channel_layer
from .models import Loan
from .consumers import ChatConsumer

class MockClass():
    def __init__(self):
        self.scope = {
            "url_route": {"kwargs":{"room_name": "test"}},
            "http_version": "1.1",
            "method": "POST",
            "path": "/test/",
        }
        self.channel_layer = get_channel_layer()
        self.room_group_name = "room"
        self.channel_name = "channel_name"

    def accept(self):
        pass

    def send(self, text_data):
        pass


class LoanTestCase(TestCase):
    def test_loan_list(self):
        client = Client()

        # test - no such api
        response = client.delete('/loan/loan')
        self.assertEqual(response.status_code, 405)

        # test - not logged in
        response = client.get('/loan/loan')
        self.assertEqual(response.status_code, 401)
        response = client.post('/loan/loan')
        self.assertEqual(response.status_code, 401)

        # login
        User.objects.create_user(username='username', password='password')
        User.objects.create_user(username='user2', password='password')
        client.login(username='username', password='password')

        # test - get
        response = client.get('/loan/loan')
        self.assertEqual(response.status_code, 200)

        # test - no request body
        response = client.post('/loan/loan')
        self.assertEqual(response.status_code, 400)

        # test - body is not json
        response = client.post('/loan/loan',
                               'This is a string',
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # make invalid data array
        invalid_data = [
            {
                'participants': None,
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [{'id': 1, 'paid_money': 50}, {'id': 2, 'paid_money': 100}],
                'deadline': None,
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [{'id': 1, 'paid_money': 50}, {'id': 2, 'paid_money': 100}],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': None,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [{'id': 1, 'paid_money': 50}, {'id': 2, 'paid_money': 100}],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': None,
                'alert_frequency': 'high',
            },
            {
                'participants': [{'id': 1, 'paid_money': 50}, {'id': 2, 'paid_money': 100}],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': None,
            },
            {
                'participants': [{'id': 1, 'paid_money': 50}, {'id': 2, 'paid_money': 100}],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': -1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [{'id': -1, 'paid_money': 50}, {'id': 2, 'paid_money': 100}],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
        ]

        # test - invalid input data
        for invalid_datum in invalid_data:
            response = client.post('/loan/loan',
                                   invalid_datum,
                                   content_type='application/json')
            self.assertEqual(response.status_code, 400)

        #make valid data
        valid_data = {'participants': [{'id': 1, 'paid_money': 50}, {'id': 2, 'paid_money': 100}],
                      'deadline': '2019-12-31T23:59:59Z', 'interest_rate': 1.5,
                      'interest_type': 'day', 'alert_frequency': 'high'}

        # test - valid input data
        response = client.post('/loan/loan',
                               valid_data,
                               content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # test - correct data
        try:
            loan = Loan.objects.get()
        except ObjectDoesNotExist:
            self.fail("The data is not stored")
        if loan.total_money != 150:
            self.fail("The data is not stored correctly")

    def test_loan(self):
        client = Client()

        response = client.post('/loan/loan/1', {}, content_type='application/json')
        self.assertEqual(response.status_code, 405)

        response = client.get('/loan/loan/1')
        self.assertEqual(response.status_code, 401)

        user = User.objects.create_user(username='user', password='pass')
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        client.login(username='user', password='pass')

        response = client.get('/loan/loan/1')
        self.assertEqual(response.status_code, 404)

        # make test data
        valid_data = [
            {
                'participants': [
                    {'id': user.id, 'paid_money': 100},
                    {'id': user1.id, 'paid_money': 50},
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [
                    {'id': user2.id, 'paid_money': 100},
                    {'id': user1.id, 'paid_money': 50},
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
        ]

        # test datas
        test_model = []
        for data in valid_data:
            response = client.post('/loan/loan', data, content_type='application/json')
            self.assertEqual(response.status_code, 201)
            test_model.append(response.json())

        response = client.get(f'/loan/loan/{test_model[1]["id"]}')
        self.assertEqual(response.status_code, 403)

        response = client.get(f'/loan/loan/{test_model[0]["id"]}')
        self.assertEqual(response.status_code, 200)

    def test_loan_transaction(self):
        client = Client()

        response = client.post('/loan/loan-transaction/1', {}, content_type='application/json')
        self.assertEqual(response.status_code, 405)

        response = client.get('/loan/loan-transaction/1')
        self.assertEqual(response.status_code, 401)

        user = User.objects.create_user(username='user', password='pass')
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        client.login(username='user', password='pass')

        response = client.get('/loan/loan-transaction/1')
        self.assertEqual(response.status_code, 404)

        # make test data
        valid_data = [
            {
                'participants': [
                    {'id': user.id, 'paid_money': 50},
                    {'id': user1.id, 'paid_money': 100}
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [
                    {'id': user2.id, 'paid_money': 50},
                    {'id': user1.id, 'paid_money': 100}
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [
                    {'id': user.id, 'paid_money': 0},
                    {'id': user1.id, 'paid_money': 100},
                    {'id': user2.id, 'paid_money': 100},
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [
                    {'id': user.id, 'paid_money': 0},
                    {'id': user1.id, 'paid_money': 0},
                    {'id': user2.id, 'paid_money': 100},
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
        ]

        # test datas
        test_model = []
        for data in valid_data:
            response = client.post('/loan/loan', data, content_type='application/json')
            self.assertEqual(response.status_code, 201)
            test_model.append(response.json())

        response = client.get(f'/loan/loan-transaction/{test_model[1]["id"]}')
        self.assertEqual(response.status_code, 403)

        response = client.get(f'/loan/loan-transaction/{test_model[0]["id"]}')
        self.assertEqual(response.status_code, 200)

    def test_transaction(self):
        client = Client()

        response = client.post('/loan/transaction/1', {}, content_type='application/json')
        self.assertEqual(response.status_code, 405)

        response = client.get('/loan/transaction/1')
        self.assertEqual(response.status_code, 401)

        user = User.objects.create_user(username='user', password='pass')
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        client.login(username='user', password='pass')

        response = client.get('/loan/transaction/1')
        self.assertEqual(response.status_code, 404)

        # make test data
        valid_data = [
            {
                'participants': [
                    {'id': user.id, 'paid_money': 50},
                    {'id': user1.id, 'paid_money': 100},
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [
                    {'id': user2.id, 'paid_money': 50},
                    {'id': user1.id, 'paid_money': 100},
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
            {
                'participants': [
                    {'id': user.id, 'paid_money': 100},
                    {'id': user1.id, 'paid_money': 0},
                    {'id': user2.id, 'paid_money': 0},
                ],
                'deadline': '2019-12-31T23:59:59Z',
                'interest_rate': 1.5,
                'interest_type': 'day',
                'alert_frequency': 'high',
            },
        ]

        # test datas
        test_model = []
        for data in valid_data:
            response = client.post('/loan/loan', data, content_type='application/json')
            self.assertEqual(response.status_code, 201)
            test_model.append(response.json())

        response = client.get('/loan/transaction/2')
        self.assertEqual(response.status_code, 403)

        response = client.get('/loan/transaction/1')
        self.assertEqual(response.status_code, 200)

        # test confirmation
        response = client.put('/loan/transaction/1')
        self.assertEqual(response.status_code, 200)

        response = client.put('/loan/transaction/2')
        self.assertEqual(response.status_code, 403)

        response = client.put('/loan/transaction/3')
        self.assertEqual(response.status_code, 200)

        client.login(username='user1', password='pass')
        response = client.put('/loan/transaction/1')
        self.assertEqual(response.status_code, 200)

        response = client.put('/loan/transaction/3')
        self.assertEqual(response.status_code, 200)

        client.logout()
        response = client.put('/loan/transaction/1')
        self.assertEqual(response.status_code, 401)

        response = client.get('/loan/chatroom/55886609')
        self.assertEqual(response.status_code, 200)

        response = client.get('/loan/chatroom/5588660900')
        self.assertEqual(response.status_code, 404)

class ConsumerTestCase(TestCase):
    def test_connect(self):
        mock_object = MockClass()
        ChatConsumer.connect(mock_object)
        ChatConsumer.disconnect(mock_object, 404)

        text_data = json.dumps({'message': 'message', 'name': 'name'})
        ChatConsumer.receive(mock_object, text_data)

        event = {'message': 'message', 'name': 'name'}
        ChatConsumer.chat_message(mock_object, event)

        self.assertEqual(event, {'message': 'message', 'name': 'name'})
