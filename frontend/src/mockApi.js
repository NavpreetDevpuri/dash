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

/**
 * Now accepts an object { text, attachment } instead of a plain string.
 */
export async function sendMessageApi(conversationId, messageObj) {
  await new Promise((resolve) => setTimeout(resolve, 600));

  // We'll return only the bot reply from here, since we show user message immediately.
  return {
    botReply: {
      id: Math.random(),
      text: `You said: "${messageObj.text}". This is a bot reply.`,
      sender: 'bot',
    },
  };
}

export async function logoutApi() {
  await new Promise((resolve) => setTimeout(resolve, 500));
  return { success: true };
}