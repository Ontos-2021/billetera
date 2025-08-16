export type TransactionType = 'income' | 'expense';
export type Transaction = {
  id: string;
  concepto: string;
  monto: number;
  type: TransactionType;
  date?: string; // ISO opcional
};
