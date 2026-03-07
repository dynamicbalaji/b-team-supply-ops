# Supply Chain AI Dashboard - Frontend

## 🚀 Project Overview

This is a React-based AI-powered supply chain management dashboard that demonstrates real-time crisis management and automated agent decision-making. The application simulates a port strike scenario affecting Apple's supply chain, showcasing how AI agents collaborate to find optimal solutions.

### Key Features
- 🗺️ **Interactive Canvas Map** - Real-time visualization of supply routes and logistics
- 🤖 **AI Agent Network** - Collaborative agents for logistics, finance, procurement, and sales
- 💬 **A2A (Agent-to-Agent) Communication** - Real-time negotiation between AI agents
- 📊 **Decision Matrix** - Dynamic what-if analysis and scenario planning
- 🎯 **Crisis Management** - Automated response to supply chain disruptions
- 📈 **Cost Tracking** - Real-time cost accumulation and savings calculation

## 🛠️ Tech Stack

### Core Technologies
- **React**: `19.2.0` - Modern React with latest features
- **Vite**: `7.3.1` - Lightning-fast build tool and dev server
- **Tailwind CSS**: `3.4.19` - Utility-first CSS framework for styling

### State Management & UI
- **Zustand**: `5.0.11` - Lightweight state management


### Development Tools
- **ESLint**: `9.39.1` - Code linting and quality
- **PostCSS**: `8.5.8` - CSS processing
- **Autoprefixer**: `10.4.27` - CSS vendor prefixing

## 📦 Installation & Setup

### Prerequisites
- Node.js (v18 or higher recommended)
- npm or yarn package manager

### Quick Start

1. **Clone and navigate to the project**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   Navigate to `http://localhost:5173`

### Available Scripts
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run lint     # Run ESLint
npm run preview  # Preview production build
```

## 📁 Folder Structure

```
src/
├── components/           # React components
│   ├── Navigation/       # Top navigation bar
│   ├── CrisisBanner/     # Crisis alert banner
│   ├── MainContent/      # Main content container
│   ├── BottomBar/        # Bottom metrics bar
│   ├── SidePanel/        # Right sidebar components
│   │   ├── AgentNetwork.jsx  # AI agent cards
│   │   └── Chat.jsx          # A2A communication log
│   └── Tabs/             # Main content tabs
│       ├── MapTab/       # Interactive map view
│       ├── SplitTab/     # Traditional vs AI comparison
│       ├── DecisionTab/  # Decision matrix
│       └── AuditTab/     # Audit trail
├── data/
│   └── mockData.js       # Sample data and scenarios
├── hooks/
│   └── useScenarioEngine.js  # Scenario automation logic
├── store/
│   └── useAppStore.js    # Zustand state management
├── styles/
│   └── index.css         # Global styles and Tailwind config
└── App.jsx               # Main application component
```

## 🎮 Features & Components

### 1. Interactive Map (`MapTab`)
- **Canvas-based rendering** for smooth animations
- **Real-time route visualization** with animated trucks
- **Node status indicators** (blocked, active, delivered)
- **Dynamic phase tracking** with progress indicators

### 2. AI Agent Network (`AgentNetwork`)
- **4 Specialized Agents**: Logistics, Finance, Procurement, Sales
- **Real-time confidence levels** with animated progress bars
- **Status tracking** (Processing, Online, Analyzing, etc.)
- **Collapsible interface** with smooth animations

### 3. A2A Communication (`Chat`)
- **Real-time message stream** between AI agents
- **Color-coded messages** by agent type
- **Auto-scrolling** with custom scrollbars
- **Human approval workflow** for critical decisions

### 4. Crisis Management
- **Real-time cost tracking** with accumulating ticker
- **Scenario engine** with 16-step automation
- **Risk assessment** with devil's advocate agent
- **Performance metrics** comparing AI vs traditional approaches

## 🎨 Styling & Design

### Design System
- **Dark theme** with professional blue/cyan accents
- **Custom color palette** defined in CSS variables
- **Typography**: Syne font for headings, JetBrains Mono for code/data
- **Responsive grid layouts** with Tailwind CSS

### Custom Animations
- **Smooth transitions** for all interactive elements
- **Pulsing indicators** for active agents
- **Sliding animations** for crisis alerts
- **Canvas animations** for map elements

### Accessibility
- **Proper contrast ratios** for all text elements
- **Focus indicators** for keyboard navigation
- **Screen reader friendly** with semantic HTML
- **Responsive design** for various screen sizes

## 🔄 State Management

### Zustand Store (`useAppStore`)
The application uses Zustand for centralized state management:

```javascript
// Key state slices:
- agents: AI agent status and data
- messages: A2A communication log
- phases: Scenario execution phases
- mapStatus: Current map and route status
- costs: Real-time cost tracking
- scenarios: Demo scenario configurations
```

### State Features
- **Reactive updates** across all components
- **Persistent state** during scenario execution
- **Optimistic updates** for smooth UX
- **Action creators** for complex state changes

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

### Environment Configuration
- Development: `http://localhost:5173`
- Production: Configure your hosting service

### Build Optimization
- **Tree shaking** for minimal bundle size
- **Code splitting** for faster loading
- **Asset optimization** with Vite
- **Modern ES modules** for better performance

## 🔮 TODO & Future Enhancements

### 🚧 Pending Implementation
- [ ] **API Integration** - Connect to real backend services
- [ ] **WebSocket Support** - Real-time data streaming
- [ ] **Authentication** - User login and role management
- [ ] **Data Persistence** - Save scenarios and configurations
- [ ] **Export Features** - PDF reports and data export

### 🎯 Planned Features
- [ ] **Multiple Scenarios** - Additional crisis types
- [ ] **Historical Data** - Past scenario analytics
- [ ] **Custom Agents** - User-configurable AI agents
- [ ] **Advanced Metrics** - Detailed performance analytics
- [ ] **Multi-language** - Internationalization support

### 🐛 Known Issues
- [ ] Canvas rendering performance on large datasets
- [ ] Mobile responsiveness needs optimization
- [ ] Accessibility improvements for screen readers

## 🤝 Contributing

### Development Guidelines
1. Follow the existing code style and component patterns
2. Use TypeScript for new features (migration in progress)
3. Ensure responsive design for all new components
4. Add proper error handling and loading states
5. Include comprehensive testing for new features

### Code Style
- Use functional components with hooks
- Implement proper prop types validation
- Follow Tailwind CSS utility patterns
- Use semantic HTML elements
- Maintain consistent naming conventions

## 📝 License & Credits

This project was developed for the 2026 Supply Chain AI Hackathon, demonstrating the power of AI-driven decision making in crisis management scenarios.

### Technologies Used
- React ecosystem for robust UI development
- Canvas API for high-performance map rendering
- Modern CSS with Tailwind for rapid styling
- Zustand for lightweight state management

---

**Last Updated**: March 6, 2026
**Version**: 1.0.0
**Status**: Development Phase - API Integration Pending
