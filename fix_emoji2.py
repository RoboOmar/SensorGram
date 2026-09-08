import os
import re

with open('frontend/js/feed.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r"btn\.querySelector\('\.icon'\)\.textContent = '[^']+';", "btn.querySelector('.icon').textContent = isLiked ? '??' : '??';", text)

# Also fix the initial post icon because it might have been ?? for all
text = re.sub(r'<span class="icon">??</span>\n        <span class="like-count">', '<span class="icon">${post.liked_by_me ? \'??\' : \'??\'}</span>\n        <span class="like-count">', text)

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
