import os
import re

with open('frontend/js/feed.js', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Replace empty state robot
text = re.sub(r'<div class="empty-state-icon">[^<]+</div>', '<div class="empty-state-icon">\U0001F916</div>', text)

# Replace delete button trash can
text = re.sub(r'<span class="icon">[^<]+</span></button>`', '<span class="icon">\U0001F5D1\uFE0F</span></button>`', text)

# Replace post heart icon
# We need to catch either the corrupted strings or previously bad substitutions
text = re.sub(r'<span class="icon">[^<]*</span>\s*<span class="like-count">', '<span class="icon">${post.liked_by_me ? \'\u2764\uFE0F\' : \'\U0001F90D\'}</span>\n        <span class="like-count">', text)

# Replace comment bubble icon
text = re.sub(r'<span class="icon">[^<]*</span>\s*<span id="comment-count-', '<span class="icon">\U0001F4AC</span>\n        <span id="comment-count-', text)

# Replace comment heart icon
text = re.sub(r'<span class="icon" id="comment-heart-\$\{c\.id\}"[^>]+>[^<]*</span>', '<span class="icon" id="comment-heart-${c.id}" style="font-size: 1.1em; color: ${likeColor}; transition: color 0.2s;">\u2665</span>', text)

# Replace send comment button arrow
text = re.sub(r'<button class="btn btn-primary btn-icon" type="submit" aria-label="Send comment">[^<]+</button>', '<button class="btn btn-primary btn-icon" type="submit" aria-label="Send comment">\u27A4</button>', text)

# Replace JS heart toggle
text = re.sub(r"btn\.querySelector\('\.icon'\)\.textContent = isLiked \? '[^']+' : '[^']+';", "btn.querySelector('.icon').textContent = isLiked ? '\u2764\uFE0F' : '\U0001F90D';", text)

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
