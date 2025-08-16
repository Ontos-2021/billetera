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
