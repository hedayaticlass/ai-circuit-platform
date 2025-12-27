import os
import sys
import django

# Setup Django
sys.path.append('as1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'as1.settings')
django.setup()

from home.models import Review, ChatMessage

# Check reviews
reviews = Review.objects.all()
print(f'Total reviews: {reviews.count()}')

approved_reviews = Review.objects.filter(is_approved=True)
print(f'Approved reviews: {approved_reviews.count()}')

for review in approved_reviews:
    user_name = review.user.username if review.user else "guest"
    comment_preview = review.comment[:50] if review.comment else "None"
    print(f'\nReview {review.id}: rating={review.rating}, user={user_name}, comment={comment_preview}')
    print(f'  chat_history_message_id: {review.chat_history_message_id}')

    if review.chat_history_message_id:
        try:
            message = ChatMessage.objects.get(id=review.chat_history_message_id, role='assistant')
            print(f'  Message found: {message.id}')

            # Check python code
            python_code = None
            if message.content_json and isinstance(message.content_json, dict):
                python_code = message.content_json.get('pythonCode') or message.content_json.get('python_code')

            if not python_code and message.content_text:
                if 'import matplotlib' in message.content_text or 'def draw_circuit' in message.content_text:
                    python_code = message.content_text

            if python_code:
                print(f'  Python code found: {len(python_code)} chars')
            else:
                print('  No python code found')

        except ChatMessage.DoesNotExist:
            print(f'  Message NOT found!')
    else:
        print('  No chat message')
