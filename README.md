# AI Stock Dashboard

![AI Stock Dashboard](https://github.com/user-attachments/assets/fbc8df49-1522-4774-ac38-5da6aa2379d6)

AI-powered website that periodically analyzes stocks, runs AI queries to generate metrics, and displays a dashboard of the top-performing stocks.

## 🚀 Features

- **Real-time Stock Analysis**: Fetches stock data from Alpha Vantage API with mock data fallback
- **AI-Powered Scoring**: Uses OpenAI GPT to analyze stocks and provide investment scores (0-100)
- **Periodic Updates**: Automatically refreshes stock data and analysis every 30 minutes
- **Beautiful Dashboard**: Modern, responsive UI with gradient backgrounds and interactive cards
- **Ranking System**: Stocks are sorted by AI analysis scores with visual ranking badges
- **Detailed Metrics**: Shows price changes, volume, market cap, and AI reasoning
- **Works Out-of-the-Box**: Uses mock data when API keys are not available

## 🛠 Tech Stack

### Backend
- **Python 3.8+** with FastAPI
- **uvicorn** for ASGI server
- **alpha-vantage** for stock data
- **OpenAI API** for AI analysis
- **APScheduler** for periodic tasks
- **Pydantic** for data validation

### Frontend
- **React 18** with Vite
- **Axios** for API communication
- **Lucide React** for icons
- **CSS3** with modern styling

### Storage
- **In-memory** storage for MVP (easily upgradeable to databases)

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/citylife4/ai-stock-dashboard.git
   cd ai-stock-dashboard
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment (optional)**
   ```bash
   cp .env.example .env
   # Edit .env file to add your OpenAI API key (optional - works with mock data)
   ```

4. **Set up the frontend**
   ```bash
   cd ../frontend
   npm install
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   python -m app.main
   ```
   Backend will be available at `http://localhost:8000`

2. **Start the frontend (in a new terminal)**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will be available at `http://localhost:5173`

3. **Open your browser** and navigate to `http://localhost:5173`

## 📊 API Endpoints

- `GET /api/v1/dashboard` - Get current stock analysis dashboard
- `POST /api/v1/refresh` - Force refresh of stock analysis
- `GET /api/v1/status` - Get service status and configuration
- `GET /api/v1/stocks/{symbol}` - Get analysis for specific stock

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# OpenAI API Key (optional - will use mock data if not provided)
OPENAI_API_KEY=your_openai_api_key_here

# Alpha Vantage API Key (required for stock data)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Server configuration
HOST=localhost
PORT=8000
DEBUG=true
```

### Stock Symbols

The application analyzes these stocks by default (configurable in `backend/app/config.py`):
- AAPL (Apple Inc.)
- GOOGL (Alphabet Inc.)
- MSFT (Microsoft Corporation)
- TSLA (Tesla Inc.)
- AMZN (Amazon.com Inc.)
- NVDA (NVIDIA Corporation)
- META (Meta Platforms Inc.)
- NFLX (Netflix Inc.)

### Update Frequency

Stock analysis updates every 30 minutes by default. This can be changed in `backend/app/config.py`:

```python
UPDATE_INTERVAL = 30  # Update every 30 minutes
```

## 🎯 How It Works

1. **Stock Data Fetching**: The application fetches real-time stock data using Alpha Vantage API
2. **AI Analysis**: Each stock is analyzed using OpenAI GPT with a structured prompt
3. **Scoring System**: AI provides scores (0-100) based on various factors:
   - Recent price performance
   - Trading volume
   - Market capitalization
   - Sector sentiment
4. **Ranking**: Stocks are sorted by AI scores and displayed with rankings
5. **Auto-Update**: The system automatically refreshes data every 30 minutes
6. **Fallback System**: When APIs are unavailable, realistic mock data is used

## 🔧 Development

### Project Structure

```
ai-stock-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration settings
│   │   ├── models.py            # Pydantic data models
│   │   ├── api/
│   │   │   └── routes.py        # API route handlers
│   │   └── services/
│   │       ├── stock_service.py # Stock data fetching
│   │       ├── ai_service.py    # AI analysis
│   │       └── scheduler.py     # Background tasks
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── StockCard.jsx    # Individual stock card
│   │   │   └── StockCard.css
│   │   ├── services/
│   │   │   └── api.js           # API communication
│   │   ├── App.jsx              # Main application
│   │   └── App.css
│   └── package.json
└── README.md
```

### Adding New Features

1. **New Stock Symbols**: Add to `STOCK_SYMBOLS` in `config.py`
2. **Different AI Models**: Modify `ai_service.py` to use different models
3. **Database Storage**: Replace in-memory storage in `scheduler.py`
4. **Additional Metrics**: Extend the `StockData` model in `models.py`

## 🚀 Production Deployment

### Docker (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### Manual Deployment

1. **Backend**: Deploy using uvicorn with multiple workers
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

2. **Frontend**: Build and serve static files
   ```bash
   npm run build
   # Serve the dist/ folder with nginx or any static file server
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Yahoo Finance](https://finance.yahoo.com/) for stock data
- [OpenAI](https://openai.com/) for AI analysis capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [React](https://reactjs.org/) for the frontend framework
- [Lucide](https://lucide.dev/) for beautiful icons