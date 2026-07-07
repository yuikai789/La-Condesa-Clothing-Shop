import os
os.chdir('c:\\Users\\Yuikai\\Documents\\Proyecto IV\\la_condesa')
from app import app

app.config['TESTING'] = True
client = app.test_client()

print('=== Testing Routes ===')

# Test 1: About page
response = client.get('/about')
print(f'About page: {response.status_code}')

# Test 2: Register page (GET)
response = client.get('/auth/register')
print(f'Register page: {response.status_code}')

# Test 3: Login page
response = client.get('/auth/login')
print(f'Login page: {response.status_code}')

# Test 4: Register with POST (duplicate)
response = client.post('/auth/register', data={
    'name': 'Test User',
    'email': 'test@example.com',
    'password': 'Test123!',
    'phone': '1234567890'
})
print(f'Register POST: {response.status_code}')

# Test 5: Register duplicate again
response = client.post('/auth/register', data={
    'name': 'Test User 2',
    'email': 'test@example.com',
    'password': 'Test123!',
    'phone': '1234567890'
})
print(f'Register duplicate: {response.status_code}')

print('=== Tests Complete ===')
