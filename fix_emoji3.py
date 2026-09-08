import os
import re

with open('frontend/js/feed.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'<span class="icon" id="comment-heart-\$\{c\.id\}"[^>]+>[^<]+</span>', '<span class="icon" id="comment-heart-${c.id}" style="font-size: 1.1em; color: ${likeColor}; transition: color 0.2s;">?</span>', text)

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
