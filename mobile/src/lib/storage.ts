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
