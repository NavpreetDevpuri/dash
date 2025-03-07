from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import ConversationThread
from app.forms import ThreadForm

chat = Blueprint('chat', __name__)

# Global chatroom route (if needed)
@chat.route('/')
@login_required
def chatroom():
    return render_template('chatroom.html', title='Chatroom')

@chat.route('/create_thread', methods=['GET', 'POST'])
@login_required
def create_thread():
    form = ThreadForm()
    if form.validate_on_submit():
        thread = ConversationThread.create(creator_id=current_user.id, title=form.title.data)
        flash('Thread created successfully!', 'success')
        return redirect(url_for('chat.thread_chat', thread_id=thread.id))
    return render_template('create_thread.html', title='Create Thread', form=form)

@chat.route('/threads')
@login_required
def threads():
    from app.db import get_db
    db = get_db()
    query = "FOR t IN threads FILTER t.creator_id == @user_id RETURN t"
    cursor = db.aql.execute(query, bind_vars={'user_id': current_user.id})
    threads = [t for t in cursor]
    return render_template('threads.html', title='My Threads', threads=threads)

@chat.route('/thread/<thread_id>')
@login_required
def thread_chat(thread_id):
    thread = ConversationThread.get(thread_id)
    if not thread or thread.creator_id != current_user.id:
        flash('Access denied or thread not found', 'danger')
        return redirect(url_for('chat.chatroom'))
    return render_template('thread_chat.html', title=thread.title, thread=thread)