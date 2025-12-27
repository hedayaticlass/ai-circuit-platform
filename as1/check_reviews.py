import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as1.settings')
django.setup()

from home.models import Review

# Check reviews
reviews = Review.objects.all()
print(f'Total reviews: {reviews.count()}')

for review in reviews[:10]:
    user_name = review.user.username if review.user else "guest"
    comment_preview = review.comment[:50] if review.comment else "None"
    print(f'Review {review.id}: rating={review.rating}, user={user_name}')
