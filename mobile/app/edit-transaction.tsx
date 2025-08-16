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
