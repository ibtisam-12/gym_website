from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.product.price * self.quantity

# ecommerce/models.py

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        # You can add other methods like 'credit_card', 'paypal', etc.
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cod')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def save(self, *args, **kwargs):
        # Get the old status if the order exists
        old_status = None
        if self.pk:
            try:
                old_status = Order.objects.get(pk=self.pk).status
            except Order.DoesNotExist:
                pass

        # Save the order
        super().save(*args, **kwargs)

        # If status has changed, log to blockchain
        if old_status != self.status:
            try:
                from blockchain.utils import blockchain
                from django.contrib.admin.models import LogEntry
                from django.contrib.contenttypes.models import ContentType
                from django.contrib.auth.models import User

                # Get the admin user who made the change
                content_type = ContentType.objects.get_for_model(self)
                log_entry = LogEntry.objects.filter(
                    content_type=content_type,
                    object_id=str(self.id),
                    action_flag=2  # CHANGE
                ).order_by('-action_time').first()

                # If no log entry found, try to get the last admin user
                admin_user = None
                if log_entry:
                    admin_user = log_entry.user
                else:
                    # Get the first superuser as fallback
                    admin_user = User.objects.filter(is_superuser=True).first()

                # Prepare data for blockchain
                data = {
                    'action': 'order_status_changed',
                    'order_id': self.id,
                    'admin_user': admin_user.username if admin_user else 'system',
                    'previous_status': old_status,
                    'new_status': self.status,
                    'timestamp': str(self.updated_at)
                }

                # Add to blockchain
                blockchain.add_block(data)
            except Exception as e:
                # Log the error but don't prevent the order from being saved
                print(f"Error logging to blockchain: {str(e)}")
                # You might want to add proper error logging here