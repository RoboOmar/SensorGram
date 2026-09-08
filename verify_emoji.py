import os

with open('frontend/js/feed.js', 'r', encoding='utf-8') as f:
    text = f.read()

print('Crown present:', '\U0001F451' in text)
print('data-like present:', 'data-like="${post.id}"' in text)
