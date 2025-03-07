const sampleAgentData = [
  // Calendar agent - human source
  {
    source: 'human',
    type: 'calendar',
    data: {
      message: 'Can you please add a meeting to my calendar?'
    }
  },
  // Calendar agent - system source
  {
    source: 'system',
    type: 'calendar',
    data: {
      event: 'Team Meeting',
      date: '2023-10-15',
      time: '10:00 AM',
      description: 'Monthly team sync-up meeting',
      members: ['alice@example.com', 'bob@example.com']
    }
  },
  // Dineout Restaurant agent - human source
  {
    source: 'human',
    type: 'dineout_restaurant',
    data: {
      message: 'Book a table for two at an Italian restaurant tonight.'
    }
  },
  // Dineout Restaurant agent - system source
  {
    source: 'system',
    type: 'dineout_restaurant',
    data: {
      restaurantName: 'Luigi’s Italian Bistro',
      reservationTime: '7:00 PM',
      date: '2023-10-16',
      confirmationNumber: 'ABC1234'
    }
  },
  // Email agent - human source
  {
    source: 'human',
    type: 'email',
    data: {
      message: 'Send an email to John about the meeting.'
    }
  },
  // Email agent - system source
  {
    source: 'system',
    type: 'email',
    data: {
      subject: 'Meeting Reminder',
      recipient: 'john.doe@example.com',
      body: 'Don\'t forget about the meeting tomorrow at 10 AM.'
    }
  },
  // Online Order Restaurant agent - human source
  {
    source: 'human',
    type: 'online_order_restaurant',
    data: {
      message: 'Order a pizza from Pizza Palace.'
    }
  },
  // Online Order Restaurant agent - system source
  {
    source: 'system',
    type: 'online_order_restaurant',
    data: {
      restaurantName: 'Pizza Palace',
      items: ['Margherita Pizza', 'Garlic Bread'],
      totalCost: 25.5,
      estimatedDeliveryTime: '45 minutes'
    }
  },
  // Memory agent - human source
  {
    source: 'human',
    type: 'memory',
    data: {
      message: 'Remember that I prefer vegetarian options.'
    }
  },
  // Memory agent - system source
  {
    source: 'system',
    type: 'memory',
    data: {
      notes: 'User prefers vegetarian options.',
      timestamp: '2023-10-14T12:34:56Z'
    }
  },
  // Messages agent - human source
  {
    source: 'human',
    type: 'messages',
    data: {
      message: 'Hi, can you help me find a nice place to eat tonight?'
    }
  },
  // Messages agent - system source
  {
    source: 'system',
    type: 'messages',
    data: {
      message: 'Sure, I can help you find a restaurant for tonight.'
    }
  }
];


