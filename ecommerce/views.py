from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Cart, CartItem, Category, Order
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import stripe
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Add this import
import re  # Add this import for browser detection

from blockchain.utils import blockchain  # Import the blockchain instance

def get_browser_name(user_agent):
    """Extract browser name from user agent string"""
    # Check for Edge first (since it contains Chrome in its user agent)
    if 'Edg/' in user_agent:
        return 'Microsoft Edge'
    
    # Common browser patterns
    browser_patterns = {
        'Chrome': r'Chrome/(\d+)',
        'Firefox': r'Firefox/(\d+)',
        'Safari': r'Safari/(\d+)',
        'Opera': r'OPR/(\d+)',
        'Internet Explorer': r'MSIE (\d+)',
    }
    
    for browser, pattern in browser_patterns.items():
        if re.search(pattern, user_agent):
            return browser
    return 'Unknown Browser'

def home(request):
    products = Product.objects.filter(is_active=True)  # Retrieve active products
    return render(request, 'ecommerce/home.html', {'products': products})

# def product_detail(request, slug):
#     product = get_object_or_404(Product, slug=slug)  # Retrieve product by slug
#     return render(request, 'ecommerce/product_detail.html', {'product': product})
def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    return render(request, 'ecommerce/product_detail.html', {'product': product})


def ecommerce_view(request, page_type=None, product_slug=None):
    """
    A unified view that handles:
    - Homepage
    - Product detail page
    - Add to cart
    - View cart
    - Checkout
    """
    # If the user is not logged in, redirect them to the login page (for non-authenticated pages)
    if not request.user.is_authenticated and page_type != 'login':
        return redirect('user_login')

    # Homepage: Display featured products
    if page_type == 'home' or page_type is None:
        products = Product.objects.filter(is_active=True)  # Get active products
        return render(request, 'ecommerce/home.html', {'products': products})

    # Product Detail Page
    if page_type == 'product_detail' and product_slug:
        product = get_object_or_404(Product, slug=product_slug)  # Get the product by slug
        return render(request, 'ecommerce/product_detail.html', {'product': product})

    # Add to Cart
    if page_type == 'add_to_cart' and product_slug:
        product = get_object_or_404(Product, slug=product_slug)

        # Get or create the user's cart
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Get or create the cart item
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        # Increase quantity if the item is already in the cart
        cart_item.quantity += 1
        cart_item.save()

        return redirect('view_cart')  # Redirect to the cart view

    # View Cart
    if page_type == 'view_cart':
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            return render(request, 'ecommerce/cart.html', {'cart': cart})
        else:
            return render(request, 'ecommerce/cart.html', {'message': 'Your cart is empty.'})

    # Checkout
    if page_type == 'checkout':
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            total_amount = cart.total  # Calculate total price
            return render(request, 'ecommerce/checkout.html', {'cart': cart, 'total_amount': total_amount})
        else:
            return render(request, 'ecommerce/checkout.html', {'message': 'Your cart is empty.'})

    # If no matching page_type found, show a 404 error
    return HttpResponse("Page not found", status=404)

def equipment(request):
    # Get the 'Equipment' category
    category = Category.objects.get(name='Equipment')
    products = Product.objects.filter(category=category)
    return render(request, 'ecommerce/equipment.html', {'products': products})

def apparel(request):
    # Get the 'Apparel' category
    category = Category.objects.get(name='Apparel')
    products = Product.objects.filter(category=category)
    return render(request, 'ecommerce/apparel.html', {'products': products})

def supplements(request):
    # Get the 'Supplements' category
    category = Category.objects.get(name='Supplements')
    products = Product.objects.filter(category=category)
    return render(request, 'ecommerce/supplements.html', {'products': products})


def contact(request):
    if request.method == "POST":
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Send an email (you can configure this in Django settings)
        try:
            send_mail(
                f'New message from {name}',  # Subject
                message,  # Message body
                email,  # From email
                [settings.DEFAULT_FROM_EMAIL],  # To email
                fail_silently=False,
            )
            return HttpResponse('<h3>Thank you for reaching out! We will get back to you soon.</h3>')
        except:
            return HttpResponse('<h3>Sorry, something went wrong. Please try again later.</h3>')

    return render(request, 'ecommerce/contact.html')

# Update cart: Update quantity of an item in the cart
def update_cart(request):
    if request.method == 'POST':
        cart = Cart.objects.get(user=request.user)
        for item in cart.items.all():
            quantity = request.POST.get(f'quantity_{item.id}')
            item.quantity = int(quantity)
            item.save()
        return redirect('view_cart')

# Remove item from cart
def remove_from_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.delete()
    return redirect('view_cart')

# Process checkout: Handle order confirmation and payment

    if request.method == 'POST':
        # Get user information and payment details
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cvv = request.POST.get('cvv')

        # Here, implement payment gateway logic (e.g., Stripe/PayPal)

        # After payment is processed, create an order
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            address=address,
            phone=phone,
            total_amount=request.session.get('cart_total'),
        )

        # Clear cart after checkout
        Cart.objects.filter(user=request.user).delete()

        return HttpResponse('<h3>Your order has been confirmed! Thank you for shopping with us!</h3>')


def order_confirmation(request, order_id):
    """
    Order confirmation view for displaying order details after checkout.
    """
    try:
        # Fetch the order based on the order_id
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        # If the order does not exist, return a 404 page or an error message
        return render(request, 'ecommerce/order_not_found.html')

    # Render the order confirmation template with the order details
    return render(request, 'ecommerce/order_confirmation.html', {'order': order})

# ecommerce/views.py

# ecommerce/views.py
def success(request):
    return render(request, 'success.html')

def cancel(request):
    return render(request, 'cancel.html')
# ecommerce/views.py

@staff_member_required
def confirm_cod_payment(request, order_id):
    order = Order.objects.get(id=order_id)
    order.status = 'processing'
    order.save()
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    browser_name = get_browser_name(user_agent)

    # Log admin confirmation to blockchain
    confirmation_data = {
        'action': 'order_confirmed',
        'order_id': order.id,
        'admin_user': request.user.username,
        'previous_status': 'pending',
        'new_status': 'processing',
        'timestamp': str(order.updated_at),
        'browser_info': browser_name,
        'ip_address': request.META.get('REMOTE_ADDR', 'Unknown')
    }
    blockchain.add_block(confirmation_data)

    return redirect('order_confirmation', order_id=order.id)

@staff_member_required
def mark_order_shipped(request, order_id):
    order = Order.objects.get(id=order_id)
    order.status = 'shipped'
    order.save()
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    browser_name = get_browser_name(user_agent)

    # Log shipping confirmation to blockchain
    shipping_data = {
        'action': 'order_shipped',
        'order_id': order.id,
        'admin_user': request.user.username,
        'previous_status': 'processing',
        'new_status': 'shipped',
        'timestamp': str(order.updated_at),
        'browser_info': browser_name,
        'ip_address': request.META.get('REMOTE_ADDR', 'Unknown')
    }
    blockchain.add_block(shipping_data)

    return redirect('order_confirmation', order_id=order.id)

@staff_member_required
def blockchain_admin(request):
    return render(request, 'ecommerce/blockchain_admin.html', {'blockchain': blockchain})
# ecommerce/views.py

def user_register(request):
    if request.method == 'POST':
        print("POST request received for registration")  # Debug log
        form = UserCreationForm(request.POST)
        print(f"Form data: {request.POST}")  # Debug log
        
        if form.is_valid():
            print("Form is valid")  # Debug log
            try:
                user = form.save()
                print(f"User created: {user.username}")  # Debug log
                
                # Get browser name from user agent
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
                browser_name = get_browser_name(user_agent)
                
                # Log registration event to blockchain
                data = {
                    'action': 'register',
                    'user': user.username,
                    'browser': browser_name,  # Store only browser name
                    'ip_address': request.META.get('REMOTE_ADDR', 'Unknown')
                }
                print(f"Attempting to add block to blockchain with data: {data}")  # Debug log
                
                try:
                    blockchain.add_block(data)  # Add the registration block to the blockchain
                    print("Block successfully added to blockchain")  # Debug log
                    messages.success(request, 'You have registered successfully!')
                except Exception as e:
                    print(f"Error adding block to blockchain: {str(e)}")  # Debug log
                    messages.warning(request, f'Registration successful, but blockchain logging failed: {str(e)}')
                
                login(request, user)  # Automatically log in the user after registration
                print("User logged in")  # Debug log
                
                return redirect('home')  # Redirect to home page after registration
            except Exception as e:
                print(f"Error during user creation: {str(e)}")  # Debug log
                messages.error(request, f'Error during registration: {str(e)}')
        else:
            print(f"Form errors: {form.errors}")  # Debug log
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()
    
    return render(request, 'ecommerce/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Get browser name from user agent
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            browser_name = get_browser_name(user_agent)
            
            # Log login event to blockchain
            data = {
                'action': 'login',
                'user': user.username,
                'browser': browser_name,  # Store only browser name
                'ip_address': request.META.get('REMOTE_ADDR', 'Unknown')
            }
            blockchain.add_block(data)  # Add the login block to the blockchain
            
            return redirect('home')  # Redirect to home page after login
        else:
            return HttpResponse('Invalid credentials', status=400)
    return render(request, 'ecommerce/login.html')

@login_required
def user_logout(request):
    # Get browser name from user agent
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    browser_name = get_browser_name(user_agent)
    
    # Log logout event in blockchain
    data = {
        'action': 'logout',
        'user': request.user.username,
        'browser': browser_name,  # Store only browser name
        'ip_address': request.META.get('REMOTE_ADDR', 'Unknown')
    }
    blockchain.add_block(data)  # Add the logout block to the blockchain
    logout(request)  # Log the user out
    return redirect('home')  # Redirect to home after logout


@login_required
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty.')
        return redirect('view_cart')

    if request.method == 'POST':
        full_name = request.POST['full_name']
        email = request.POST['email']
        address = request.POST['address']
        phone = request.POST['phone']
        city = request.POST['city']
        state = request.POST['state']
        pincode = request.POST['pincode']
        
        payment_method = 'cod'  # Always Cash on Delivery

        # Create an order with COD payment method
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            email=email,
            address=address,
            phone=phone,
            city=city,
            state=state,
            pincode=pincode,
            total_amount=cart.total,
            payment_method=payment_method,
        )
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        browser_name = get_browser_name(user_agent)


        # Log order creation to blockchain with detailed information
        order_data = {
            'action': 'order_placed',
            'order_id': order.id,
            'user': request.user.username,
            'total_amount': str(order.total_amount),
            'payment_method': payment_method,
            'shipping_address': {
                'full_name': full_name,
                'address': address,
                'city': city,
                'state': state,
                'pincode': pincode
            },
            'items': [
                {
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': str(item.product.price),
                    'subtotal': str(item.subtotal)
                } for item in cart.items.all()
            ],
            'browser_info':browser_name,
            'ip_address': request.META.get('REMOTE_ADDR', 'Unknown'),
            'timestamp': str(order.created_at)
        }
        blockchain.add_block(order_data)

        # Clear the cart after order creation
        Cart.objects.filter(user=request.user).delete()

        return redirect('order_confirmation', order_id=order.id)

    return render(request, 'ecommerce/checkout.html', {'cart': cart})