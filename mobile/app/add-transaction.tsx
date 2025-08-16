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
