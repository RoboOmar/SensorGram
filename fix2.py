import os

with open('frontend/js/feed.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix appendLiveComment
text = text.replace(r'document.querySelector(\[data-comment-id="\"\]\)', 'document.querySelector(`[data-comment-id="${data.id}"]`)')
text = text.replace(r'document.getElementById(\eplies-\\)', 'document.getElementById(`replies-${data.parent_comment_id}`)')

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
