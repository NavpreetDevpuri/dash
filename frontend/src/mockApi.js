// src/mockApi.js
export async function signInApi(email, password) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  if (email === 'test@example.com' && password === 'password') {
    return {
      success: true,
      token: 'dummy-jwt-token',
      user: {
        id: 1,
        name: 'Test User',
        email,
      },
    };
  } else {
    return {
      success: false,
      error: 'Invalid credentials',
    };
  }
}

export async function signUpApi(email, password) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  return {
    success: true,
    token: 'dummy-jwt-token-signup',
    user: {
      id: 2,
      name: 'New User',
      email,
    },
  };
}

export async function fetchConversationsApi() {
  await new Promise((resolve) => setTimeout(resolve, 600));
  // We'll return an empty array for "recent conversation" demonstration
  // because pinned items are now separate in the UI
  return [];
}

export async function fetchMessagesApi(conversationId) {
  await new Promise((resolve) => setTimeout(resolve, 600));
  // Return some dummy messages
  return [
    { id: 101, text: 'Hello from the bot!', sender: 'bot' },
    { id: 102, text: 'How can I help?', sender: 'bot' },
  ];
}

export async function sendMessageApi(conversationId, message) {
  await new Promise((resolve) => setTimeout(resolve, 600));
  return {
    userMessage: {
      id: Math.random(),
      text: message,
      sender: 'user',
    },
    botReply: {
      id: Math.random(),
      text: `You said: "${message}". This is a bot reply.`,
      sender: 'bot',
    },
  };
}

export async function logoutApi() {
  await new Promise((resolve) => setTimeout(resolve, 500));
  return { success: true };
}