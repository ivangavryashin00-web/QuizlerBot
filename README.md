# QuizletBot - AI-Powered Telegram Learning Assistant

AI-powered Telegram bot for creating and learning with flashcards. Features Claude AI integration, image support, and import/export functionality.

## Features

- ✅ Create unlimited flashcard decks
- ✅ Interactive learning mode
- ✅ Claude AI integration (definitions, examples, answer checking)
- ✅ Image support (JPG, PNG, WebP) with OCR
- ✅ Import/Export (CSV, JSON, Excel, PDF)
- ✅ Learning statistics and progress tracking
- ✅ SQLite database
- ✅ Telegram bot interface

## Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Anthropic API Key (optional, for AI features)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/quizlet-bot.git
cd quizlet-bot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your tokens
```

4. Run the bot
```bash
python main.py
```

## Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_token_here
ANTHROPIC_API_KEY=sk-ant-your_key_here
USE_AI_FEATURES=True
ENABLE_IMAGE_SUPPORT=True
```

## Deploy on Railway

1. Push to GitHub
2. Connect GitHub repo to Railway
3. Add environment variables in Railway dashboard
4. Railway will automatically deploy using Dockerfile

## Technology Stack

- Python 3.11
- python-telegram-bot 20.3
- SQLite3
- Anthropic Claude API
- Pillow (image processing)

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, open an issue on GitHub. 
