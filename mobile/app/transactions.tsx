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
