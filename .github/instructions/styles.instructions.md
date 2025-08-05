# 🎨 MoneyFlow Mirror - Guía de Estilos para Agentes de IA

## 📋 Arquitectura de Estilos

**Framework Principal**: TailwindCSS (CDN) con configuración personalizada en `base.html`
**CSS Legacy**: Bootstrap/CSS personalizado en `/static/css/` para compatibilidad
**Fonts**: Inter (UI), JetBrains Mono (números financieros)

## 🎯 Paleta de Colores Financiera

```javascript
// Configuración TailwindCSS (base.html)
colors: {
    primary: '#4285f4',           // Azul confianza
    'primary-light': '#6ba6f6',
    'primary-dark': '#3367d6',
    success: '#34a853',           // Verde ingresos
    'success-light': '#81c995',
    'success-dark': '#2d7d32',
    expense: '#ea4335',           // Rojo gastos
    'expense-light': '#f07470',
    'expense-dark': '#d23025',
    warning: '#fbbc04',           // Amarillo precaución
}
```

## 🧱 Patrones de Componentes Obligatorios

### **Tarjetas Financieras** (Principal UX Pattern)
```html
<!-- ✅ USAR SIEMPRE este patrón -->
<div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200 card-hover">
    <div class="flex items-center justify-between">
        <div>
            <p class="text-sm font-medium text-success-dark mb-1">💰 Etiqueta</p>
            <p class="text-3xl font-numbers font-bold text-success">+$1,234.56</p>
            <p class="text-xs text-gray-500 mt-1">ARS</p>
        </div>
        <div class="w-12 h-12 bg-success-light bg-opacity-20 rounded-full flex items-center justify-center">
            <span class="text-2xl">📈</span>
        </div>
    </div>
</div>
```

### **Botones de Acción Rápida** (Dashboard Pattern)
```html
<!-- ✅ Gradientes empoderadoras para acciones principales -->
<a href="#" class="group bg-gradient-to-br from-expense to-expense-dark hover:from-expense-dark hover:to-expense text-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
    <div class="flex flex-col items-center text-center">
        <div class="w-16 h-16 bg-white bg-opacity-20 rounded-full flex items-center justify-center mb-4 group-hover:bg-opacity-30">
            <span class="text-3xl">💸</span>
        </div>
        <h3 class="text-xl font-bold mb-2">Acción Principal</h3>
        <p class="text-expense-light opacity-90">Descripción motivadora</p>
    </div>
</a>
```

### **Navegación con Enlaces "Ver todos"**
```html
<!-- ✅ Incluir SIEMPRE iconos SVG en enlaces de navegación -->
<a href="#" class="flex items-center text-white hover:text-gray-200 text-sm font-medium transition-colors duration-200">
    Ver todos
    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
    </svg>
</a>
```

## 💰 Tipografía Financiera OBLIGATORIA

### **Números y Montos**
```html
<!-- ✅ SIEMPRE usar font-numbers para montos -->
<p class="text-3xl font-numbers font-bold text-success">+${{ amount|floatformat:2 }}</p>

<!-- ✅ Clase financiera para montos menores -->
<p class="font-numbers font-bold text-expense">-$123.45</p>
```

### **Jerarquía de Texto**
- **Headers**: `text-4xl font-bold` (Bienvenidas), `text-2xl font-bold` (Secciones)
- **Descripción**: `text-xl text-gray-600` (Subtítulos)
- **Labels**: `text-sm font-medium text-{color}-dark`
- **Metadata**: `text-xs text-gray-500`

## 📱 Mobile-First Responsive (CRÍTICO)

### **Grids Responsivos Estándar**
```html
<!-- ✅ Patrón principal para dashboards -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">  <!-- Resúmenes -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">       <!-- Transacciones -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">  <!-- Acciones -->
```

### **Espaciado Mobile**
- **Secciones**: `mb-8` (desktop), reducir a `mb-6` en mobile si es necesario
- **Cards**: `p-6` (desktop), `p-4` (mobile automático con responsive)
- **Contenedores**: `max-w-2xl mx-auto` para acciones, `max-w-4xl mx-auto` para landing

## 🎭 Estados Emocionales y UX

### **Estados de Balance** (Lógica condicional OBLIGATORIA)
```html
<!-- ✅ SIEMPRE implementar lógica condicional para balance -->
{% if balance_neto > 0 %}
    <p class="text-3xl font-numbers font-bold text-success">+${{ balance_neto }}</p>
    <p class="text-xs text-success-dark mt-1">Balance positivo 📈</p>
{% elif balance_neto < 0 %}
    <p class="text-3xl font-numbers font-bold text-expense">${{ balance_neto }}</p>
    <p class="text-xs text-expense-dark mt-1">Balance negativo 📉</p>
{% else %}
    <p class="text-3xl font-numbers font-bold text-primary">${{ balance_neto }}</p>
    <p class="text-xs text-primary-dark mt-1">Balance equilibrado ⚖️</p>
{% endif %}
```

### **Animaciones de Interacción**
- **Cards**: `hover:shadow-md transition-shadow duration-200 card-hover`
- **Botones**: `transition-all duration-300 transform hover:scale-105`
- **Enlaces**: `transition-colors duration-200`

## 🚫 Anti-Patterns (NO hacer)

- ❌ NO usar Bootstrap grid (`container`, `row`, `col-*`)
- ❌ NO usar colores hard-coded (#hex), usar siempre variables de Tailwind
- ❌ NO omitir `font-numbers` en montos financieros
- ❌ NO crear tarjetas sin hover effects
- ❌ NO usar iconos de texto sin emojis en contexto financiero
- ❌ NO duplicar secciones de perfil o navegación

## 🔄 Optimización UX Crítica

### **Orden de Información (Dashboard)**
1. **Bienvenida** - `text-center mb-8`
2. **Acciones Rápidas** - Gradientes con `transform hover:scale-105`
3. **Resúmenes Financieros** - Grid de 3 columnas con lógica condicional
4. **Transacciones Recientes** - Grid 2 columnas con "Ver todos"
5. **Perfil** - Al final, `mt-6`

### **Estados Vacíos Empáticos**
```html
<!-- ✅ Mensajes motivadores para estados vacíos -->
<div class="p-8 text-center text-gray-500">
    <span class="text-4xl mb-4 block">📝</span>
    <p>No hay gastos registrados</p>
</div>
```

## 📐 Template Structure
- **Base**: TailwindCSS config en `base.html` con `font-main`, `font-numbers`
- **Pages**: Extender de `base.html`, usar `{% block content %}`
- **Static**: Legacy CSS en `/static/css/` solo para componentes específicos

**Prioridad**: TailwindCSS > CSS personalizado > Bootstrap legacy
