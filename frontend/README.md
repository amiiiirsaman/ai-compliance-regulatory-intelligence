# Compliance & Regulatory Intelligence System - Frontend

Modern React + TypeScript frontend for the AI-powered compliance review system.

## Features

- 🎨 **Sleek Modern Design** - Clean UI with Tailwind CSS, Lucide icons, and Framer Motion animations
- 🔐 **Authentication** - JWT-based auth with access/refresh tokens
- 📤 **Document Upload** - Drag & drop file upload with progress tracking
- 📊 **Real-time Updates** - WebSocket integration for live review progress
- 📋 **Review Management** - Comprehensive review listing and detail views
- 🔍 **Violation Analysis** - Detailed violation cards with severity indicators
- ⚡ **Bedrock Logs** - View all AWS Bedrock API calls and token usage

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **Redux Toolkit** - State management
- **React Router v6** - Client-side routing
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Beautiful icons
- **Framer Motion** - Smooth animations
- **React Hot Toast** - Toast notifications
- **React Dropzone** - File upload

## Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```
   
   The app will be available at http://localhost:5173

3. **Build for production:**
   ```bash
   npm run build
   ```

## Project Structure

```
src/
├── components/          # Reusable components
│   └── Layout.tsx       # Main layout with sidebar
├── lib/                 # Utilities & services
│   ├── api.ts           # Axios instance with auth
│   ├── websocket.ts     # WebSocket hook
│   └── utils.ts         # Helper functions
├── pages/               # Page components
│   ├── Login.tsx        # Login form
│   ├── Register.tsx     # Registration form
│   ├── Dashboard.tsx    # Overview dashboard
│   ├── Upload.tsx       # Document upload
│   ├── ReviewList.tsx   # All reviews
│   └── ReviewDetail.tsx # Review details & violations
├── store/               # Redux store
│   ├── index.ts         # Store config
│   └── slices/          # Redux slices
│       ├── authSlice.ts
│       ├── documentsSlice.ts
│       └── reviewsSlice.ts
├── types/               # TypeScript types
│   └── index.ts
├── App.tsx              # Routes & app setup
├── main.tsx             # Entry point
└── index.css            # Tailwind & custom styles
```

## Environment

The app proxies API requests to `http://localhost:8000` in development. Make sure the backend is running.

## Design System

### Colors
- **Primary:** Navy blue (#1e3a8a)
- **Accent:** Gold (#d97706)
- **Compliant:** Green (#059669)
- **Violations:** Red → Amber scale by severity

### Typography
- **Headings:** Merriweather (serif)
- **Body:** Inter (sans-serif)
- **Code:** JetBrains Mono (monospace)
