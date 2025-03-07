document.addEventListener('DOMContentLoaded', function() {
  // Connect to the WebSocket server.
  const socket = io();

  const form = document.getElementById('chat-form');
  const chatBox = document.getElementById('chat-box');
  const messageInput = document.getElementById('message');
  // Optional hidden field if in a thread-specific chat.
  const threadInput = document.getElementById('thread-id');

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (message !== '') {
      let payload = { message: message, type: 'text' };
      if (threadInput) {
        payload['thread_id'] = threadInput.value;
      }
      socket.emit('send_message', payload);
      messageInput.value = '';
    }
  });

  socket.on('receive_message', function(data) {
    // If this is a thread-specific chat, only process messages matching the thread_id.
    if (threadInput && data.thread_id !== threadInput.value) {
      return;
    }
    const msgDiv = document.createElement('div');
    msgDiv.className = 'card-panel';
    msgDiv.textContent = 'Echo: ' + data.message;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  });
});