import os
import re

with open('frontend/js/feed.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the multi-line ones
text = re.sub(r'document\.getElementById\(\\\r?\neplies-\\\\\)', 'document.getElementById(`replies-${data.parent_comment_id}`)', text)
text = re.sub(r'document\.getElementById\(\\comment-count-\\\\\)', 'document.getElementById(`comment-count-${data.post_id}`)', text)
text = re.sub(r'input\.placeholder = Replying to  \+ authorName;', 'input.placeholder = `Replying to ` + authorName;', text)
text = re.sub(r'document\.getElementById\(comment-like-count- \+ commentId\);', 'document.getElementById(`comment-like-count-${commentId}`);', text)
text = re.sub(r'document\.getElementById\(comment-heart- \+ commentId\);', 'document.getElementById(`comment-heart-${commentId}`);', text)

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
