import React, { useState } from 'react';
import { Button, ScrollView, Text, TextInput, View } from 'react-native';

export default function App() {
  const [input, setInput] = useState('');
  const [chat, setChat] = useState([]);

  const sendMessage = async () => {
    const res = await fetch('https://medibot-backend-ylqu.onrender.com/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: input }),
    });

    const data = await res.json();
    setChat(prev => [...prev, { role: 'user', content: input }, { role: 'bot', content: data.answer }]);
    setInput('');
  };

  return (
    <View style={{ padding: 20 }}>
      <ScrollView style={{ height: '80%' }}>
        {chat.map((msg, i) => (
          <Text key={i} style={{ marginVertical: 4 }}>
            <Text style={{ fontWeight: 'bold' }}>{msg.role === 'user' ? 'You' : 'Bot'}: </Text>
            {msg.content}
          </Text>
        ))}
      </ScrollView>
      <TextInput
        style={{ borderWidth: 1, padding: 8, marginBottom: 10 }}
        value={input}
        onChangeText={setInput}
        placeholder="Ask something..."
      />
      <Button title="Send" onPress={sendMessage} />
    </View>
  );
}
