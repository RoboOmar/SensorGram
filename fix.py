import os

with open('frontend/js/feed.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix appendLiveComment
text = text.replace(r'document.getElementById(\comments-list-\\)', 'document.getElementById(`comments-list-${data.post_id}`)')
text = text.replace(r'document.querySelector(\[data-comment-id="\"\]\)', 'document.querySelector(`[data-comment-id="${data.id}"]`)')
text = text.replace(r'document.getElementById(\post-\\)', 'document.getElementById(`post-${data.post_id}`)')
text = text.replace(r'document.getElementById(\eplies-\\)', 'document.getElementById(`replies-${data.parent_comment_id}`)')
text = text.replace(r'document.getElementById(\comment-count-\\)', 'document.getElementById(`comment-count-${data.post_id}`)')

# Fix click listener
text = text.replace(r'input.placeholder = Replying to  + authorName;', 'input.placeholder = `Replying to ` + authorName;')
text = text.replace(r'document.getElementById(comment-like-count- + commentId);', 'document.getElementById(`comment-like-count-${commentId}`);')
text = text.replace(r'document.getElementById(comment-heart- + commentId);', 'document.getElementById(`comment-heart-${commentId}`);')

with open('frontend/js/feed.js', 'w', encoding='utf-8') as f:
    f.write(text)
