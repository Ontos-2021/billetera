---
applyTo: '**'
---

# Style Guidelines for MoneyFlow Mirror 💸

## Design Philosophy: Emotional Finance

Create a **delightful** and **emotionally engaging** personal finance experience that makes users **want** to manage their money. Focus on:

- **Trust & Security**: Calming blues and clean layouts to convey financial stability
- **Positive Reinforcement**: Encouraging greens for savings/income, gentle warnings for expenses
- **Accessibility**: High contrast, clear typography, and intuitive interactions
- **Joy in Use**: Subtle animations, micro-interactions, and satisfying feedback

## Technology Stack

- **Framework**: TailwindCSS (CDN or compiled)
- **Vanilla Technologies**: HTML5, CSS3, JavaScript ES6+
- **No Dependencies**: Pure JavaScript, no jQuery or heavy frameworks
- **Progressive Enhancement**: Works without JavaScript, enhanced with it

## Color Palette (Emotional Design)

```css
/* Primary Palette - Trust & Stability */
--primary: #4285f4;          /* Trustworthy blue */
--primary-light: #6ba6f6;    /* Lighter trust */
--primary-dark: #3367d6;     /* Deep confidence */

/* Success & Growth - Positive Financial Actions */
--success: #34a853;          /* Growth green */
--success-light: #81c995;    /* Light success */
--success-dark: #2d7d32;     /* Deep growth */

/* Warning & Attention - Mindful Spending */
--warning: #fbbc04;          /* Mindful amber */
--warning-light: #fdd663;    /* Gentle caution */
--warning-dark: #f29900;     /* Focused attention */

/* Expense & Alerts - Conscious Spending */
--expense: #ea4335;          /* Mindful red */
--expense-light: #f07470;    /* Gentle expense */
--expense-dark: #d23025;     /* Important alert */

/* Neutrals - Clean & Professional */
--gray-50: #f8fafc;          /* Background wash */
--gray-100: #f1f5f9;         /* Card backgrounds */
--gray-200: #e2e8f0;         /* Borders */
--gray-500: #64748b;         /* Secondary text */
--gray-900: #0f172a;         /* Primary text */
```

## Typography Scale

```css
/* Font Families */
--font-main: 'Inter', system-ui, sans-serif;
--font-numbers: 'SF Mono', 'JetBrains Mono', monospace;

/* Scales */
--text-xs: 0.75rem;      /* 12px - Labels */
--text-sm: 0.875rem;     /* 14px - Secondary */
--text-base: 1rem;       /* 16px - Body */
--text-lg: 1.125rem;     /* 18px - Emphasis */
--text-xl: 1.25rem;      /* 20px - Small headers */
--text-2xl: 1.5rem;      /* 24px - Headers */
--text-3xl: 1.875rem;    /* 30px - Large numbers */
--text-4xl: 2.25rem;     /* 36px - Hero numbers */
```

## Component Patterns

### Cards (Primary Content Containers)
```html
<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
  <h3 class="text-lg font-semibold text-gray-900 mb-4">Card Title</h3>
  <!-- Content -->
</div>
```

### Financial Numbers (Emotional Context)
```html
<!-- Income/Positive -->
<span class="text-2xl font-mono font-bold text-success">+$1,250.00</span>

<!-- Expense/Spending -->
<span class="text-2xl font-mono font-bold text-expense">-$89.50</span>

<!-- Balance/Neutral -->
<span class="text-3xl font-mono font-bold text-primary">$3,428.75</span>
```

### Buttons (Action Hierarchy)
```html
<!-- Primary Action -->
<button class="bg-primary hover:bg-primary-dark text-white font-medium px-6 py-3 rounded-lg transition-colors duration-200 shadow-sm hover:shadow-md">
  Add Income
</button>

<!-- Secondary Action -->
<button class="bg-gray-100 hover:bg-gray-200 text-gray-900 font-medium px-6 py-3 rounded-lg transition-colors duration-200">
  View Details
</button>

<!-- Expense Action -->
<button class="bg-expense hover:bg-expense-dark text-white font-medium px-6 py-3 rounded-lg transition-colors duration-200">
  Record Expense
</button>
```

### Forms (Trust & Clarity)
```html
<div class="space-y-4">
  <div>
    <label class="block text-sm font-medium text-gray-900 mb-2">Amount</label>
    <input type="number" 
           class="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-primary focus:border-primary transition-colors duration-200 font-mono text-lg"
           placeholder="0.00">
  </div>
</div>
```

## Responsive Design Principles

### Mobile-First Approach
```css
/* Base styles (mobile) */
.container { padding: 1rem; }
.card { padding: 1rem; }
.text-hero { font-size: 1.5rem; }

/* Tablet (md: 768px+) */
@media (min-width: 768px) {
  .container { padding: 1.5rem; }
  .card { padding: 1.5rem; }
  .text-hero { font-size: 2rem; }
}

/* Desktop (lg: 1024px+) */
@media (min-width: 1024px) {
  .container { padding: 2rem; }
  .card { padding: 2rem; }
  .text-hero { font-size: 2.5rem; }
}
```

### Breakpoint Strategy
- **Mobile**: 320px-767px (Primary experience)
- **Tablet**: 768px-1023px (Enhanced layout)
- **Desktop**: 1024px+ (Full features)

## Animation & Interaction Guidelines

### Micro-interactions (Emotional Feedback)
```css
/* Hover States */
.interactive {
  transition: all 200ms ease-out;
}

.interactive:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Success Feedback */
.success-pulse {
  animation: pulse-success 600ms ease-out;
}

@keyframes pulse-success {
  0% { box-shadow: 0 0 0 0 rgba(52, 168, 83, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(52, 168, 83, 0); }
  100% { box-shadow: 0 0 0 0 rgba(52, 168, 83, 0); }
}
```

### Loading States
```html
<div class="animate-pulse bg-gray-200 h-4 rounded"></div>
```

## Accessibility Requirements

- **Color Contrast**: WCAG AA (4.5:1 minimum)
- **Focus Indicators**: Visible 2px outlines
- **Touch Targets**: Minimum 44px for mobile
- **Screen Readers**: Proper ARIA labels
- **Keyboard Navigation**: Full functionality

## File Organization

```
static/
├── css/
│   ├── tailwind.css          # TailwindCSS base
│   ├── components.css        # Custom components
│   └── themes/
│       ├── default.css       # Main theme
│       └── dark.css          # Dark mode (future)
├── js/
│   ├── main.js              # Core interactions
│   ├── forms.js             # Form enhancements
│   └── animations.js        # Micro-interactions
└── icons/                   # SVG icons
```

## TailwindCSS Integration

### CDN Setup (Quick Start)
```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          primary: '#4285f4',
          success: '#34a853',
          warning: '#fbbc04',
          expense: '#ea4335'
        }
      }
    }
  }
</script>
```

### Build Process (Production)
1. Install: `npm install -D tailwindcss`
2. Config: `tailwind.config.js`
3. Build: `npx tailwindcss -i ./input.css -o ./output.css --watch`

## Implementation Guidelines

1. **Start Mobile**: Design every component for mobile first
2. **Emotional Hierarchy**: Use color psychology for financial actions
3. **Performance**: Optimize for fast loading (finances are urgent)
4. **Progressive Enhancement**: Core functionality works without JavaScript
5. **User Testing**: Test with real expense/income scenarios

## Example Implementation

```html
<!-- Expense Card with Emotional Design -->
<div class="bg-white rounded-xl p-6 border-l-4 border-expense shadow-sm hover:shadow-md transition-shadow duration-200">
  <div class="flex items-center justify-between">
    <div>
      <h3 class="font-medium text-gray-900">Grocery Shopping</h3>
      <p class="text-sm text-gray-500">Today • Food & Dining</p>
    </div>
    <span class="text-xl font-mono font-bold text-expense">-$67.32</span>
  </div>
</div>
```

Remember: Every design decision should make managing finances feel **empowering**, not overwhelming.