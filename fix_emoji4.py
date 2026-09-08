import os
import re

with open('frontend/js/feed.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix data-like-post
text = text.replace('data-like-post="${post.id}"', 'data-like="${post.id}"')

# Fix Creator badge emoji
text = re.sub(r'<span class="creator-badge"[^>]*>[^<]*</span>', '<span class="creator-badge" title="Creator" style="color: #ffd700; font-size: 0.8em; margin-left: 4px;">\U0001F451</span>', text)

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
