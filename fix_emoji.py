import os
import re

with open('frontend/js/feed.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Replace empty state robot
text = re.sub(r'<div class="empty-state-icon">[^<]+</div>', '<div class="empty-state-icon">??</div>', text)

# Replace delete button trash can
text = re.sub(r'<span class="icon">[^<]+</span></button>`', '<span class="icon">???</span></button>`', text)

# Replace heart icons (like button and comment like button)
# Wait, some are <span class="icon">heart</span>
text = re.sub(r'<span class="icon">[^<]+</span>\s*<span class="like-count">', '<span class="icon">??</span>\n        <span class="like-count">', text)

# Replace comment bubble icon
text = re.sub(r'<span class="icon">[^<]+</span>\s*<span id="comment-count-', '<span class="icon">??</span>\n        <span id="comment-count-', text)

# Replace comment heart icon
text = re.sub(r'<span class="icon" id="comment-heart-\$\{c\.id\}"[^>]+>[^<]+</span>', '<span class="icon" id="comment-heart-${c.id}" style="font-size: 1.1em; color: ${likeColor}; transition: color 0.2s;">??</span>', text)

# Replace send comment button arrow
text = re.sub(r'<button class="btn btn-primary btn-icon" type="submit" aria-label="Send comment">[^<]+</button>', '<button class="btn btn-primary btn-icon" type="submit" aria-label="Send comment">?</button>', text)

# Replace JS heart toggle
# btn.querySelector('.icon').textContent = isLiked ? '...' : '...';
text = re.sub(r"btn\.querySelector\('\.icon'\)\.textContent = isLiked \? '[^']+' : '[^']+';", "btn.querySelector('.icon').textContent = '??';", text) # Wait, isLiked was actually changing the color in CSS, but let's just make sure the heart stays or changes correctly. Actually, let's keep it '??' for both and rely on CSS, or use '??' and '??'. Originally it was ? and ? or something.

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
