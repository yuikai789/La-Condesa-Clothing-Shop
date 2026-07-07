import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

results = []

def test(method, path, data=None, desc='', valid_statuses=None):
    try:
        if data:
            resp = client.open(path, method=method, data=data, follow_redirects=True)
        else:
            resp = client.open(path, method=method, follow_redirects=True)
        if valid_statuses:
            ok = resp.status_code in valid_statuses
        else:
            ok = resp.status_code < 400
        results.append((ok, method, path, resp.status_code, desc))
    except Exception as e:
        results.append((False, method, path, 'ERR', f'{desc} - {type(e).__name__}: {e}'))

print('=' * 70)
print('TESTING ALL PAGES')
print('=' * 70)

print('\n--- PUBLIC PAGES ---')
test('GET', '/')
test('GET', '/about')
test('GET', '/contact')
test('GET', '/catalog')
test('GET', '/catalog?category=1&size=M&min_price=0&max_price=1000')

print('\n--- AUTH PAGES ---')
test('GET', '/auth/login')
test('GET', '/auth/register')
test('POST', '/auth/register', {'name': 'Test User', 'email': 'testuser@test.com', 'password': 'Test1234a', 'phone': '5512345678'}, 'Register')
test('POST', '/auth/register', {'name': 'Test User', 'email': 'testuser@test.com', 'password': 'Test1234a', 'phone': '5512345678'}, 'Register duplicate')
test('POST', '/auth/login', {'email': 'testuser@test.com', 'password': 'Test1234a'}, 'Login')
test('GET', '/auth/logout', {}, 'Logout')

print('\n--- CUSTOMER PAGES ---')
with client.session_transaction() as sess:
    sess['_user_id'] = '1'
    sess['_fresh'] = True
test('GET', '/customer/dashboard', {}, 'Dashboard (as user 1)')
test('GET', '/customer/cart', {}, 'Cart')
test('GET', '/customer/orders', {}, 'Orders')
test('GET', '/customer/checkout', {}, 'Checkout (empty cart)')

print('\n--- EMPLOYEE PAGES ---')
test('GET', '/employee/dashboard', {}, 'Employee dashboard')
test('GET', '/employee/orders', {}, 'Employee orders')
test('GET', '/employee/sales', {}, 'Employee sales')
test('POST', '/employee/orders/1/mark-paid', {'payment_reference': 'REF123'}, 'Mark paid')
test('POST', '/employee/orders/1/prepare', {}, 'Prepare order')
test('POST', '/employee/orders/1/ready', {}, 'Ready for pickup')
test('POST', '/employee/orders/1/deliver', {}, 'Deliver order')

print('\n--- ADMIN PAGES ---')
test('GET', '/admin/dashboard', {}, 'Admin dashboard')
test('GET', '/admin/users', {}, 'Admin users')
test('GET', '/admin/products', {}, 'Admin products')
test('GET', '/admin/inventory', {}, 'Admin inventory')
test('GET', '/admin/analytics', {}, 'Admin analytics')

print('\n--- ADMIN CRUD ---')
test('POST', '/admin/users', {'name': 'New User', 'email': 'new@test.com', 'password': 'Test1234a', 'phone': '5512345678', 'role': 'employee'}, 'Create user')
test('POST', '/admin/users/2', {'name': 'Updated User', 'email': 'updated@test.com', 'role': 'customer'}, 'Update user')
test('POST', '/admin/products', {'name': 'Test Product', 'description': 'Test desc', 'base_price': '99.99', 'category_id': '1', 'sizes[]': 'M,L', 'stocks[]': '10,5', 'colors[]': 'Negro,Dorado'}, 'Create product')
test('POST', '/admin/products/1', {'name': 'Updated Product', 'base_price': '149.99', 'category_id': '1'}, 'Update product')
test('POST', '/admin/inventory/movements', {'product_id': '1', 'movement_type': 'purchase', 'quantity': '20', 'reason': 'Test'}, 'Add movement')

print('\n--- ERROR PAGES ---')
test('GET', '/nonexistent', {}, '404 page', valid_statuses=[404])

print('\n' + '=' * 70)
print('RESULTS')
print('=' * 70)
passed = sum(1 for r in results if r[0])
failed = sum(1 for r in results if not r[0])
for ok, method, path, status, desc in results:
    mark = 'OK' if ok else 'FAIL'
    print(f'  {mark} {method:4s} {str(status):3s} {path:45s} {desc}')
print(f'\n{passed} passed, {failed} failed out of {len(results)} tests')

if failed > 0:
    sys.exit(1)
else:
    print('ALL TESTS PASSED!')
