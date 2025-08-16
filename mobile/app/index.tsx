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
