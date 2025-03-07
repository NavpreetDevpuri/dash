this is how my app will look. I want you to carefully analyze it and guide me step by step on how to create it. I am new to this and a fresher, so please explain everything clearly. The app should look like ChatGPT but with additional icons or tabs. Please use React. 

wherever possible use, use some library like matterial UI, 

think hard 


- I don't need backend code for now, add proper api calls to load recent comversations, messages and send messages, get reply,
Open pop up for logout, also have signup signin UI, with proper dummy api calls, justy mock the response, while still have all the functionality, ready to use after replacing the API calls, 
- dark mode 
- i want icon on left like instead "My ChatGPT-like APP", it should be "close sidebar icon", "search icon", and "new chat icon", not in words, only icons
- instead of conversation 1,2,3, i want to show "Food order", "Dineout booking", "Calender", "Email", "Messages". Write exact words but add imojis in front like add food imogis in front of food.
- write how many "Food order", "Dineout booking", "Calender", "Email", "Messages" are upcoming or unread next to "Food order", "Dineout booking", "Calender", "Email", "Messages". Show the numbers only like 1,2,3
- Below food order, dine out booking etc add "recent conversation"
- below "recent conversation" add all the recents conversation that have been done, and it should be infinity like chatgpt
- above setting and logout, there should be profile icon
- in "type your message" add upload icon on left side and add speak to text, voice assistant, and send message(it only appears when we start typing"), on right side. Add only icons


update with below details, read properly and think hardly and give me updates codes

---

- Search dummy API to open a new conversation. For now, persist this dummy API data in local storage only.  
- text and background colours are same, unable to read , keep text or all the words in white so we can read it easily.  
- (`🍔 Food order (1)`, `🍽️ Dineout booking (2)`, `📅 Calendar (3)`, `📧 Email (4)`, `💬 Messages (5)`) — Numbers 1, 2, 3, 4, and 5 should appear as notification circular numbers and be clickable. Clicking them should open a conversation, call the dummy API to get details, and display them in a user-friendly UI as a card at the top of the new conversation.  
- The conversation should have a small icon, just like on the left side. Clicking the icon should show the content. The card should remain on top of all messages when scrolling up. When at the bottom or middle, clicking the icon should open a pop-up with details.  
- Recent conversations should be clickable and open in the correct conversation thread.  
- There should be no scrollbar.  
- Profile, settings, and logout icons should be in the top-right corner, not at the bottom left.  
- The mic icon should start speech-to-text in the input box.  
- The attachment icon should open the file selector and send the file as an attachment via API.  
- The search bar should open a pop-up for searching, which will call the dummy API to get conversation results. Matching messages should appear as a list with `...` at the beginning and end if the message is long. Clicking a result should navigate to the conversation, properly highlighting the matched message while handling scrolling.  
- Infinite scrolling should be enabled for conversations. When opening a matched message, scrolling up or down should load more messages.  
- There should be a button to scroll to the bottom when clicked.  

----

THINK HARD




update with below details, read properly and think hardly and give me updates codes

---

- Icon on the left side for food orders, dine-out bookings, etc., should be at the end of each block so they appear in vertical alignment.  
- The input box is still white, and the surrounding is also white. The input box background is dark with dark text color—make it white and fix it.  
- The chatroom is not persisting with the conversation. When I reopen the same chat, it should show the message history.  
- The conversation is not scrollable; it just expands endlessly if we keep sending new messages. It should be scrollable.  
- Conversation details don’t need to be shown always. I should be at the top, meaning it should be at the top of the messages in the message history, just like the "Group created by" info in WhatsApp.  
- The conversation should have a title on top with edit and delete options, along with an info button that opens a pop-up. This should only appear if the conversation is initiated from categories like food orders. The 2-3 icons should be on the right side, and the title should be on the left. The title can be concatenated with "..." just before those icons on the right side.  
- The conversation list in the left-side panel should also have edit and select icons. The edit icon should open a pop-up for changing the conversation title.  
- Add more conversations and make the search function work using dummy APIs, storing data in local storage for now. Implement a basic text search for conversations.  
- The main app window still has some padding, causing an extra scrollbar. Fix it.  
- The sign-in and sign-up pages are still white-themed and not well-designed.  
- The settings icon is not opening a pop-up with some dummy settings. The left side should show categories, and the right side should show properties in the pop-up. For example, selecting "Model" on the left should display options like OpenAI, etc., with an input box (password-type) to add an API key.  
- The scrollbar is still white-themed for the left panel.  
- "Recent Conversations" should be a separate block with a scrollbar, distinct from food orders, etc.  
- The scrollbar looks basic; add a better one.  
- The minimize and expand icon is not changing for the left panel.  
- The moment I select an attachment, it just sends the message. The attachment should be shown clipped on top of the input box, allowing me to still write the message. The message should only be sent after pressing Enter or the send button.

----

THINK HARD


update with below details, read properly and think hardly and give me updates codes

--- 

- No need for an edit icon or delete options for pinned conversations.  
- "Recent Conversations" should not scroll with other conversations; keep it like a header for the scroll area.  
- Pinned conversations are showing the wrong title; it should also include an icon before it, and the "more info" icon popup should be a little wider.  
- Chatroom scroll is still not working.  
- The chatroom input box should allow multi-line input.  
- Speech-to-text does not have any indication of when it starts or stops, and it is closing automatically after a few seconds if I don’t speak. It also listens to only one line; I want it to keep listening until I turn it off.  
- Attachments with proper file icons and names are not showing up on top of the chat input box. After sending messages, they should also appear as a box containing the attachment on top of the message. If possible, for previewable files like images, videos, PDFs, etc., show a proper preview, and clicking on it should open a large popup.  
- All the popups are not having a close icon.  
- The conversation edit popup should be wider.  
- There should be a delete icon for non-pinned conversations as well. The top bar for conversations should also be shown for those, but no need for an info icon.  
- In settings, models should be on the left side, with the dropdown and API key on the right side.  
- In settings, add "Memories" on the left side, and on the right side, show a list of memories fetched from a dummy API with options to edit and delete.  
- The search function is still not working. It should search messages and display a list of matching messages. Clicking on a result should open the conversation containing that message and display it, allowing users to load older or newer messages from that point, similar to WhatsApp or Facebook Messenger.
------

THINK HARD AND TAKE YOUR TIME




update with below details, read properly and think hardly and give me updates codes

-------

- the search botton is not working, when i type something it should show to everywhere suppose when i say "hello", it should capture and find out from all the chat room, rcent conversation or new message where "hello" word has. For example: consider whatsapp sreenshot which i have attached for this.
- profile button is not working, under the profile icon, it should have name, phone number, email.
- on middle top "conversation 123..." and edit, delete, they should not be there, remove it.
- all the conversation under the recent conversation should have delete button icon next to edit icon, delete and edit can only see when i hover on the conversation title otherwise dont show it.
- also keep same background but little light colour from background theme in "type your message" box, it shouldnot be white. and words which we are gona type should be all white, all the words should be white and dont keep "blue" colour when i send the message, it should be same colour like agent replied colour. Keep agent replied colour same as background theme.
- when i select some files or docs to upload, it should be visible on the chatbox whether it is succesfully uploaded on it before sending it same like chatgpt 
- when we talk by clicking on the mic, it should show like recording audio line like chatgpt. Also, there should be different icon to stop it. 
- memory under the memories in the settings should have "edit" and "delete" icons on right side and it should work delet and edit
- when i click on "save" icon one notification should pop-up like "successfully save" in select model information unbder the models 
- purple colour should be round which are available on right side of "food order, dineout booking etc". When i click on "1" or "2" it should show the status of them. It can also have the conversation below the status like when i click on "food order 1" it should show in the conversation top like "your food is preparing..." and under it should have conversation where agent and user start can have converstion like agent "your food is preparing and it will be deliver within 10 mins" and user response "thanks for the update"
- when we have long conversation, it is still showing white on the left side, it should be same colour like black and type box shouldn't scroll down, it should be the same where it is, only conversation can scroll up and down how long it is. See the screenshot attachment for your reference

------

THINK HARD AND TAKE YOUR TIME


update with below details, read properly and think hardly and give me updates codes

------

- memory is not deleting when we delete it, it keeps coming. Also, add different to add new memory
- ther are should be "edit" and "update" icon should be there for name, phone number and email id. Also, it should save whenever we edit or update any information like name or phone number or email. Write "Phone number" instead of "Phone" and "Email ID" instad of "Email"
- when we search something in search icon and click on it, it should open that chat. Suppose i serach "Hi" and many chats came that has "hi" and i click on any chat and that chat should open.
- when we click on any chat under recent conversations, it should highlight with little colour change so it will know which conversation or chat i open
- keep background theme little light, it is very dark
- when we click on attach file icon, it should say "Upload files or more" and when we click on mic and start saying something it should be live, it should not be slow, whenenver we speak everything should write down in live on chatbox
- file, mic, send icons etc, make it white

THINK HARD AND TAKE YOUR TIME

find . -type d -name node_modules -prune -o -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.css" \) -exec echo "{}" \; -exec cat "{}" \;

