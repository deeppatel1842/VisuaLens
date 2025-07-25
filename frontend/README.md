# VisuaLens Frontend

Modern, responsive web interface for the VisuaLens Visual Question Answering system.

## Features

- **Drag & Drop Image Upload**: Intuitive image upload with drag-and-drop support
- **Real-time Question Input**: Live character counting and validation
- **Quick Question Templates**: Pre-defined questions for common use cases
- **Session History Management**: Track and export question history
- **Responsive Design**: Works seamlessly on mobile, tablet, and desktop
- **Dark Mode Support**: Automatic dark mode based on system preferences
- **Progressive Web App**: Offline capabilities and app-like experience
- **Advanced Options**: Detailed analysis settings and configuration

## 🏗️ Architecture

### File Structure

```
frontend/
├── index.html              # Main application page
├── test.html              # Frontend testing suite
├── css/
│   ├── reset.css          # CSS reset and base styles
│   ├── main.css           # Main styles and CSS custom properties
│   ├── components.css     # Component-specific styles
│   └── responsive.css     # Responsive design and media queries
├── js/
│   ├── app.js            # Main application logic
│   └── utils.js          # Utility functions and helpers
└── assets/               # Static assets (icons, images, etc.)
```

### Technology Stack

- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern CSS with custom properties, Grid, and Flexbox
- **Vanilla JavaScript**: No frameworks - pure ES6+ JavaScript
- **Web APIs**: File API, Fetch API, Local Storage, Clipboard API

## 🎨 Design System

### CSS Custom Properties (Variables)

The design system uses CSS custom properties for consistent theming:

```css
:root {
    /* Colors */
    --primary-color: #3b82f6;
    --primary-hover: #2563eb;
    --primary-light: rgba(59, 130, 246, 0.1);
    
    /* Typography */
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    
    /* Spacing */
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-4: 1rem;
    --space-8: 2rem;
    
    /* Layout */
    --z-dropdown: 1000;
    --z-sticky: 1020;
    --z-popover: 1030;
    --z-modal: 1040;
}
```

### Responsive Breakpoints

- **Mobile**: `< 768px`
- **Tablet**: `768px - 1023px`
- **Desktop**: `≥ 1024px`
- **Large Desktop**: `≥ 1280px`

## Getting Started

### Prerequisites

- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Local web server (for testing)
- VisuaLens Backend API running on `http://localhost:8000`

### Development Setup

1. **Start a local web server**:
   ```bash
   # Using Python
   python -m http.server 3000
   
   # Using Node.js
   npx http-server -p 3000
   
   # Using Live Server (VS Code extension)
   # Right-click index.html → "Open with Live Server"
   ```

2. **Open the application**:
   - Navigate to `http://localhost:3000`
   - Or open `test.html` for component testing

3. **Ensure backend is running**:
   - The backend API should be running on `http://localhost:8000`
   - The frontend will show connection status

### Testing

Open `test.html` to access the frontend testing suite:

- **Component Tests**: Verify all UI components load correctly
- **Responsive Tests**: Test different screen sizes
- **Integration Tests**: Check API communication

## 🔧 Configuration

### API Endpoint

The default API endpoint is configured in `js/app.js`:

```javascript
constructor() {
    this.apiBaseUrl = 'http://localhost:8000';
    // ... other configuration
}
```

### Advanced Features

- **Session Management**: Automatically saves question history
- **Image Optimization**: Client-side image resizing and compression
- **Error Handling**: Comprehensive error handling with user notifications
- **Performance Monitoring**: Built-in performance tracking

## 📱 Mobile Experience

The frontend is optimized for mobile devices:

- **Touch-friendly**: Large touch targets and intuitive gestures
- **Responsive Images**: Automatic image resizing for mobile
- **Offline Support**: Basic offline functionality with service workers
- **PWA Features**: Install as app on mobile devices

## 🎯 Component Guide

### Upload Zone

Drag-and-drop image upload with preview:

```javascript
// Handle file upload
handleImageFile(file) {
    // Validate file type and size
    // Display preview
    // Update UI state
}
```

### Question Input

Smart question input with validation:

- Character counter (500 character limit)
- Quick question templates
- Keyboard shortcuts (Ctrl+Enter to submit)

### Answer Display

Rich answer presentation:

- Formatted text display
- Response metadata (model, timing)
- Action buttons (copy, share, export)

### History Management

Session-based history tracking:

- Local storage persistence
- Export functionality
- Search and filter capabilities

## 🔒 Security

### Client-side Security

- **Input Validation**: All user inputs are validated
- **File Type Checking**: Only allowed image formats
- **Size Limits**: Maximum file size enforcement
- **XSS Prevention**: Proper output escaping

### Privacy

- **Local Storage**: Session data stays on device
- **No Tracking**: No external analytics or tracking
- **HTTPS Ready**: Designed for secure connections

## Performance

### Optimization Techniques

- **CSS Organization**: Modular CSS with component isolation
- **JavaScript Modules**: Clean separation of concerns
- **Image Optimization**: Client-side compression
- **Lazy Loading**: Progressive enhancement

### Metrics

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Bundle Size**: < 100KB (uncompressed)

## 🌐 Browser Support

### Minimum Versions

- Chrome 90+ (April 2021)
- Firefox 88+ (April 2021)
- Safari 14+ (September 2020)
- Edge 90+ (April 2021)

### Progressive Enhancement

- Graceful degradation for older browsers
- Feature detection for modern APIs
- Fallbacks for unsupported features

## 🛠️ Development

### Code Style

- **ES6+**: Modern JavaScript features
- **Semantic HTML**: Accessible markup
- **BEM CSS**: Block Element Modifier naming
- **Mobile-first**: Responsive design approach

### Adding New Features

1. Update HTML structure in `index.html`
2. Add styles in appropriate CSS file
3. Implement JavaScript functionality
4. Test across devices and browsers
5. Update documentation

## 📋 API Integration

### Backend Communication

The frontend communicates with the backend via REST API:

```javascript
// Ask question endpoint
POST /ask
Content-Type: multipart/form-data
{
    image: File,
    question: string,
    session_id: string,
    detailed_analysis?: boolean
}

// Health check
GET /health
```

### Error Handling

Comprehensive error handling for API failures:

- Network errors
- Server errors (5xx)
- Validation errors (4xx)
- Timeout handling

## 🎨 Customization

### Theming

Customize the appearance by modifying CSS custom properties:

```css
:root {
    --primary-color: #your-color;
    --font-family-primary: 'Your Font', sans-serif;
}
```

### Layout

Adjust layout by modifying the main container grid:

```css
.main-container {
    grid-template-columns: 350px 1fr 320px;
    /* Adjust column sizes */
}
```

## 📚 Resources

- [CSS Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [JavaScript File API](https://developer.mozilla.org/en-US/docs/Web/API/File)
- [Web Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## 🐛 Troubleshooting

### Common Issues

1. **Images not uploading**:
   - Check file size (< 10MB)
   - Verify file type (JPEG, PNG, GIF, BMP, WebP)
   - Ensure backend is running

2. **API connection failed**:
   - Verify backend URL (`http://localhost:8000`)
   - Check CORS configuration
   - Confirm network connectivity

3. **Styles not loading**:
   - Clear browser cache
   - Check console for CSS errors
   - Verify file paths

4. **Mobile layout issues**:
   - Test in device mode
   - Check viewport meta tag
   - Verify responsive CSS

## 📄 License

Part of the VisuaLens project. See main project README for license information.

---

**VisuaLens Frontend** - Built with ❤️ for the future of visual AI interaction.
