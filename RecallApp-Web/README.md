# Recall Web - Memory Search Web App

A web-based version of the Recall memory search system that can be accessed from any device, including iPhone. Built with Next.js and deployable to Vercel.

## 🌐 Live Demo

Deploy this to Vercel and access from any device with a web browser.

## 🚀 Features

- **Search**: Natural language search across your memory timeline
- **Timeline View**: Browse activities chronologically
- **Recent Activities**: See what you've been doing in the last few hours
- **Statistics**: View database stats and system status
- **Mobile Optimized**: Works perfectly on iPhone and other mobile devices
- **Dark Mode**: Automatic dark mode support
- **Real-time Updates**: Auto-refresh for recent activities

## 📱 Mobile Experience

The web app is fully responsive and optimized for mobile devices:
- Touch-friendly interface
- Safe area support for iPhone notch/Dynamic Island
- Swipe gestures for navigation
- Mobile-optimized layouts
- PWA support for "Add to Home Screen"

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS
- **Data Fetching**: TanStack Query (React Query)
- **Icons**: Lucide React
- **Backend**: Python serverless functions
- **Deployment**: Vercel

## 📦 Installation

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+ (for API)
- Vercel account (free tier works)

### Local Development

1. **Clone the repository**:
```bash
git clone <repo-url>
cd RecallApp-Web
```

2. **Install dependencies**:
```bash
npm install
```

3. **Run development server**:
```bash
npm run dev
```

4. **Open in browser**:
```
http://localhost:3000
```

## 🚀 Deployment to Vercel

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/recall-web)

### Manual Deploy

1. **Install Vercel CLI**:
```bash
npm i -g vercel
```

2. **Deploy**:
```bash
vercel
```

3. **Follow prompts**:
- Select your account
- Choose project name
- Accept default settings

4. **Access your app**:
```
https://your-project.vercel.app
```

## 📱 Testing on iPhone

### Method 1: Direct URL
1. Deploy to Vercel
2. Open Safari on iPhone
3. Navigate to your Vercel URL
4. Tap Share → "Add to Home Screen"

### Method 2: Local Network (Development)
1. Find your computer's IP address:
```bash
# Mac
ipconfig getifaddr en0

# Windows
ipconfig
```

2. Run dev server:
```bash
npm run dev
```

3. On iPhone, open Safari:
```
http://YOUR_COMPUTER_IP:3000
```

## 🔧 Configuration

### Environment Variables

Create `.env.local` for local development:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# Optional: Real backend URL (if you have one)
# NEXT_PUBLIC_BACKEND_URL=https://your-backend.com
```

For production (Vercel), set these in the Vercel dashboard.

## 📁 Project Structure

```
RecallApp-Web/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Main page
│   ├── layout.tsx         # Root layout
│   ├── globals.css        # Global styles
│   └── providers.tsx      # React Query provider
├── components/            # React components
│   ├── SearchSection.tsx  # Search interface
│   ├── TimelineView.tsx   # Timeline browser
│   ├── RecentActivities.tsx # Recent events
│   └── StatsPanel.tsx     # Statistics
├── api/                   # Serverless functions
│   └── index.py          # Python API endpoint
├── public/               # Static assets
├── package.json          # Dependencies
├── vercel.json          # Vercel configuration
└── next.config.js       # Next.js configuration
```

## 🎨 Features by Component

### SearchSection
- Natural language search input
- Source filtering (WindRecorder, Claude)
- Relevance scoring
- Tag display

### TimelineView
- Date picker
- Hour-by-hour grouping
- Expandable event details
- Quick date navigation

### RecentActivities
- Time range selector (1h, 4h, 12h, 24h)
- Auto-refresh every minute
- Relative timestamps
- Activity preview

### StatsPanel
- Total events counter
- Source breakdown chart
- Database size monitoring
- Archive status

## 🔌 API Endpoints

The Python serverless API provides:

- `GET /api/search?q=query` - Search events
- `GET /api/timeline?date=2025-08-22` - Get timeline
- `GET /api/events/recent?hours=4` - Recent activities
- `GET /api/stats` - System statistics

## 🎯 Roadmap

- [ ] Real database integration (replace demo data)
- [ ] User authentication
- [ ] WebSocket for real-time updates
- [ ] Export functionality
- [ ] Advanced filtering
- [ ] Voice search
- [ ] Offline support (PWA)
- [ ] Push notifications

## 🐛 Troubleshooting

### Common Issues

**Build fails on Vercel**:
- Check Python version in vercel.json
- Ensure all dependencies are in package.json

**API not working**:
- Check CORS settings in vercel.json
- Verify Python function syntax

**Mobile layout issues**:
- Clear browser cache
- Check viewport meta tag
- Test in Safari developer tools

## 📄 License

MIT License - see LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## 📞 Support

For issues, please open a GitHub issue or contact support.