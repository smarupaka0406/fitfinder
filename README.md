# ✨ FitFinder MVP

Find visually similar, lower-cost fashion alternatives using image or link input.

## Quick Start

```bash
chmod +x quickstart.sh
./quickstart.sh
```

Then open **two terminals**:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` 🎉

## User Flow

1. **Upload Image** or **Paste Link** - Enter a fashion item
2. **Search** - Backend analyzes and finds alternatives
3. **View Results** - See similar items with prices
4. **Filter** - Sort by price and similarity
5. **Purchase** - Click to buy

## Project Structure

```
MyFirstMVP/
├── backend/              # Python Flask API
│   ├── app.py           # Main Flask app
│   ├── config.py        # Configuration
│   ├── database.py      # SQLAlchemy setup
│   ├── models.py        # Database models
│   └── requirements.txt # Python dependencies
│
├── frontend/            # React + TypeScript UI
│   ├── src/
│   │   ├── App.tsx      # Main component
│   │   ├── components/  # React components
│   │   ├── styles/      # CSS files
│   │   └── main.tsx     # Entry point
│   ├── package.json
│   ├── vite.config.ts
│   └── index.html
│
├── README.md
└── quickstart.sh
```

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Python Flask + SQLAlchemy
- **Database**: SQLite (development)

## Features

✅ Image upload capability
✅ Product link input
✅ Mock search results
✅ Responsive design
✅ Fast development setup

## API Endpoints

- `POST /api/search` - Search for similar items
- `GET /api/health` - Health check

## Next Steps

1. Run `./quickstart.sh`
2. Start both servers
3. Test the application
4. Integrate with real APIs
5. Deploy to production!

## License

MIT
