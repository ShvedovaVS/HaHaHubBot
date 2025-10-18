Technical Documentation for HaHaHubBot (@ha_ha_hub_bot)

1. Introduction
This document describes the work of a Telegram bot. The bot's name is "HaHaHubBot". The main goal of this bot is to find and send memes to users. Users can search for memes using categories or specific words. The primary audience for this Meme Bot is general Telegram users looking for quick entertainment. The bot is designed for young people familiar with internet meme culture, users seeking content for a specific mood, and those who prefer simple button-based navigation over typing commands. Essentially, it serves anyone who wants to find and share relevant memes instantly without any complexity.

3. Main Functions
The bot has two main ways to search for memes.
 Search by Categories (Поиск по категориям): the user chooses a category and then chooses options inside the category to find a meme.
 Search by Words (Поиск по словам): the user can type any word or phrase to find a meme.

5. How the Bot Works: User Scenarios
The bot works through a system of menus. The user presses buttons to navigate.

3.1. Navigation Buttons
•	Назад: This button takes the user to the previous menu.
•	Начать сначала: This button takes the user back to the very beginning (the main menu).
•	Выйти: This button stops the interaction with the bot.

3.2. Starting the Bot
When the user starts the bot, they see the main menu:
•	Поиск по категориям
•	Поиск по словам
•	Начать сначала
•	Выйти

3.3. Scenario 1: Search by Words (Поиск по словам)
1.  The user presses «Поиск по словам».
2.  The bot asks: «Введи слово или фразу для поиска».
3.  The user types a word, for example, «КОТ».
4.  The bot finds a meme with this word and shows it.
5.  After showing the meme, the bot gives new options:
•	Следующий мем
•	Показать показанные мемы
•	Новый поиск
•	Начать сначала
•	Выйти
If nothing is found, the bot sends a message: «По словам ничего не найдено» (Nothing found for these words).

3.4. Scenario 2: Search by Categories (Поиск по категориям)
1.  The user presses «Поиск по категориям».
2.  The bot shows a menu with categories:
•	Юмор
•	Сарказм
•	Оскорбление
•	Мотивация
•	Настроение
•	Назад
3.  The user chooses a category, for example, «Оскорбление».
4.  The bot then shows a sub-menu with levels for this category:
•	Не оскорбительно
•	Лёгкое
•	Очень
•	Ненавистно
•	Назад
•	Начать сначала
5.  The user chooses a level, for example, «Лёгкое».
6.  The bot finds a matching meme and shows it.
7.  After the meme, the bot gives options (same as in 3.2, step 5).

Another example for the «Мотивация» category
After choosing «Мотивация», the bot shows a simple sub-menu:
•	Не мотивирует
•	Мотивирует
•	Назад
•	Начать сначала

4. Technical Details
Platform: the bot is built for Telegram.
Interaction Type: the bot uses inline keyboards (buttons under the chat) for user input. This makes it easy for the user to click instead of typing commands.
Data Storage: the bot must have a database to store:
    Memes (photos).
    Tags for each meme (like categories, levels, keywords).
Logic: the bot's main job is to take the user's choice from the buttons, find a suitable meme in the database, and send it.

6. Conclusion
HaHaHubBot is a simple and user-friendly tool for finding memes. It uses a clear button-based menu, so users do not need to remember commands. The two search methods (by category and by word) help users find the perfect meme for their mood.
