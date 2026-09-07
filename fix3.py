import os
import re

with open('frontend/js/feed.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the querySelector
text = re.sub(r'document\.querySelector\(\\[^)]+\)', 'document.querySelector(`[data-comment-id="${data.id}"]`)', text)
text = re.sub(r'document\.getElementById\(\\eplies-\\\\\)', 'document.getElementById(`replies-${data.parent_comment_id}`)', text)
text = re.sub(r'document\.getElementById\(\\comment-count-\\\\\)', 'document.getElementById(`comment-count-${data.post_id}`)', text)

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
