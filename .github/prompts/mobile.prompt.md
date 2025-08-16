# Objetivo

Crear en el **mismo repo** una app móvil **Expo (React Native + TypeScript)** dentro de **/mobile**, conectada al backend Django, enfocada **solo** en **CRUD de Ingresos y Egresos** (sin grupos, sin pagos). Debe funcionar en iPhone vía **Expo Go** y en Android Emulator.

> **Política de endpoints**: *si no existen los endpoints suficientes y necesarios en el backend, el agente debe crearlos junto con la implementación*. Mínimo requerido: `GET /health/` y el recurso REST ` /api/transactions/` (listar, crear, obtener, actualizar, borrar).

---

## Supuestos y condiciones

* El repo ya contiene un proyecto Django con `manage.py` en la raíz o en `/backend`.
* SO: **Windows**. Pruebas iniciales en **iPhone** con Expo Go (misma Wi‑Fi que la PC) y opcional en **Android Emulator**.
* No romper nada existente: si `/mobile` ya existe, **no** sobreescribir, solo agregar/actualizar archivos faltantes.
* Desarrollo sin cuentas pagas de Apple/Google.

---

## Tareas del agente (idempotentes)

### 0) Detección de estructura

1. Si existe `backend/` con `manage.py`, usar `backend/` como raíz del backend; si no, asumir repo root.
2. Comprobar Node >= 18 (`node -v`). Si no se cumple, **documentar** requisito, continuar creando archivos igualmente.

### 1) Crear carpeta `/mobile` con Expo + TS

* Si **no existe** `/mobile`:

  ```bash
  mkdir -p mobile && cd mobile
  npx create-expo-app@latest . -t expo-template-blank-typescript
  ```
* Si **existe**, verificar `app.json` o `app.config.(js|ts)` y `package.json`. Si faltan, crearlos (ver abajo).

### 2) Dependencias mínimas (managed workflow)

Dentro de `/mobile`:

```bash
npx expo install expo-router react-native-safe-area-context react-native-screens
npx expo install expo-constants expo-linking
npx expo install @react-native-async-storage/async-storage
npm i -D @types/react @types/react-native
```

> Evitar libs que requieran `prebuild` en este primer commit.

### 3) Estructura de archivos (Expo Router)

Crear/actualizar:

```
/mobile
  app/
    _layout.tsx
    index.tsx          # Home / Resumen
    transactions.tsx   # Listado
    add-transaction.tsx
    edit-transaction.tsx
  src/
    lib/
      api.ts
      storage.ts
    types/
      index.ts
  app.config.ts
  .env.example
  .gitignore
```

#### 3.1) `app/_layout.tsx`

```tsx
import { Stack } from 'expo-router';
export default function Layout() {
  return <Stack screenOptions={{ headerShown: true }} />;
}
```

#### 3.2) `app/index.tsx` (Home/Resumen)

```tsx
import { Link } from 'expo-router';
import { View, Text } from 'react-native';
import { getTotals } from '../src/lib/storage';
import { useEffect, useState } from 'react';

export default function Home() {
  const [totals, setTotals] = useState({ ingresos: 0, egresos: 0, balance: 0 });
  useEffect(() => { getTotals().then(setTotals); }, []);

  return (
    <View style={{ padding: 16, gap: 10 }}>
      <Text style={{ fontSize: 22, fontWeight: '700' }}>Resumen</Text>
      <Text>Ingresos: ${totals.ingresos}</Text>
      <Text>Egresos:  ${totals.egresos}</Text>
      <Text style={{ fontWeight: '700' }}>Balance:  ${totals.balance}</Text>
      <Link href="/transactions">Ver movimientos</Link>
      <Link href="/add-transaction">Agregar movimiento</Link>
    </View>
  );
}
```

#### 3.3) `app/transactions.tsx` (Listado)

```tsx
import { useEffect, useState } from 'react';
import { View, Text, FlatList, Pressable } from 'react-native';
import { Transaction } from '../src/types';
import { getTransactions } from '../src/lib/storage';
import { Link } from 'expo-router';

export default function Transactions() {
  const [items, setItems] = useState<Transaction[]>([]);
  useEffect(() => { getTransactions().then(setItems); }, []);

  return (
    <View style={{ padding: 16 }}>
      <Text style={{ fontSize: 22, fontWeight: '600' }}>Movimientos</Text>
      <FlatList
        data={items}
        keyExtractor={(t) => t.id}
        renderItem={({ item }) => (
          <Link href={{ pathname: '/edit-transaction', params: { id: item.id } }} asChild>
            <Pressable style={{ paddingVertical: 8 }}>
              <Text>
                {item.type === 'income' ? '➕' : '➖'} {item.concepto} — ${item.monto}
              </Text>
            </Pressable>
          </Link>
        )}
        ListEmptyComponent={<Text>No hay movimientos</Text>}
      />
    </View>
  );
}
```

#### 3.4) `app/add-transaction.tsx`

```tsx
import { useState } from 'react';
import { View, Text, TextInput, Button, Switch } from 'react-native';
import { addTransaction } from '../src/lib/storage';
import { router } from 'expo-router';

export default function AddTransaction() {
  const [concepto, setConcepto] = useState('');
  const [monto, setMonto] = useState('');
  const [isIncome, setIsIncome] = useState(true);

  const guardar = async () => {
    const num = Number(monto);
    if (!concepto || isNaN(num) || num <= 0) {
      alert('Completá concepto y monto (>0)');
      return;
    }
    await addTransaction({ concepto, monto: num, type: isIncome ? 'income' : 'expense' });
    router.replace('/transactions');
  };

  return (
    <View style={{ padding: 16, gap: 10 }}>
      <Text style={{ fontSize: 22, fontWeight: '600' }}>Agregar movimiento</Text>
      <TextInput placeholder="Concepto" value={concepto} onChangeText={setConcepto} style={{ borderWidth: 1, padding: 8, borderRadius: 8 }} />
      <TextInput placeholder="Monto" value={monto} onChangeText={setMonto} keyboardType="numeric" style={{ borderWidth: 1, padding: 8, borderRadius: 8 }} />
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <Text>Ingreso</Text>
        <Switch value={isIncome} onValueChange={setIsIncome} />
      </View>
      <Button title="Guardar" onPress={guardar} />
    </View>
  );
}
```

#### 3.5) `app/edit-transaction.tsx`

```tsx
import { useLocalSearchParams, router } from 'expo-router';
import { useEffect, useState } from 'react';
import { View, Text, TextInput, Button, Switch } from 'react-native';
import { getTransactionById, updateTransaction, deleteTransaction } from '../src/lib/storage';

export default function EditTransaction() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [concepto, setConcepto] = useState('');
  const [monto, setMonto] = useState('');
  const [isIncome, setIsIncome] = useState(true);

  useEffect(() => {
    if (id) {
      getTransactionById(String(id)).then(t => {
        if (!t) return;
        setConcepto(t.concepto);
        setMonto(String(t.monto));
        setIsIncome(t.type === 'income');
      });
    }
  }, [id]);

  const guardar = async () => {
    if (!id) return;
    const num = Number(monto);
    if (!concepto || isNaN(num) || num <= 0) {
      alert('Completá concepto y monto (>0)');
      return;
    }
    await updateTransaction(String(id), { concepto, monto: num, type: isIncome ? 'income' : 'expense' });
    router.back();
  };

  const borrar = async () => {
    if (!id) return;
    await deleteTransaction(String(id));
    router.replace('/transactions');
  };

  return (
    <View style={{ padding: 16, gap: 10 }}>
      <Text style={{ fontSize: 22, fontWeight: '600' }}>Editar movimiento</Text>
      <TextInput placeholder="Concepto" value={concepto} onChangeText={setConcepto} style={{ borderWidth: 1, padding: 8, borderRadius: 8 }} />
      <TextInput placeholder="Monto" value={monto} onChangeText={setMonto} keyboardType="numeric" style={{ borderWidth: 1, padding: 8, borderRadius: 8 }} />
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <Text>Ingreso</Text>
        <Switch value={isIncome} onValueChange={setIsIncome} />
      </View>
      <Button title="Guardar cambios" onPress={guardar} />
      <Button title="Eliminar" color="#b00020" onPress={borrar} />
    </View>
  );
}
```

### 4) Lógica de datos local (AsyncStorage)

#### 4.1) `src/types/index.ts`

```ts
export type TransactionType = 'income' | 'expense';
export type Transaction = {
  id: string;
  concepto: string;
  monto: number;
  type: TransactionType;
  date?: string; // ISO opcional
};
```

#### 4.2) `src/lib/storage.ts`

```ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Transaction } from '../types';

const K_TRANSACTIONS = 'transactions';

export async function getTransactions(): Promise<Transaction[]> {
  const raw = await AsyncStorage.getItem(K_TRANSACTIONS);
  const list: Transaction[] = raw ? JSON.parse(raw) : [];
  return list.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
}

export async function getTransactionById(id: string) {
  const list = await getTransactions();
  return list.find(t => t.id === id);
}

export async function addTransaction(input: { concepto: string; monto: number; type: 'income' | 'expense' }) {
  const list = await getTransactions();
  const item: Transaction = {
    id: Date.now().toString(),
    concepto: input.concepto,
    monto: input.monto,
    type: input.type,
    date: new Date().toISOString(),
  };
  list.push(item);
  await AsyncStorage.setItem(K_TRANSACTIONS, JSON.stringify(list));
  return item;
}

export async function updateTransaction(id: string, input: { concepto: string; monto: number; type: 'income' | 'expense' }) {
  const list = await getTransactions();
  const idx = list.findIndex(t => t.id === id);
  if (idx === -1) return;
  list[idx] = { ...list[idx], ...input };
  await AsyncStorage.setItem(K_TRANSACTIONS, JSON.stringify(list));
}

export async function deleteTransaction(id: string) {
  const list = await getTransactions();
  const next = list.filter(t => t.id !== id);
  await AsyncStorage.setItem(K_TRANSACTIONS, JSON.stringify(next));
}

export async function getTotals() {
  const list = await getTransactions();
  const ingresos = list.filter(t => t.type === 'income').reduce((a, t) => a + t.monto, 0);
  const egresos  = list.filter(t => t.type === 'expense').reduce((a, t) => a + t.monto, 0);
  return { ingresos, egresos, balance: ingresos - egresos };
}
```

### 5) API mínima del backend (crear si no existe)

#### 5.1) Endpoint de salud

* `GET /health/` → `{ "status": "ok" }` (ver ejemplo clásico)

#### 5.2) Recurso `transactions`

* **Modelo** en Django (app `wallet` o `core`):

```python
# models.py
from django.db import models

class Transaction(models.Model):
    TYPE_CHOICES = (('income', 'Income'), ('expense', 'Expense'))
    concepto = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

* **Serializer DRF**:

```python
# serializers.py
from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'concepto', 'monto', 'type', 'date']
```

* **ViewSet + Router**:

```python
# views.py
from rest_framework import viewsets
from .models import Transaction
from .serializers import TransactionSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().order_by('-date')
    serializer_class = TransactionSerializer
```

```python
# urls.py (de la app)
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
urlpatterns = router.urls
```

* **urls.py principal**:

```python
from django.urls import path, include
urlpatterns = [
    path('health/', health_view),
    path('api/', include('wallet.urls')),
]
```

* **CORS (dev)** en `settings.py`:

```python
INSTALLED_APPS += ['corsheaders', 'rest_framework']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', *MIDDLEWARE]
CORS_ALLOW_ALL_ORIGINS = True  # solo desarrollo
```

> Si no existe la app `wallet`, crearla con `python manage.py startapp wallet` y añadir archivos previos.

### 6) Configuración de Expo y variables de entorno

#### 6.1) `app.config.ts`

```ts
import 'dotenv/config';
import type { ExpoConfig } from 'expo/config';

const config: ExpoConfig = {
  name: 'Billetera',
  slug: 'billetera-mobile',
  scheme: 'billetera',
  extra: {
    BACKEND_URL: process.env.EXPO_PUBLIC_BACKEND_URL,
  },
};
export default config;
```

#### 6.2) `.env.example`

```
# Cambiar por la IP local de la máquina donde corre Django
EXPO_PUBLIC_BACKEND_URL=http://192.168.0.10:8000
```

### 7) `.gitignore` en `/mobile`

```
.expo
.expo-shared
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
.env*
```

### 8) Scripts de ejecución

`/mobile/package.json`:

```json
{
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web"
  }
}
```

Opcional en el **root** del repo:

```json
{
  "scripts": {
    "backend": "cd backend && python manage.py runserver 0.0.0.0:8000",
    "mobile": "cd mobile && npm run start"
  }
}
```

---

## Prueba local (paso a paso)

1. **Backend Django**:

   ```bash
   python manage.py makemigrations && python manage.py migrate
   python manage.py runserver 0.0.0.0:8000
   ```
2. **Config móvil**: copiar `/mobile/.env.example` a `/mobile/.env` y ajustar `EXPO_PUBLIC_BACKEND_URL` con la IP LAN de la PC.
3. **App móvil**:

   ```bash
   cd mobile
   npm install
   npm run start
   ```
4. **iPhone**: instalar **Expo Go**, escanear QR, abrir app.
5. **Flujo:**

   * Home muestra **Resumen** con totales desde storage local.
   * Agregar un movimiento (ingreso o egreso) → ver en **Movimientos**.
   * Editar / eliminar desde **Movimientos**.
   * (Opcional) Integrar llamadas a `/api/transactions/` y sincronizar.

---

## Consideraciones de red (Windows)

* iPhone no accede a `localhost` de la PC. Usar **IP LAN** (ej: `http://192.168.1.23:8000`).
* Android Emulator puede usar `http://10.0.2.2:8000`.
* En Expo, presionar `s` para **tunnel** si hay bloqueos de red.

---

## Checklist de aceptación (DoD)

*

---

## Próximos pasos

* Sincronización con backend (pull/push, manejo de conflictos).
* Filtros por fecha/categorías y exportación CSV.
* Estado global (Zustand) + validaciones.
* Auth JWT (DRF SimpleJWT) y secure storage.
* Notificaciones locales (recordatorios de registrar movimientos).
* CI/CD con EAS Build/Update.

---

## Mensaje de commit sugerido

```
feat(mobile): Expo RN+TS (sin grupos/pagos) con CRUD de ingresos/egresos y storage local; endpoints mínimos creados
```
