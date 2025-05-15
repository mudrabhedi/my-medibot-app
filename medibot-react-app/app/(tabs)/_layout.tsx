import { Stack } from 'expo-router';
import React from 'react';

export default function Layout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false, // 👈 Hides the top "index" title bar
      }}
    />
  );
}
